#
#   sms_manager
#   Copyright (c) Philippe Romano, 2021-2024
#
#   Home Assistant addon with slug: sms_gateway
#   Handles MQTT broker messages to send sms or for received sms
#
#   Log is generated  under HomeAssistant
#   To display the log
#       go to "add-ons" then "log"
#

import paho.mqtt.client as mqtt
import sys
import signal
import argparse
import json
import logging

from gsm import gsm


global  sms_gateway, mqtt_client

def signal_handler(sig, frame):
    global  sms_gateway, mqtt_client

    logging.info('Closing sms gateway under signal handler')
    sms_gateway.stop()
    logging.info('... Sms gateway stopped and closed under signal handler')
    sys.exit(0)

def print_response(data):
    for key, value in data["response"].items():
        logging.info(f"   {key}:  {value}")

def on_message(client, userdata, msg):
    global sms_gateway, mqtt_client

    logging.info("")
    logging.info(f"Received SMS Message to send")
    logging.info(f"... JSON UTF-8 Message")
    logging.info(msg.payload)
    message = json.loads(msg.payload)
    sms_gateway.sendSmsToNumber(message["to"], message["txt"])


def main_modem(options):
    global sms_gateway, mqtt_client

    # Start gateway
    logging.info('Starting SMS gateway')
    sms_gateway = gsm("Huawei", options.mode, options.device, options.pin, mqtt_client)
    sms_gateway.start()
    while not sms_gateway.Ready:
        pass

    logging.info('Subscribing on topic: send_sms')
    mqtt_client.subscribe("send_sms")
    logging.info('... Subscribing done')

    logging.info('Entering MQTT endless loop')
    mqtt_client.loop_forever()
    logging.info('... Leaving MQTT endless loop')


def main(args=None):
    global mqtt_client

    # set logger
    #logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)

    # Handle Interrupt and termination signals
    logging.info("")
    logging.info('Preparing signal handling for termination')
    signal.signal(signal.SIGINT, signal_handler)  # Handle CTRL-C signal
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    logging.info('.... signal handling for termination done')

    logging.info('Parsing arguments')
    try:
        parser = argparse.ArgumentParser(description="Name Server command line launcher")
        parser.add_argument("--mode", dest="mode", help="modem or api", default="modem")
        parser.add_argument("-d", "--device", dest="device", help="USB device name", default="/dev/USB0")
        parser.add_argument("--pin", dest="pin", help="code pin", default="0000")
        parser.add_argument("-u", "--user", dest="user", help="mqtt user", default="xxxx")
        parser.add_argument("-s", "--secret", dest="secret", help="mqtt user password", default="xxxx")
        parser.add_argument("-r", "--host", dest="host", help="mqtt host", default="")
        parser.add_argument("-p", "--port", dest="port", help="mqtt port", default=0)
        options = parser.parse_args(args)
        logging.info('... Arguments parsed:')
        logging.info('...... mode is: '+options.mode)
        logging.info('...... device is: '+options.device)
        logging.info('...... pin is: '+options.pin)
        logging.info('...... mqtt user is: '+options.user)
        logging.info('...... mqtt user secret is: '+options.secret)
        logging.info('...... mqtt host is: '+options.host)
        logging.info('...... mqtt port is: '+options.port)
    except (Exception,) as e:
        return None

    # Handle MQTT
    logging.info('Connecting to MQTT broker')
    broker = options.host
    port = int(options.port)
    user = options.user
    password = options.secret
    topic = "send_sms"

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_message = on_message
    mqtt_client.username_pw_set(user, password)  # see Mosquitto broker config
    # mqtt_client.tls_set()
    mqtt_client.connect(broker)
    logging.info('... Connected to MQTT broker: '+broker+':'+str(port)+' on topic: '+topic)

    if options.mode == 'modem':
        main_modem(options)
    else:
        logging.info('Error ! specify options "mode"')
        pass


if __name__ == '__main__':
    main()
