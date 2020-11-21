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

import paho.mqtt.client as mqtt
import gw2mqtt.goodwe_inverter as inverter

from datetime import datetime
from configparser import ConfigParser
from gw2mqtt import mqtt
from gw2mqtt import __version__

# Telegram
def telegram_notify(telegram_token, telegram_chatid, message):
    token = telegram_token
    chat_id = telegram_chatid
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=message)

# Goodwe inverter
def goodwe_inverter_connection(gw_inverter_ip, gw_inverter_port, telegram_token, telegram_chatid):
    currentTime = datetime.now()
    connection_retries = 1
    for i in range(connection_retries):
        try:
            inverter_connection = asyncio.run(inverter.discover(gw_inverter_ip, gw_inverter_port))
            inv_con_state = "connected"
            logging.info("Connected to inverter")
            return inverter_connection, inv_con_state
            i = 0
        except Exception as exp:
            errorMsg = ("Retrying connection to inverter - " + str(gw_inverter_ip) + " - Result: " + str(exp))
            logging.error(str(currentTime) + " - " + str(errorMsg))
            telegram_notify(telegram_token, telegram_chatid, errorMsg)
            if i < connection_retries - 1:
                continue
            else:
                break

def run_once(settings):
    try:
        mqtt_broker = mqtt.MQTT(settings.telegram_token, settings.telegram_chatid, settings.mqtt_host, settings.mqtt_port, settings.mqtt_user, settings.mqtt_password, settings.mqtt_topic)
        mqtt_broker.mqtt_server_connection(settings.mqtt_host, settings.mqtt_port, settings.mqtt_user, settings.mqtt_password, settings.mqtt_topic)
        inverter = goodwe_inverter_connection(settings.gw_inverter_ip, settings.gw_inverter_port, settings.telegram_token, settings.telegram_chatid)
        return mqtt_broker, inverter[0], inverter[1]
    except Exception as exp:
        currentTime = datetime.now()   
        errorMsg = (str(currentTime) + " - Unable to connect to inverter - " + str(settings.gw_inverter_ip))
        logging.error(str(currentTime) + " - " + str(errorMsg))
        telegram_notify(settings.telegram_token, settings.telegram_chatid, "FATAL: "  +str(errorMsg))
        sys.exit(1)

def run():
    startTime = datetime.now()
    
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
    parser.add_argument("--telegram-token", help="Telegram bot token", metavar='TELEGRAM_TOKEN')
    parser.add_argument("--telegram-chatid", help="Telegram chat id", metavar='TELEGRAM_CHATID')
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

    # Inverter connection
    clients = run_once(args)
    mqtt_client = clients[0]
    try:
        inverter = clients[1]
        inv_con_state = clients[2]
    except Exception as exp:
        currentTime = datetime.now()
        errorMsg = ("Unable to connect to inverter - " + str(settings.gw_inverter_ip) + " - Result: " + str(exp))
        logging.error(str(currentTime) + " - " + str(errorMsg))
        telegram_notify(telegram_token, telegram_chatid, errorMsg)

    sleep_counter = 1 
   
    while True:
        try:
            currentTime = datetime.now()
            response = asyncio.run(inverter.read_runtime_data())
            chk_connection = mqtt_client.mqtt_get_socket()
            if chk_connection is not None:
                for key, value in response.items():
                    topic = (str(settings.mqtt_topic) + "/" + str(key))
                    mqtt_client.mqtt_publish_data(mqtt_client, topic, value)
                logging.info(str(currentTime) + " - Published inverter data to mqtt broker")
            else:
                errorMsg = ("Publishing inverter data to " + str(settings.mqtt_topic) + " on " + str(settings.mqtt_host) + " failed")
                logging.error(str(currentTime) + " - " + str(errorMsg))
                telegram_notify(settings.telegram_token, settings.telegram_chatid, errorMsg)
                time.sleep(30)

        except KeyboardInterrupt:
            mqtt_client.mqtt_disconnect()
            sys.exit(1)

        if settings.gw_interval is None:
            break

        interval = settings.gw_interval
        time.sleep(interval - (datetime.now() - startTime).seconds % interval)

if __name__ == "__main__":
    run()
