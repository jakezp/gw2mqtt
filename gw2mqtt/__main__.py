#!/usr/bin/env python3

import sys, os
if sys.version_info < (3,8):
    sys.exit('Sorry, you need at least Python 3.8')

import time
import logging
import asyncio
import argparse
import locale
import json
import telegram

from datetime import datetime
from configparser import ConfigParser

import paho.mqtt.client as mqtt
import gw2mqtt.goodwe_inverter as inverter

from gw2mqtt import __version__

# Telegram
def telegram_notify(telegram_token, telegram_chatid, message):
    token = telegram_token
    chat_id = telegram_chatid
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=message)

# MQTT broker
def mqtt_server_connection(mqtt_host, mqtt_port, mqtt_user, mqtt_password, mqtt_topic):
    client = mqtt.Client()
    client.on_connect = mqtt_on_connect
    #client.on_message = mqtt_on_message
    client.username_pw_set(mqtt_user, password=mqtt_password)
    client.connect(mqtt_host, port=int(mqtt_port), keepalive=30)
    client.loop_start()
    #mqtt_subscribe(client, mqtt_subscription_topic)
    
    return client
def mqtt_server_disconnect():
    client = mqtt.Client()
    client.loop_stop()

def mqtt_on_connect(client, userdata, flags, rc):
    global mqtt_connected
    mqtt_connected = rc
    if rc == 0:
        logging.debug("Connected to broker")

#def mqtt_on_message(client, userdata, message):
#    global mode

#def mqtt_subscribe(client, mqtt_subscription_topic):
#    client.subscribe(mqtt_subscription_topic)
#    logging.info("Subscribed to command topic")

def mqtt_publish_data(client, mqtt_publish_topic, payload):
    client.publish(mqtt_publish_topic, payload)

# Goodwe inverter
def goodwe_inverter_connection(gw_inverter_ip, gw_inverter_port, telegram_token, telegram_chatid):
    connection_retries = 5
    for i in range(connection_retries):
        try:
            inverter_connection = asyncio.run(inverter.discover(gw_inverter_ip, gw_inverter_port))
            inv_con_state = "connected"
            logging.info("Connected to inverter")
            return inverter_connection, inv_con_state
            i = 0
        except:
            logging.error("Connecting to inverter failed")
            telegram_notify(telegram_token, telegram_chatid, "WARNING: gw2mqtt - connecting to inverter failed")
            if i < connection_retries - 1:
                continue
            else:
                break

def connect_inverter(settings):
    try:
        inverter = goodwe_inverter_connection(settings.gw_inverter_ip, settings.gw_inverter_port, settings.telegram_token, settings.telegram_chatid)
        return inverter[0], inverter[1]
    except:
        telegram_notify(settings.telegram_token, settings.telegram_chatid, "FATAL: gw2mqtt failed to connect to the inverter.")

def run():
    defaults = {
        'log': "info"
    }

    # Parse any config file specification. We make this parser with add_help=False so
    # that it doesn't parse -h and print help.
    conf_parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )
    conf_parser.add_argument("--config", help="Specify config file", metavar='FILE')
    args, remaining_argv = conf_parser.parse_known_args()

    # Read configuration file and add it to the defaults hash.
    if args.config:
        config = ConfigParser()
        config.read(args.config)
        if "Defaults" in config:
            defaults.update(dict(config.items("Defaults")))
        else:
            sys.exit("Bad config file, missing Defaults section")

    # Parse rest of arguments
    parser = argparse.ArgumentParser(
        description=__doc__,
        parents=[conf_parser],
    )
    parser.set_defaults(**defaults)
    parser.add_argument("--gw-inverter-ip", help="GoodWe Inverter IP address", metavar='GW_IP')
    parser.add_argument("--gw-inverter-port", help="GoodWe Inverter port (default: 8899)", metavar='PORT')
    parser.add_argument("--gw-interval", help="Interval to collect data from inverter", type=int, choices=[10, 20, 30, 300])
    parser.add_argument("--mqtt-host", help="MQTT hostname or IP address", metavar='MQTT_IP')
    parser.add_argument("--mqtt-port", help="MQTT port (1883 or 8883 for TLS)", metavar='MQTT_PORT')
    parser.add_argument("--mqtt-user", help="MQTT username", metavar='MQTT_USER')
    parser.add_argument("--mqtt-password", help="MQTT password", metavar='MQTT_PASS')
    parser.add_argument("--mqtt-topic", help="MQTT subscribtion topic to listen to commands", metavar='MQTT_TOPIC')
    parser.add_argument("--pvo-api-key", help="PVOutput API key", metavar='KEY')
    parser.add_argument("--pvo-interval", help="PVOutput interval in minutes", type=int, choices=[5, 10, 15])
    parser.add_argument("--telegram-token", help="Telegram bot token", metavar='TELEGRAM_TOKEN')
    parser.add_argument("--telegram-chatid", help="Telegram chat id", metavar='TELEGRAM_CHATID')
    parser.add_argument("--telegram_token", help="Telegram bot token")
    parser.add_argument("--log", help="Set log level (default info)", choices=['debug', 'info', 'warning', 'critical'])
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    args = parser.parse_args()
    settings = args 
    
    # Configure the logging
    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(format='%(levelname)-8s %(message)s', level=numeric_level)

    logging.debug("gw2mqtt version " + __version__)
    
    if settings.gw_inverter_ip is None or settings.mqtt_host is None:
        sys.exit("Missing --gw-inverter-ip or --mqtt-host")

    startTime = datetime.now()
    
    # Inverter connection
    inverter_clients = connect_inverter(args)
    inverter = inverter_clients[0]
    inv_con_state = inverter_clients[1]
    
    sleep_counter = 1 
    
    while True:
        try:
            currentTime = datetime.now()
            response = asyncio.run(inverter.read_runtime_data())
            mqtt_client = mqtt_server_connection(settings.mqtt_host, settings.mqtt_port, settings.mqtt_user, settings.mqtt_password, settings.mqtt_topic)
            for i in range(sleep_counter):
                if sleep_counter == 1:
                    time.sleep(5)
            sleep_counter = 0
            if mqtt_connected == 0:
                for key, value in response.items():
                    topic = ("emoncms/goodwe/" + str(key))
                    mqtt_publish_data(mqtt_client, topic, value)
            logging.info(str(currentTime) + " - Publishing data to mqtt broker")
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as exp:
            logging.error(str(currentTime) + " - Publishing mqtt failed - " + str(exp))
            publishError = ("Failed to publish to mqtt broker - " + str(exp))
            telegram_notify(settings.telegram_token, settings.telegram_chatid, publishError)
            sleep_counter +=1
            if sleep_counter > 1:
                time.sleep(240)

        if settings.gw_interval is None:
            break

        interval = settings.gw_interval
        time.sleep(interval - (datetime.now() - startTime).seconds % interval)

if __name__ == "__main__":
    run()
