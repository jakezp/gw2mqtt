
# gw2mqtt

gw2mqtt is a command line tool to get data from Goodwe inverter directly (UDP) and publish data to mqtt.

## Installation

This is stll very broken as I am mainly working on getting this working at home, and it's not really meant for distribution. But if you really want to try it, you need to have Python 3 and pip installed. Then:

```shell
sudo pip3 install https://github.com/jakezp/gw2mqtt/raw/main/dist/gw2mqtt-0.0.9.tar.gz
```

```shell
usage: gw2mqtt [-h] [--gw-inverter-ip GW_IP] 
		    [--gw-inverter-port PORT] [--gw-interval {10,20,30}] 
		    [--mqtt-host MQTT_IP] [--mqtt-port MQTT_PORT]
               	    [--mqtt-subscription-topic MQTT_TOPIC]
		    [--log {debug,info,warning,critical}] [--version]

Data will be published to "emoncms/goodwe".
```

### Examples

```shell
gw2mqtt --mqtt-host 192.168.1.x --mqtt-port 1883 --gw-inverter-ip 192.168.1.x --gw-inverter-port 8899 --mqtt-subscription-topic goodwe/command --gw-interval 10 --log info
```

*Please note: the subscription topic does not do anything yet. It's meant to listen for commands: normal, backup or off-grid, to set the inverter mode to either of these modes. Subscription is working and will pront the results, but not currently sending the commands to the inverter.*
]

### Config file

Config file is not currently working either...

```ini
[Defaults]
mqtt-host = ...
mqtt-port = ...
mqtt-subscription-topic = ...
gw-inverter-ip = ...
gw-inverter-port - ...
```

## Docker

You can use the [Dockerfile](https://raw.githubusercontent.com/jakezp/gw2mqtt/main/Dockerfile) to run a Docker container as follows:

Update the values in the Dockerfile to match your environment, then:

```shell
docker build --tag gw2mqtt .
```

```shell
docker run --rm gw2mqtt
```

## Disclaimer

None of this is official software, nor is any of this original software or ideas. Everytihng here has been mashed together from different sources (listed below) and there is no guarantee / waranty / promise that this will work, nor do I make any claims that your equipment may not be damaged. DO NOT USE THIS.

This is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the software.

## Sources & inspiration

As mentioned above, none of the work contained here can be considered original. It's a nasty mash together, with very limited knowledge (and horrible use) Python, of the awesome work done by others. Based on the following:<br/>
[gw2pvo](https://github.com/markruys/gw2pvo) - gw2pvo is a command line tool to upload solar data from a GoodWe power inverter to the PVOutput.org website<br/>
[GoodWe solar inverter sensors for Home Assistant](https://github.com/mletenay/home-assistant-goodwe-inverter) - The GoodWe Inverter Solar Sensor component will retrieve data from a GoodWe inverter connected to local network

