"""Manage MQTT connexion, subscription and publishing."""
import os
import sys
import ssl
import uritools
import paho.mqtt.client as mqtt


MYUSERNAME = "admin"
MYPASSWORD = "changeme"
DEFAULT_INSECURE_MQTT_PORT = 1883
DEFAULT_TLS_MQTT_PORT = 8883

# pylint: disable=too-many-instance-attributes
class MQTTInterface:
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
        self.mqtts = False
        self.client_name = f"enki_{os.getpid()}"
        self.client = mqtt.Client(self.client_name, 1883, 60)
        self.client.user_data_set(self)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(MYUSERNAME, MYPASSWORD)
        self.subscribed_topics = ["spBv1.0/#"]
        self.forwarded_topics = {}
        self.connect_callback = None
        self.disconnect_callback = None
        self.message_callback = None

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
        self.mqtts = uri.scheme == "mqtts"
        if self.mqtts:
            port = uri.getport(default=DEFAULT_TLS_MQTT_PORT)
        else:
            port = uri.getport(default=DEFAULT_INSECURE_MQTT_PORT)

        host = str(uri.gethost())
        self.set_server(host, port, certificate)

    def get_uri(self) -> str:
        """Returns the broker's URI."""
        scheme = "mqtts" if self.mqtts else "mqtt"
        return f"{scheme}://{self.server}:{self.port}"

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
    def on_connect(client, userdata, _flags, ret):
        """The callback for when the client receives a CONNACK response from the server."""
        if ret != 0:
            print("Failed to connect with result code " + str(ret))
            sys.exit()

        if userdata.connect_callback is not None:
            userdata.connect_callback()

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        for topic in userdata.subscribed_topics:
            client.subscribe(topic)

    @staticmethod
    def on_message(_client, userdata, msg):
        """The callback for when a PUBLISH message is received from the server."""
        if userdata.message_callback:
            userdata.message_callback(userdata, msg)

        for (topic, q_io) in userdata.forwarded_topics.items():
            if mqtt.topic_matches_sub(topic, msg.topic):
                q_io.put(msg)

    def join(self, _timeout=None):
        """Wait for the MQTT loop to stop."""
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
