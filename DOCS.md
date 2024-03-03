sms_gateway
===========

## Version
**sms_gateway** v1.1.4

This project provides à SMS gateway to send and receive SMS
using a USB Dongle Modem.

You will be able to send all GSM7 characters (extended characters not handled)

    @£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ
     !\"#¤%&'()*+,-./0123456789:;<=>?
    ¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§
    ¿abcdefghijklmnopqrstuvwxyzäöñüà

Communication / integration with Home Assistant is realized 
using 2 MQTT topics. One for HA scripts to send SMS (`send_sms`) and another one to handle 
SMS reception and passing back SMS to Home Assistant (`sms_received`)

Your GSM modem must handle the following AT commands/responses

    ATZ = "ATZ"                   # reset modem
    ATE0 = "ATE0"                 # set echo off
    ATE1 = "ATE1"                 # set echo on
    ATCLIP = "AT+CLIP?"           # get calling line identification presentation
    ATCMEE = "AT+CMEE=1"          # set extended error
    #ATCPIN = "AT+CPIN=\"0000\""  # set pin code
    #ATCLCK0 = "AT+CLCK=\"SC\",0,\"0000\""  # disable code pin check, pin=0000
    #ATCLCK1 = "AT+CLCK=\"SC\",1,\"0000\""  # enable code pin check, pin=0000
    ATCSCS = "AT+CSCS=\"GSM\""    # force GSM mode for SMS
    ATCMGF = "AT+CMGF=1"          # enable sms in text mode
    ATCSDH = "AT+CSDH=1"          # enable more fields in sms read
    ATCMGS = "AT+CMGS="           # send message with prompt
    ATCMGD = "AT+CMGD="           # delete messages: =0,4 -> 4 means ignore the value 0 of index and delete all SMS messages from the message storage area
    ATCMGL = "AT+CMGL="           # list all messages
    ATCMGR = "AT+CMGR="           # read message by index in storage
    ATCMGW = "AT+CMGW="           # write
    ATCMSS = "AT+CMSS="           # send message by index in storage
    ATCPMS = "AT+CPMS=\"ME\",\"ME\",\"ME\""  # storage is Mobile
    ATCSQ = "AT+CSQ"              # signal strength
    ATCREG = "AT+CREG?"           # registered on network ?
    ATCNMI = "AT+CNMI=2,1,0,0,0"  # when sms arrives CMTI send to pc


This add-on is NOT READY yet for some modem from Huawei providing full 
network with Hilink. You will have to wait for a future release.

## Build

Use the provided _Dockerfile_ and _run.sh_ to build and run the image.

## Home Assistant requirements

On your Home Assistant you must have configured 2 needed add-ons
- **MQTT (used Mosquito broker in dev/test)**
  - define 2 topics to send and receive SMS (by default `send_sms` and `sms_received` are proposed)
- **Samba Share**
  - used to update add-on local directory on your Home Assistant installation.
  
## Add-on configuration

    GSM_Mode: modem
    GSM_Device: /dev/ttyUSB1
    GSM_PIN: 0000
    GSM_AUTH: +336XXXXXXXX,+336YYYYYYYY
    MQTT_Host: homeassistant.local
    MQTT_Port: 1883
    MQTT_User: mqtt
    MQTT_Password: mqtt
    MQTT_Receive: sms_received
    MQTT_Send: send_sms
    ADDON_Logging: INFO

GSM_Mode : 'modem' ('api' under construction)

GSM_Device: where your USB dongle device is configured

GSM_PIN: Pin code of the Sim

GSM_AUTH: Comma separated list of authorized mobile numbers to receive sms from. Other will be rejected by the add-on

MQTT_Receive: Topic on which add-on will publish received SMS

MQTT_Send: Topic on which HA will publish SMS to be sent by the add-on

ADDON_Logging: python logging levels (DEBUG INFO WARNING ERROR CRITICAL)

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

### Dev/Tests environment where the add-on is actually produced

Raspberry PI4B
- GSM modem Huawei E3131
- Core 2024.2.5
- Supervisor 2024.02.0 
- Operating System 12.0
- Frontend 20240207.1

### Contributors

- see https://github.com/Helios06/sms_gateway for last release
- See [contributors page](https://github.com/Helios06/sms_gateway) for a list of contributors.

