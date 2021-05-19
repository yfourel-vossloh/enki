#!/usr/bin/env python
import sys
sys.path.insert(0, "tahu/client_libraries/python/")

import paho.mqtt.client as mqtt
import sparkplug_b as sparkplug
import time
import random
import string

from sparkplug_b import *


class SparkplugTopic:

    def __init__(self, topic):
        tokens = topic.split("/")
        self.topic = topic
        if len(tokens) != 4 and len(tokens) != 5:
            self.valid_topic = False
        else:
            self.namespace = tokens[0]
            self.group_id = tokens[1]
            self.message_type = tokens[2]
            self.edge_node_id = tokens[3]
            if len(tokens) == 5:
                self.device_id = tokens[4]
            else:
                self.device_id = None

    def is_nbirth(self):
        return self.message_type == "NBIRTH"

    def is_dbirth(self):
        return self.message_type == "DBIRTH"

    def is_ndata(self):
        return self.message_type == "NDATA"

    def is_ddata(self):
        return self.message_type == "DDATA"

    def __repr__(self):
        return "%s(\"%s\")" % (type(self).__name__, self.topic)

    def __str__(self):
        return "%s" % (self.topic)


class SPDev:
    """Base class for Edge of Network Nodes or Devices"""
    def __init__(self, birth_topic, metrics):
        self.birth_topic = birth_topic
        self.edge_node_id = birth_topic.edge_node_id
        self.metrics = metrics

    def __repr__(self):
        return "%s(\"%s\")" % (type(self).__name__, self.birth_topic)

    def add_metric(self, metric):
        """Add a metric to a device

        The alias of the added metric must not already exists in the metrics
        attached to the Device
        """
        for m in self.metrics:
            assert m.alias == metric.alias, \
                    "Alias %d already exists in device" % (m.alias)

        self.metrics.append(metric)

    def get_metric(self, alias):
        """Get metric object from an alias"""
        for m in self.metrics:
            if m.alias == alias:
                return m
        return None

    @classmethod
    def get_metric_val_str(cls, metric):
        # Use google's protobuf backend to print metric, it's quite verbose...
        return "%s" % (metric)

    def get_metric_str(self, metric):
        """Return string describing metric if it is known to Device"""
        for m in self.metrics:
            if m.alias == metric.alias:
                s = "%s: %s" % (m.name, self.get_metric_val_str(metric))
                return s
        return None

    def print_metric(self, metric):
        """Print received metric using list of known metrics"""
        s = self.get_metric_str(metric)
        if s is None:
            print("Unknown metric %d for Edge Node %s" % (metric.alias,
                                                          self.edge_node_id))
        else:
            print(s)


class EdgeNode(SPDev):
    def __init__(self, birth_topic, metrics):
        super().__init__(birth_topic, metrics)
        self.devices = list()

    def add_dev(self, device):
        # TODO: check if device does not already exist.
        self.devices.append(device)


class SparkplugNetwork(object):
    class __SparkplugNetwork:
        def __init__(self):
            self.eon_nodes = list()

        def __str__(self):
            return self.eon_nodes

        def add_eon(self, eon):
            self.eon_nodes.append(eon)

        def find_eon(self, topic):
            for eon in self.eon_nodes:
                if (eon.birth_topic.namespace == topic.namespace and
                    eon.birth_topic.group_id == topic.group_id and
                    eon.birth_topic.edge_node_id == topic.edge_node_id):
                    return eon
            return None

        def find_dev(self, topic):
            assert topic.device_id is not None, \
                    "Invalid device topic: %s" % (topic)
            eon = self.find_eon(topic)
            if eon is None:
                return None
            for dev in eon.devices:
                if dev.birth_topic.device_id == topic.device_id:
                    return dev
            return None

    instance = None

    def __new__(cls): # __new__ always a classmethod
        if not SparkplugNetwork.instance:
            SparkplugNetwork.instance = SparkplugNetwork.__SparkplugNetwork()
        return SparkplugNetwork.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)


# Application Variables
serverUrl = "localhost"
myGroupId = "Sparkplug B Devices"
myNodeName = "enki"
myUsername = "admin"
myPassword = "changeme"

######################################################################
# The callback for when the client receives a CONNACK response from the server.
######################################################################
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected with result code "+str(rc))
    else:
        print("Failed to connect with result code "+str(rc))
        sys.exit()

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("spBv1.0/" + myGroupId + "/#")
    client.subscribe("spBv1.0/" + myGroupId + "/#")
######################################################################

######################################################################
# The callback for when a PUBLISH message is received from the server.
######################################################################
def on_message(client, userdata, msg):
    topic = SparkplugTopic(msg.topic)
    print("Message arrived: %s" % (topic))

    sp_net = SparkplugNetwork()
    if topic.is_nbirth():
        print("Register node birth")
        inboundPayload = sparkplug_b_pb2.Payload()
        inboundPayload.ParseFromString(msg.payload)
        node = EdgeNode(topic, inboundPayload.metrics)
        sp_net.add_eon(node)
        for m in inboundPayload.metrics:
            node.print_metric(m)
    elif topic.is_dbirth():
        print("Register device birth")
        eon = sp_net.find_eon(topic)
        assert eon is not None, "Device birth before Node birth is not allowed"
        inboundPayload = sparkplug_b_pb2.Payload()
        inboundPayload.ParseFromString(msg.payload)
        dev = SPDev(topic, inboundPayload.metrics)
        eon.add_dev(dev)
        for m in inboundPayload.metrics:
            dev.print_metric(m)
    elif topic.is_ddata():
        inboundPayload = sparkplug_b_pb2.Payload()
        inboundPayload.ParseFromString(msg.payload)
        dev = sp_net.find_dev(topic)
        if dev is None:
            print("Unknown device for topic : %s" % (topic))
        else:
            for m in inboundPayload.metrics:
                dev.print_metric(m)
    print("------------------")


######################################################################

######################################################################
# Main Application
######################################################################
def main():
    print("Starting main application")

    # Create the node death payload
    deathPayload = sparkplug.getNodeDeathPayload()

    # Start of main program - Set up the MQTT client connection
    client = mqtt.Client(serverUrl + "enki", 1883, 60)
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(myUsername, myPassword)
    deathByteArray = bytearray(deathPayload.SerializeToString())
    client.will_set("spBv1.0/" + myGroupId + "/NDEATH/" + myNodeName,
                    deathByteArray, 0, False)
    client.connect(serverUrl, 1883, 60)

    # Short delay to allow connect callback to occur
    time.sleep(.1)
    client.loop_start()

    while True:

        # Sit and wait for inbound or outbound events
        for _ in range(50):
            time.sleep(.1)
######################################################################

if __name__ == "__main__":
    main()
