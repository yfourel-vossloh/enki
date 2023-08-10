"""Manage MQTT connexion, subscription and publishing."""
import os
import sys
import threading
import uritools
import ssl
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
        self.port = None

        self.client = mqtt.Client("enki_%d" % os.getpid(), 1883, 60)
        self.client.user_data_set(self)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(MYUSERNAME, MYPASSWORD)
        self.subscribed_topics = ["spBv1.0/#"]
        self.forwarded_topics = {}

    def set_server(self, server, port, certificate=None):
        """Set mqtt server address and port."""
        self.server = server
        self.port = port
        if certificate is not None:
            self.client.tls_set(certificate, tls_version=ssl.PROTOCOL_TLSv1_2)

    def set_server_from_uri(self, server_uri, certificate=None):
        """Set mqtt server from its URI."""
        assert uritools.isuri(server_uri), f"{server_uri} is not a valid URI"
        uri = uritools.urisplit(server_uri)
        mqtts = uri.scheme == "mqtts"
        if mqtts:
            port = uri.getport(default=8883)
        else:
            port = uri.getport(default=1883)

        host = str(uri.gethost())
        self.set_server(host, port, certificate)

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
        if ret != 0:
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
            eon = sp_net.find_eon(topic)
            if dev is None:
                print("Unknown device for topic : %s" % (topic))
            else:
                for metric in payload.metrics:
                    dev_metric = dev.get_metric(metric.name, metric.alias)
                    if dev_metric:
                        dev.update_metric(metric)
                        print("DDATA from device %s" % dev.get_short_handle())
                        dev.print_metric(metric)
                    else:
                        print(f"No match for metric {metric.name}/{metric.alias} "
                              f"in device {dev.get_short_handle()}")
        elif topic.is_ddeath():
            dev = sp_net.find_dev(topic)
            eon = sp_net.find_eon(topic)
            if dev is not None and eon is not None:
                print("Device %s died" % dev.get_short_handle())
                eon.remove_dev(dev)

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
        """Connect to the broker and start mqtt loop."""
        self.client.connect(self.server, self.port, 60)
        self.client.loop_start()

    def stop(self):
        """Stop loop and disconnect from the broker."""
        self.client.loop_stop()
        self.client.disconnect()
