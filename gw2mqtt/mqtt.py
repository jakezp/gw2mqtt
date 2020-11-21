import sys, os
import time
import logging
import telegram

import paho.mqtt.client as mqtt

from datetime import datetime

__author__ = "Jacqueco Peenz"
__copyright__ = "Copyright 2020, Jacqueco Peenz"
__license__ = "MIT"
__email__ = "jakezp@gmail.com"
__credit__ = "https://github.com/jkairys/mqtt-pvoutput-bridge"

class MQTT:

    def __init__(self, telegram_token, telegram_chatid, mqtt_host, mqtt_port, mqtt_user, mqtt_password, mqtt_topic):
        self.telegram_token = telegram_token
        self.telegram_chatid = telegram_chatid
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_user = mqtt_user
        self.mqtt_password = mqtt_password
        self.mqtt_topic = mqtt_topic
        self.currentTime = datetime.now()
        self.client = mqtt.Client()
        mqtt.Client.connected_flag = False
        mqtt.Client.bad_connection_flag = False

    # Telegram
    def telegram_notify(self, telegram_token, telegram_chatid, message):
        token = self.telegram_token
        chat_id = self.telegram_chatid
        bot = telegram.Bot(token=token)
        bot.sendMessage(chat_id=chat_id, text=message)

    def mqtt_server_connection(self, mqtt_host, mqtt_port, mqtt_user, mqtt_password, mqtt_topic):
        try:
            client = self.client
            client.on_connect = self.on_connect
            client.username_pw_set(self.mqtt_user, password=self.mqtt_password)
            client.connect(self.mqtt_host, port=int(mqtt_port))
            client.loop_start()
            if not client.connected_flag and not client.bad_connection_flag:
                time.sleep(5)
            if client.bad_connection_flag:
                client.loop_stop() 
                sys.exit(1)
            return
        except Exception as exp:
            errorMsg = ("Unable to connect mqtt broker - " + str(self.mqtt_host) + " - Reason: " + str(exp))
            logging.error(str(self.currentTime) + " - " + str(errorMsg))
            self.telegram_notify(self.telegram_token, self.telegram_chatid, errorMsg)
            sys.exit(1)
    
    def on_connect(self, client, userdata, flags, rc):
        if rc==0:
            client.connected_flag=True
            successMsg = ("Connected to mqtt broker - " + str(self.mqtt_host) + " - Result: " + str(rc))
            logging.info(str(self.currentTime) + " - " + str(successMsg))
            self.telegram_notify(self.telegram_token, self.telegram_chatid, successMsg)
        else:
            client.bad_connection_flag=True
            errorMsg = ("Unable to connect mqtt broker - " + str(self.mqtt_host) + " - Result: " + str(rc))
            logging.error(str(self.currentTime) + " - " + str(errorMsg))
            self.telegram_notify(self.telegram_token, self.telegram_chatid, errorMsg)
    
    def mqtt_get_socket(self):
        socket = self.client.socket()
        if socket is not None:
            return socket

    def mqtt_publish_data(self, client, mqtt_topic, payload):
        self.client.publish(mqtt_topic, payload)

    def mqtt_disconnect(self):
        self.client.loop_stop()
        sys.exit(1)
