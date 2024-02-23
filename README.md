sms_gateway
===========

This project provides à SMS gateway to send and receive SMS
using a GSM USB dongle. 

So far works only in modem mode.

Communication / integration with Home Assistant is realized 
using 2 MQTT topics. One for HA scripts to send SMS (`send_sms`) and another one to handle 
SMS reception and passing back SMS to Home Assistant (`sms_received`)

See repo: https://github.com/Helios06/sms_gateway

## Version
**sms_gateway** v1.0.7

## Build

Use the provided _Dockerfile_ and _run.sh_ to build and run the image.

## Home Assistant requirements

On your Home Assistant you must have configured several add-ons
- **Mosquito broker (MQTT)**
  - define 2 topics to send and receive SMS (by default `send_sms` and `sms_received` are proposed)
- **Samba Share**
  - used to update add-on local directory on your Home Assistant installation.
  
## Add-on configuration

    GSM_Mode: "Choose here 'modem' or 'api'"
    GSM_Device: "/dev/ttyUSB1"
    GSM_PIN: "0000"
    GSM_AUTH: " +336XXXXXXXX"
    MQTT_Host: "homeassistant.local"
    MQTT_Port: 1883
    MQTT_User: "mqtt"
    MQTT_Password: "mqtt"
    MQTT_Receive: "sms_received"
    MQTT_Send: "send_sms"

GSM_Mode : 'modem' ('api' under construction)

GSM_Device: where your USB dongle device is configured

GSM_PIN: Pin code of the Sim

GSM_AUTH: Comma separated list of authorized mobile numbers to receive sms from. Other will be rejected by the add-on

MQTT_Receive: Topic on which add-on will publish received SMS

MQTT_Send: Topic on which HA will publish SMS to be sent by the add-on


### Sending SMS example
Automation and Script example

    alias: test_send_sms
    description: ""
    trigger: []
    condition: []
    action:
      - service: script.script_send_sms
        data:
          mobile: "06xxxxxxxx"
          txt: "@£$¥èéùìòÇ"
        enabled: true
        - service: script.script_send_sms
          data:
            mobile: "06xxxxxxxx"
            txt: \"Hello\" de Léonard
    mode: single
        
    alias: script-send-sms
    sequence:
      - service: mqtt.publish
        data:
          qos: 0
          retain: false
          topic: send_sms
          payload_template: "{\"to\": \"{{mobile}}\", \"txt\": \"{{txt}}\"}"
    mode: single

### Receiving SMS example
Automation and Script example

    alias: sms-received
    description: "SMS received is JSON -> {\"from\": new_sms['Number'], \"txt\": new_sms['Msg']}"
    trigger:
      - platform: mqtt
        topic: sms_received
    condition: []
    action:
        - alias: Check for "patio on"
          if:
            - condition: template
              value_template: "{{trigger.payload_json.txt|lower == 'patio on'}}"
          then:
            - service: script.script_patio_on
              data: {}
        - alias: Check for "patio off"
          if:
            - condition: template
              value_template: "{{trigger.payload_json.txt|lower == 'patio off'}}"
          then:
            - service: script.script_patio_off
              data: {}
        - service: mqtt.publish
          data:
            qos: 0
            retain: false
            topic: send_sms
            payload_template: >-
              {"to": "{{trigger.payload_json.from}}", "txt":
              "{{trigger.payload_json.txt}} ok"}
    mode: single


### Contributors

- See [contributors page](https://github.com/Helios06/sms_gateway) for a list of contributors.

