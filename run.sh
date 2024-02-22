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

echo "run.sh: launching sms_manager.py"
python3 /sms_manager.py --mode $mode -d $device --pin $pin --host $host --port $port -u $user -s $password --auth $auth --send $send --recv $recv
