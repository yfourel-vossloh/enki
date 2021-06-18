#!/usr/bin/env python
import sys
import shlex
import time
import random
import string
import os
import argparse
import cmd2
import threading
import paho.mqtt.client as mqtt


sys.path.insert(0, "tahu/client_libraries/python/")
import sparkplug_b as sparkplug
from sparkplug_b import *

sp_namespace = "spBv1.0"


def datatype_to_str(datatype):
    if (datatype == MetricDataType.Int8):
        return "Int8"
    elif datatype == MetricDataType.Int16:
        return "Int16"
    elif datatype == MetricDataType.Int32:
        return "Int32"
    elif datatype == MetricDataType.Int64:
        return "Int64"
    elif datatype == MetricDataType.UInt8:
        return "UInt8"
    elif datatype == MetricDataType.UInt16:
        return "UInt16"
    elif datatype == MetricDataType.UInt32:
        return "UInt32"
    elif datatype == MetricDataType.UInt64:
        return "UInt64"
    elif datatype == MetricDataType.Float:
        return "Float"
    elif datatype == MetricDataType.Double:
        return "Double"
    elif datatype == MetricDataType.Boolean:
        return "Boolean"
    elif datatype == MetricDataType.String:
        return "String"
    elif datatype == MetricDataType.DateTime:
        return "DateTime"
    elif datatype == MetricDataType.Text:
        return "Text"
    elif datatype == MetricDataType.UUID:
        return "UUID"
    elif datatype == MetricDataType.Bytes:
        return "Bytes"
    elif datatype == MetricDataType.File:
        return "File"
    elif datatype == MetricDataType.Template:
        return "Template"
    else:
        return "Invalid datatype %s" % str(datatype)


class SparkplugTopic:

    @staticmethod
    def create(group_id, cmd, eon_id, dev_id=None):
        topic_str = "%s/%s/%s/%s" % (sp_namespace, group_id, cmd, eon_id)
        if dev_id is not None:
            topic_str += "/%s" % (dev_id)
        return SparkplugTopic(topic_str)

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


def forge_payload_from_metric(payload, metric):
    """Add a user modified version of metric to payload"""
    int_value_types = [MetricDataType.Int8,
                       MetricDataType.Int16,
                       MetricDataType.Int32,
                       MetricDataType.UInt8,
                       MetricDataType.UInt16,
                       MetricDataType.UInt32]
    long_value_types = [MetricDataType.Int64,
                        MetricDataType.UInt64,
                        MetricDataType.DateTime]
    float_value_types = [MetricDataType.Float]
    double_value_types = [MetricDataType.Double]
    boolean_value_types = [MetricDataType.Boolean]
    string_value_types = [MetricDataType.String,
                          MetricDataType.Text,
                          MetricDataType.UUID]
    bytes_value_types = [MetricDataType.Bytes,
                         MetricDataType.File]
    if metric.datatype in int_value_types + long_value_types:
        value = int(input("Enter integer value %s:"
                          % (datatype_to_str(metric.datatype))))
        addMetric(payload, None, metric.alias, metric.datatype, value)
    else:
        print("not implemented")


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
    __instance = None
    def __new__(cls):
        if SparkplugNetwork.__instance is None:
            SparkplugNetwork.__instance = object.__new__(cls)
        return SparkplugNetwork.__instance

    def __init__(self):
        if "eon_nodes" not in self.__dict__:
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


# Application Variables
myGroupId = "Sparkplug B Devices"
myNodeName = "enki"
myUsername = "admin"
myPassword = "changeme"


######################################################################
# The callback for when a PUBLISH message is received from the server.
######################################################################
######################################################################


