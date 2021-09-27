"""Manage MQTT connexion, subscription and publishing."""
import os
import sys
import threading
import paho.mqtt.client as mqtt

import sparkplug_b_pb2

from sp_topic import SparkplugTopic
from sp_dev import SPDev, EdgeNode
from sp_network import SparkplugNetwork
import sp_logger

MYUSERNAME = "admin"
MYPASSWORD = "changeme"

class MQTTInterface(object):
    """MQTT Interface management."""
    __instance = None

    def __new__(cls):
        if MQTTInterface.__instance is None:
            MQTTInterface.__instance = object.__new__(cls)
        return MQTTInterface.__instance

    def __init__(self):
        if "server" in self.__dict__:
            return

        super().__init__()
        self.server = None

        self.client = mqtt.Client("enki_%d" % os.getpid(), 1883, 60)
        self.client.user_data_set(self)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(MYUSERNAME, MYPASSWORD)
        self.subscribed_topics = ["spBv1.0/#"]
        self.forwarded_topics = {}

    def set_server(self, server):
        """Set mqtt server address."""
        self.server = server

    def get_subscribed_topics(self):
        """Get list of topics subscribed to."""
        return self.subscribed_topics

    def subscribe(self, topic):
        """Subscribe to a topic."""
        if topic not in self.subscribed_topics:
            self.client.subscribe(topic)
            self.subscribed_topics.append(topic)

    def unsubscribe(self, topic):
        """Unsubscribe from topic."""
        if topic in self.subscribed_topics:
            self.client.unsubscribe(topic)
            self.subscribed_topics.remove(topic)

    def publish(self, topic, byte_array, qos, retain):
        """Publish message on topic."""
        self.client.publish(topic, byte_array, qos, retain)

    def forward_topic(self, topic, q_io):
        """Forward messages received on topic to queue"""
        self.forwarded_topics[topic] = q_io

    def stop_forwarding(self, topic):
        """Stop forwarding messages received on topic"""
        self.forwarded_topics.pop(topic)

    @staticmethod
    def on_connect(client, userdata, flags, ret):
        """The callback for when the client receives a CONNACK response from the server."""
        if ret == 0:
            print("Connected with result code "+str(ret))
        else:
            print("Failed to connect with result code "+str(ret))
            sys.exit()

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        for topic in userdata.subscribed_topics:
            client.subscribe(topic)

    @staticmethod
    def on_message(client, userdata, msg):
        """The callback for when a PUBLISH message is received from the server."""
        topic = SparkplugTopic(msg.topic)

        sp_net = SparkplugNetwork()
        payload = sparkplug_b_pb2.Payload()
        payload.ParseFromString(msg.payload)
        if topic.is_nbirth():
            print("Register node birth: %s" % (topic))
            node = EdgeNode(topic, payload.metrics)
            sp_net.add_eon(node)
        elif topic.is_dbirth():
            print("Register device birth: %s" % (topic))
            eon = sp_net.find_eon(topic)
            assert eon is not None, "Device birth before Node birth is not allowed"
            dev = SPDev(topic, payload.metrics)
            eon.add_dev(dev)
        elif topic.is_ddata():
            dev = sp_net.find_dev(topic)
            if dev is None:
                print("Unknown device for topic : %s" % (topic))

        loggers = sp_logger.SPLogger.get_all_matching_topic(msg.topic)
        for logger in loggers:
            logger.process_payload(payload)

        for (topic, q_io) in userdata.forwarded_topics.items():
            if mqtt.topic_matches_sub(topic, msg.topic):
                q_io.put(msg)

    def join(self, timeout=None):
        self.client.loop_stop()
        MQTTInterface.__instance = None

    def start(self):
        self.client.connect(self.server, 1883, 60)
        self.client.loop_start()
