FROM alpine:3.12

RUN apk add --no-cache python3 libffi openssl tzdata bash gcc g++ python3-dev libffi-dev openssl-dev && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools wheel && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache && \
    pip3 install paho-mqtt python-telegram-bot && \
    pip3 install https://github.com/jakezp/gw2mqtt/raw/main/dist/gw2mqtt-0.3.1.tar.gz

ENTRYPOINT exec /usr/bin/gw2mqtt --config config/gw2mqtt.cfg
