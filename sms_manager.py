"""
MIT License

Copyright (c) 2023-2024  Helios  helios14_75@hotmail.fr

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

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
    logging.info(f"MQTT send message received")
    logging.debug(f"... JSON UTF-8 Message")
    logging.debug(msg.payload)
    message = json.loads(msg.payload)
    logging.info(f"... %s", message["txt"])
    sms_gateway.sendSmsToNumber(message["to"], message["txt"])


def main_modem(loglevel, options):
    global sms_gateway, mqtt_client

    # Start gateway
    logging.info('Starting SMS gateway')
    sms_gateway = gsm(loglevel, "Huawei", options.mode, options.device, options.pin, options.auth, options.recv, mqtt_client)
    sms_gateway.start()
    while not sms_gateway.Ready:
        pass

    logging.info('Subscribing on topic: '+options.send)
    mqtt_client.subscribe(options.send)
    logging.info('... Subscribing done')

    logging.info('')
    logging.info('Entering MQTT endless loop')
    mqtt_client.loop_forever()
    logging.info('... Leaving MQTT endless loop')


def main(args=None):
    global mqtt_client

    try:
        parser = argparse.ArgumentParser(description="Name Server command line launcher")
        parser.add_argument("--mode", dest="mode", help="modem or api", default="modem")
        parser.add_argument("-d", "--device", dest="device", help="USB device name", default="/dev/USB0")
        parser.add_argument("--pin", dest="pin", help="code pin", default="-")
        parser.add_argument("--auth", dest="auth", help="authorized numbers", default="")
        parser.add_argument("-u", "--user", dest="user", help="mqtt user", default="mqtt")
        parser.add_argument("-s", "--secret", dest="secret", help="mqtt user password", default="mqtt")
        parser.add_argument("-r", "--host", dest="host", help="mqtt host", default="homeassistant.local")
        parser.add_argument("-p", "--port", dest="port", help="mqtt port", default="1883")
        parser.add_argument("--send", dest="send", help="mqtt send", default="send_sms")
        parser.add_argument("--recv", dest="recv", help="mqtt receive", default="sms_received")
        parser.add_argument("--log", dest="logging", help="addon logging level", default="INFO")
        options = parser.parse_args(args)
    except (Exception,):
        return None

    # DEBUG INFO WARNING ERROR CRITICAL
    log_level = logging.DEBUG
    if options.logging == "DEBUG":
        log_level = logging.DEBUG
    if options.logging == "INFO":
        log_level = logging.INFO
    if options.logging == "WARNING":
        log_level = logging.WARNING
    if options.logging == "ERROR":
        log_level = logging.ERROR
    if options.logging == "CRITICAL":
        log_level = logging.CRITICAL

    # set logger
    #logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
    logging.basicConfig(level=log_level)

    logging.info('')
    logging.info('Arguments parsed:')
    logging.info('... mode is: '+options.mode)
    logging.info('... device is: '+options.device)
    logging.info('... pin is: '+options.pin)
    logging.info('... auth is: '+options.auth)
    logging.info('... mqtt user is: '+options.user)
    logging.info('... mqtt user secret is: '+options.secret)
    logging.info('... mqtt host is: '+options.host)
    logging.info('... mqtt port is: '+options.port)
    logging.info('... mqtt send is: '+options.send)
    logging.info('... mqtt recv is: '+options.recv)
    logging.info('... addon logging is: '+options.logging)

    # Handle Interrupt and termination signals
    logging.info("")
    logging.info('Preparing signal handling for termination')
    signal.signal(signal.SIGINT, signal_handler)  # Handle CTRL-C signal
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    logging.info('.... signal handling for termination done')

    # Handle MQTT
    logging.info('Connecting to MQTT broker')
    broker = options.host
    port = int(options.port)
    user = options.user
    password = options.secret
    topic = options.send        # "send_sms"

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_message = on_message
    mqtt_client.username_pw_set(user, password)  # see Mosquitto broker config
    # mqtt_client.tls_set()
    mqtt_client.connect(broker)
    logging.info('... Listening to MQTT broker: '+broker+':'+str(port)+' on topic: '+topic)

    if options.mode == 'modem':
        main_modem(log_level, options)
    else:
        logging.info('Error ! specify options "mode"')
    pass


if __name__ == '__main__':
    main()
