sms_gateway
===========

This project provides à SMS gateway to send and receive SMS
using a USB Dongle Modem.

Communication / integration with Home Assistant is realized 
using 2 MQTT topics. One for HA scripts to send SMS (`send_sms`) and another one to handle 
SMS reception and passing back SMS to Home Assistant (`sms_received`)

### Home Assistant requirements

On your Home Assistant you must have configured 2 needed add-ons
- **MQTT (used Mosquito broker in dev/test)**
  - define 2 topics to send and receive SMS (by default `send_sms` and `sms_received` are proposed)
- **Samba Share**
  - used to update add-on local directory on your Home Assistant installation.

### Repository and Contributors
- see https://github.com/Helios06/sms_gateway for last release
- See [contributors page](https://github.com/Helios06/sms_gateway) for a list of contributors.

