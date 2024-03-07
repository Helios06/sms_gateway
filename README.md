# sms_gateway

This add-on provides à SMS gateway to send and receive SMS
using a USB Dongle Modem.

![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield] ![Supports armhf Architecture][armhf-shield] ![Supports armv7 Architecture][armv7-shield] ![Supports i386 Architecture][i386-shield]

### Integration with Home Assistant 

Communication/integration with Home Assistant is realized 
using 2 MQTT topics. 
- one for HA scripts to send SMS 
  - topic name proposed is `send_sms` but is configurable
- another one to handle SMS reception and passing them back to 
Home Assistant
  - topic name proposed is `sms_received` but is configurable

### Repository and Contributors
- see https://github.com/Helios06/sms_gateway for last release
- See [contributors page](https://github.com/Helios06/sms_gateway) for a list of contributors.


[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg