#!/usr/bin/with-contenv bashio

mode=$(bashio::config 'GSM_Mode')
device=$(bashio::config 'GSM_Device')
pin=$(bashio::config 'GSM_PIN')
auth=$(bashio::config 'GSM_AUTH')

host=$(bashio::config 'MQTT_Host')
port=$(bashio::config 'MQTT_Port')
user=$(bashio::config 'MQTT_User')
password=$(bashio::config 'MQTT_Password')
send=$(bashio::config 'MQTT_Send')
recv=$(bashio::config 'MQTT_Receive')

logging=$(bashio::config 'ADDON_Logging')

echo "run.sh: launching sms_manager.py"
python3 /sms_manager.py --mode $mode \
  -d $device --pin $pin --auth $auth \
  --host $host --port $port -u $user -s $password --send $send --recv $recv \
  --log $logging