######################################################################
# SPShell
######################################################################
@cmd2.with_default_category('SPSH')
class SPShell(cmd2.Cmd):
    """Sparkplug Shell"""
    def __init__(self):
        cmd2.Cmd.__init__(self, allow_cli_args=False)
        self.prompt = "spsh> "

    def do_exit(self, *args):
        return True

    def help_list(self):
        print("list [short]:")
        print("  Show list of Edge of Network Nodes (EoN) and devices")
        print("")
        print("short: display short path to device instead of full group/eon/device")

    def do_list(self, *args):
        cmd_args = args[0].split()
        if len(cmd_args) == 0:
            full_view = True
        elif cmd_args[0] == "short":
            full_view = False
        else:
            print("Invalid argument: %s" % cmd_args[0])
            return

        sp_net = SparkplugNetwork()
        for eon in sp_net.eon_nodes:
            print("- %s/%s" % (eon.birth_topic.group_id, eon.birth_topic.edge_node_id))
            for dev in eon.devices:
                if full_view:
                    print("   * %s/%s/%s" % (eon.birth_topic.group_id,
                                             eon.birth_topic.edge_node_id,
                                             dev.birth_topic.device_id))
                else:
                    print("   * %s" % (dev.birth_topic.device_id))

    def complete_list(self, text, line, begidx, endidx):
        index_dict = {
            1: ["short"]
        }
        return self.index_based_complete(text, line, begidx, endidx, index_dict=index_dict)

    def help_metrics(self):
        print("metrics <sparkplug_id>")
        print("  Show metrics available for an Edge of Network Node or a device")
        print("")
        print("sparkplug_id:")
        print(" Unique string identifying the node or device requested")
        print(" EoN format: <group_id>/<eon_id>")
        print(" Devices format: <group_id>/<eon_id>/<device_id>")

    def do_metrics(self, *args):
        cmd_args = shlex.split(args[0])
        if len(cmd_args) == 0:
            print("Error: Missing sparkplug_id.")
            self.help_metrics()
            return

        sparkplug_id = cmd_args[0].split("/")
        if len(sparkplug_id) == 2:
            group_id = sparkplug_id[0]
            cmd = "NCMD"
            eon_id = sparkplug_id[1]
            dev_id = None
        elif len(sparkplug_id) == 3:
            group_id = sparkplug_id[0]
            cmd = "DCMD"
            eon_id = sparkplug_id[1]
            dev_id = sparkplug_id[2]
        else:
            print("Error: Invalid sparkplug_id: %s" % (cmd_args[0]))
            self.help_metrics()
            return

        topic = SparkplugTopic.create(group_id, cmd, eon_id, dev_id)

        sp_net = SparkplugNetwork()
        if dev_id is None:
            sp_dev = sp_net.find_eon(topic)
        else:
            sp_dev = sp_net.find_dev(topic)

        if sp_dev is not None:
            for m in sp_dev.metrics:
                print("%s[%d]: %s" % (m.name, m.alias, datatype_to_str(m.datatype)))

    def complete_metrics(self, text, line, begidx, endidx):
        sp_net = SparkplugNetwork()
        sp_id_list = []
        for eon in sp_net.eon_nodes:
            sp_id = "%s/%s" % (eon.birth_topic.group_id, eon.birth_topic.edge_node_id)
            sp_id_list.append(sp_id)
            for dev in eon.devices:
                sp_id = "%s/%s/%s" % (eon.birth_topic.group_id,
                                      eon.birth_topic.edge_node_id,
                                      dev.birth_topic.device_id)
                sp_id_list.append(sp_id)
        index_dict = {
            1: sp_id_list
        }
        return self.index_based_complete(text, line, begidx, endidx, index_dict=index_dict)

    def broker_list_topics(self, args):
        mqtt_if = MQTTInterface()
        for topic in mqtt_if.get_subscribed_topics():
            print(topic)

    def broker_sub(self, args):
        mqtt_if = MQTTInterface()
        mqtt_if.subscribe(args.topic)

    def broker_unsub(self, args):
        mqtt_if = MQTTInterface()
        mqtt_if.unsubscribe(args.topic)

    parser_broker = cmd2.Cmd2ArgumentParser()
    subparser_broker = parser_broker.add_subparsers(help='broker subcommands')
    parser_list = subparser_broker.add_parser('list', help='List subscribed topics')
    parser_list.set_defaults(func=broker_list_topics)
    parser_sub = subparser_broker.add_parser('subscribe',
                                             help='Subscribe to topic')
    parser_sub.add_argument('topic', help='Topic to subcribe to')
    parser_sub.set_defaults(func=broker_sub)
    parser_unsub = subparser_broker.add_parser('unsubscribe',
                                               help='Unsubscribe from topic')
    parser_unsub.add_argument('topic', help='Topic to unsubcribe from')
    parser_unsub.set_defaults(func=broker_unsub)

    @cmd2.with_argparser(parser_broker)
    def do_broker(self, args):
        """Manage broker subscriptions"""
        args.func(self, args)


class MQTTInterface(threading.Thread):
    __instance = None
    def __new__(cls):
        if MQTTInterface.__instance is None:
            MQTTInterface.__instance = object.__new__(cls)
        return MQTTInterface.__instance

    def __init__(self):
        if "server" in self.__dict__:
            return

        super(MQTTInterface, self).__init__()
        self.server = None
        self.stop_request = threading.Event()

        self.client = mqtt.Client("enki_%d" % os.getpid(), 1883, 60)
        self.client.user_data_set(self)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(myUsername, myPassword)
        self.subscribed_topics = ["spBv1.0/#"]

    def set_server(self, server):
        self.server = server

    def get_subscribed_topics(self):
        return self.subscribed_topics

    def subscribe(self, topic):
        if topic not in self.subscribed_topics:
            self.client.subscribe(topic)
            self.subscribed_topics.append(topic)

    def unsubscribe(self, topic):
        if topic in self.subscribed_topics:
            self.client.unsubscribe(topic)
            self.subscribed_topics.remove(topic)

    @staticmethod
    def on_connect(client, userdata, flags, rc):
        """ The callback for when the client receives a CONNACK response from the server."""
        if rc == 0:
            print("Connected with result code "+str(rc))
        else:
            print("Failed to connect with result code "+str(rc))
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
            #else:
            #    for m in inboundPayload.metrics:
            #        dev.print_metric(m)

    def join(self, timeout=None):
        self.stop_request.set()
        super(MQTTInterface, self).join(timeout)

    def run(self):
        self.client.connect(self.server, 1883, 60)

        while not self.stop_request.isSet():
            self.client.loop()


######################################################################
# Main Application
######################################################################
def main():
    parser = argparse.ArgumentParser(description="View and manipulate sparkplug payload")
    parser.add_argument('--server',
                        help='MQTT broker address', default='localhost')
    args = parser.parse_args()

    mqtt_if = MQTTInterface()
    mqtt_if.set_server(args.server)
    time.sleep(.1)
    mqtt_if.start()

    spshell = SPShell()
    sys.exit(spshell.cmdloop("Sparkplug Shell"))
######################################################################


if __name__ == "__main__":
    main()
