FROM alpine:3.12

RUN apk add --no-cache python3 tzdata bash && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools wheel && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache && \
    pip install paho-mqtt
    pip install https://github.com/jakezp/gw2mqtt/raw/main/dist/gw2mqtt-0.0.9.tar.gz

ENTRYPOINT exec /usr/bin/gw2mqtt --mqtt-host MQTT_IP --mqtt-port MQTT_PORT  --gw-inverter-ip INVERTER_IP --gw-inverter-port INVERTER_PORT --mqtt-subscription-topic COMMAND_TOPIC --gw-interval 10 --log info 
