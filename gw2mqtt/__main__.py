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
def mqtt_server_connection(mqtt_host, mqtt_subscription_topic):
    client = mqtt.Client("gw2mqtt-client")
    client.on_connect = mqtt_on_connect
    #client.on_message = mqtt_on_message
    client.connect(mqtt_host)
    client.loop_start()
    #mqtt_subscribe(client, mqtt_subscription_topic)
    return client

def mqtt_on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to broker")
    else:
        logging.error("Failed to connect to MQTT broker")

#def mqtt_on_message(client, userdata, message):
#    global mode
#    if str(message.payload) == "b'normal'":
#        mode = "normal"
#        inverter_mode = 0
#        logging.info("Received 'normal' on command topic")
#        #goodwe_inverter_change_mode(inverter_mode)
#    elif str(message.payload) == "b'backup'":
#        mode = "backup"
#        inverter_mode = 2
#        logging.info("Received 'backup' on command topic")
#        #goodwe_inverter_change_mode(inverter_mode)
#    elif str(message.payload) == "b'off-grid'":
#        mode = "off-grid"
#        inverter_mode = 1
#        logging.info("Received 'off-grid' on command topic")
#        #goodwe_inverter_change_mode(inverter_mode)
#    else:
#        mode = "unknown"
#        logging.info("Received an unknown command on command topic")

#def mqtt_subscribe(client, mqtt_subscription_topic):
#    client.subscribe(mqtt_subscription_topic)
#    logging.info("Subscribed to command topic")

def mqtt_publish_data(client, mqtt_publish_topic, payload):
    client.publish(mqtt_publish_topic, payload)

# Goodwe inverter
#def inverter_change_mode(inverter_mode):
#    # Not working yet
#    mode_result = inverter.set_work_mode(int(inverter_mode))
#    logging.info (mode_result)
#    logging.info("Setting inverter mode to " + str(inverter_mode))

def goodwe_inverter_connection(gw_inverter_ip, gw_inverter_port, telegram_token, telegram_chatid):

    connection_retries = 1
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

def run_once(settings):
    try:
        mqtt_client = mqtt_server_connection(settings.mqtt_host, settings.mqtt_subscription_topic)
        inverter = goodwe_inverter_connection(settings.gw_inverter_ip, settings.gw_inverter_port, settings.telegram_token, settings.telegram_chatid)
        return mqtt_client, inverter[0], inverter[1]
    except:
        telegram_notify(settings.telegram_token, settings.telegram_chatid, "FATAL: gw2mqtt failed to connect to inverter or MQTT broker. Please investigate urgently")
        sys.exit("Failed to connect to inverter or MQTT broker")

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
    parser.add_argument("--mqtt-subscription-topic", help="MQTT subscribtion topic to listen to commands", metavar='MQTT_TOPIC')
    parser.add_argument("--pvo-api-key", help="PVOutput API key", metavar='KEY')
    parser.add_argument("--pvo-interval", help="PVOutput interval in minutes", type=int, choices=[5, 10, 15])
    parser.add_argument("--telegram-token", help="Telegram bot token", metavar='TELEGRAM_TOKEN')
    parser.add_argument("--telegram-chatid", help="Telegram chat id", metavar='TELEGRAM_CHATID')
    parser.add_argument("--telegram_token", help="Telegram bot token")
    parser.add_argument("--log", help="Set log level (default info)", choices=['debug', 'info', 'warning', 'critical'])
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    args = parser.parse_args()
    
    # Configure the logging
    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(format='%(levelname)-8s %(message)s', level=numeric_level)

    logging.debug("gw2mqtt version " + __version__)

    if args.gw_inverter_ip is None or args.mqtt_host is None:
        sys.exit("Missing --gw-inverter-ip or --mqtt-host")

    # Sample to inject single processes
    #if args.date:
    #    try:
    #        copy(args)
    #    except KeyboardInterrupt:
    #        sys.exit(1)
    #    except Exception as exp:
    #        logging.error(exp)
    #    sys.exit()
    #
    startTime = datetime.now()
    clients = run_once(args)
    logging.info(clients) 
    mqtt_client = clients[0]
    inverter = clients[1]
    inv_con_state = clients[2]

    logging.debug("Inverter client connection: " + str(inverter))
    logging.debug("MQTT broker client connection: " + str(mqtt_client))
    logging.debug("Inverter status: " + str(inv_con_state))

    while True:
        try:
            response = asyncio.run(inverter.read_runtime_data())
            for key, value in response.items():
                topic = ("emoncms/goodwe/" + str(key))
                mqtt_publish_data(mqtt_client, topic, value)
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as exp:
            logging.error(exp)

        if args.gw_interval is None:
            break

        interval = args.gw_interval
        time.sleep(interval - (datetime.now() - startTime).seconds % interval)

if __name__ == "__main__":
    run()
