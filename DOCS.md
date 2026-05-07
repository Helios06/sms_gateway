# SMS Gateway App 

This App (formerly known as ADD-ON) provides à SMS Gateway in order for automations and scripts to be able to send and receive SMS using a GSM USB dongle modem.

It is intentionally a lightweight version in order to run on the same computer as HA (PI4 for exemple).

It handles all GSM7 characters (extended characters not handled)

    @£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ
     !\"#¤%&'()*+,-./0123456789:;<=>?
    ¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§
    ¿abcdefghijklmnopqrstuvwxyzäöñüà


### Home Assistant requirements

On your Home Assistant you must have configured 2 needed Apps (formerly known as ADD-ONS)
- **MQTT** (Mosquito broker)
  - message broker that implements the MQTT protocol. 
  - Mosquitto is lightweight and is suitable for use on all devices from low power single board computers.
  - See [MQTT Mosquitto Broker GitHub](https://github.com/home-assistant/addons/tree/master/mosquitto)
- **Samba Share**
  - This App allows you to enable file sharing across different operating systems over a network. 
  - It lets you access your config files with Windows and macOS devices.
  - See [Samba Share GitHub](https://github.com/home-assistant/addons/tree/master/samba)

### Where to find help

 - [SMS Gateway (this App) GitHub](https://github.com/Helios06/sms_gateway)
 - [Apps Development for HA](https://developers.home-assistant.io/docs/apps)
 - [MQTT Mosquitto Broker GitHub](https://github.com/home-assistant/addons/tree/master/mosquitto)
 - [Samba Share GitHub](https://github.com/home-assistant/addons/tree/master/samba)
 - [HA Community](https://community.home-assistant.io)

### Installation

- copy this App (SMS Gateway) on your local Apps repository using Samba Share
- install/update and configure this APP (SMS Gateway) on Home Assistant: Settings -> Apps -> Install Apps

### Integration with MQTT Message Broker (Mosquito) 

Communication/integration is done using 2 MQTT topics. 
- one for HA scripts to send SMS 
  - topic name proposed is `send_sms`(but configurable)
- one to handle SMS reception and passing them back to HA
  - topic name proposed is `sms_received` (but configurable)

### USB GSM dongle requirements

Your GSM modem must handle the following AT commands/responses

    ATZ = "ATZ"                               # reset modem
    ATE0 = "ATE0"                             # set echo off
    ATE1 = "ATE1"                             # set echo on
    ATCLIP = "AT+CLIP?"                       # get calling line identification presentation
    ATCMEE = "AT+CMEE=1"                      # set extended error
    #ATCPIN = "AT+CPIN=\"0000\""              # set pin code
    #ATCLCK0 = "AT+CLCK=\"SC\",0,\"0000\""    # disable code pin check, pin=0000
    #ATCLCK1 = "AT+CLCK=\"SC\",1,\"0000\""    # enable code pin check, pin=0000
    ATCSCS = "AT+CSCS=\"GSM\""                # force GSM mode for SMS
    ATCMGF = "AT+CMGF=1"                      # enable sms in text mode
    ATCSDH = "AT+CSDH=1"                      # enable more fields in sms read
    ATCMGS = "AT+CMGS="                       # send message with prompt
    ATCMGD = "AT+CMGD="                       # delete messages: =0,4 -> 4 means ignore the value 0 of index and delete all SMS messages from the message storage area
    ATCMGL = "AT+CMGL="                       # list all messages
    ATCMGR = "AT+CMGR="                       # read message by index in storage
    ATCMGW = "AT+CMGW="                       # write
    ATCMSS = "AT+CMSS="                       # send message by index in storage
    ATCPMS = "AT+CPMS=\"ME\",\"ME\",\"ME\""   # storage is Mobile
    ATCSQ = "AT+CSQ"                          # signal strength
    ATCREG = "AT+CREG?"                       # registered on network ?
    ATCNMI = "AT+CNMI=2,1,0,0,0"              # when sms arrives CMTI send to pc
  
### This App Configuration example

    GSM_Mode: modem
    GSM_Device: /dev/serial/by-id/usb-HUAWEI_HUAWEI_Mobile-if00-port0
    GSM_PIN: 0000
    GSM_AUTH: +336XXXXXXXX,+336YYYYYYYY
    MQTT_Host: core-mosquitto
    MQTT_Port: 1883
    MQTT_User: mqtt
    MQTT_Password: mqtt
    MQTT_Receive: sms_received
    MQTT_Send: send_sms
    ADDON_Logging: INFO

- GSM_Mode : 
  - 'modem' (do not change that)
- GSM_Device: 
    - /dev/ttyUSBx
    - /dev/ttyACMx
    - /dev/serial/by-id/...... (this one is preferable) 
      - You may find the correct value for this by going to Settings
        HA -> System -> Hardware and then look for USB details and choose a by-id one
        it is recommended to use a "by-id" path to the device if one exists, as it is not subject to change if other devices are added to the system.
- GSM_PIN: 
  - Pin code of the Sim
- GSM_AUTH: 
  - Comma separated list of authorized mobile numbers to receive SMS from. Other will be rejected.
- MQTT_Receive: 
  - Topic on which add-on will publish received SMS
- MQTT_Send: 
  - Topic on which HA will publish SMS to be sent by the add-on
- ADDON_Logging: 
  - use python logging levels 
    - DEBUG, INFO, WARNING, ERROR, CRITICAL

### Home Assistant Sending SMS, automation example

```yaml
alias: test_send_sms
description: ""
mode: single
triggers: []
conditions: []
actions:
  - data:
      mobile: 06XXXXXXXX
      txt: "@£$¥èéùìòÇ"
    enabled: true
    action: script.script_send_sms
  - data:
      mobile: 06XXXXXXXX
      txt: Øø
    enabled: false
    action: script.script_send_sms
  - data:
      mobile: 06XXXXXXXX
      txt: ÅåΔ_ΦΓΛΩΠΨΣΘ
    enabled: false
    action: script.script_send_sms
  - data:
      mobile: 06XXXXXXXX
      txt: ÆæßÉ
    enabled: false
    action: script.script_send_sms
  - data:
      mobile: 06XXXXXXXX
      txt: " !#¤%&'()*+,-./0123456789:;<=>?"
    enabled: false
    action: script.script_send_sms
  - data:
      mobile: 06XXXXXXXX
      txt: ¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§
    enabled: false
    action: script.script_send_sms
  - data:
      mobile: 06XXXXXXXX
      txt: ¿abcdefghijklmnopqrstuvwxyzäöñüà
    enabled: false
    action: script.script_send_sms
  - data:
      mobile: 06XXXXXXXX
      txt: ¿abcdefghijklmnopqrstuvwxyzäöñüà
    enabled: false
    action: script.script_send_sms
  - data:
      mobile: 06XXXXXXXX
      txt: \"Hello\" de Léonard
    enabled: false
    action: script.script_send_sms
```

### Home Assistant Sending SMS, script example

```yaml
alias: script-send-sms
sequence:
  - data:
      qos: 0
      retain: false
      topic: send_sms
      payload: "{\"to\": \"{{mobile}}\", \"txt\": \"{{txt}}\"}"
    action: mqtt.publish
mode: single
```

### Home Assistant Receiving SMS, automation example

```yaml
alias: automation-sms-received
description: "SMS received is JSON -> {\"from\": new_sms['Number'], \"txt\": new_sms['Msg']}"
triggers:
  - topic: sms_received
    trigger: mqtt
conditions: []
actions:
  - alias: Check for "patio on"
    if:
      - condition: template
        value_template: "{{trigger.payload_json.txt|lower == 'patio on'}}"
    then:
      - data: {}
        action: script.script_patio_on
      - data:
          qos: 0
          retain: false
          topic: send_sms
          payload: "{\"to\": \"{{trigger.payload_json.from}}\", \"txt\": \"Patio allumé\"}"
        action: mqtt.publish
  - alias: Check for "patio off"
    if:
      - condition: template
        value_template: "{{trigger.payload_json.txt|lower == 'patio off'}}"
    then:
      - data: {}
        action: script.script_patio_off
      - data:
          qos: 0
          retain: false
          topic: send_sms
          payload: "{\"to\": \"{{trigger.payload_json.from}}\", \"txt\": \"Patio éteint\"}"
        action: mqtt.publish
  - metadata: {}
    data:
      my_message: "{{trigger.payload_json.txt}}"
    enabled: true
    action: script.script_notify_ha
mode: single

```
   
### Dev/Tests environment where the add-on is actually developed

- Raspberry PI4B using
  - GSM modem Huawei E3131
  - Core 2026.5.0
  - Supervisor 2026.04.2
  - Operating System 17.3
  - Frontend 20260429.3

### Contributors

- see https://github.com/Helios06/sms_gateway for last release
- See [contributors page](https://github.com/Helios06/sms_gateway) for a list of contributors.

### MIT License

Copyright (c) 2023-2026  Helios  philippemario.romano@hotmail.fr

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
