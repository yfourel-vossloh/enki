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
import pathlib
import datetime
import paho.mqtt.client as mqtt


sys.path.insert(0, "tahu/client_libraries/python/")
import sparkplug_b as sparkplug
from sparkplug_b import *

# Application Variables
myUsername = "admin"
myPassword = "changeme"
sp_namespace = "spBv1.0"

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


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


def str_to_int(s):
    """Convert string to int.

    String must be a decimal or hexadecimal value with 0x prefix
    """
    s = s.strip()
    if s[0:2] == '0x':
        return int(s, 16)
    else:
        return int(s)


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
    elif datatype == MetricDataType.DataSet:
        return "DataSet"
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


def prompt_user_simple_datatype(name, datatype):
    usr_input = input("[%s] %s: " % (datatype_to_str(datatype), name))
    value = None
    if datatype in int_value_types + long_value_types:
        value = str_to_int(usr_input)
    elif datatype in boolean_value_types:
        usr_input = input("Entre True or False:")
        if usr_input == "True":
            value = True
        elif usr_input == "False":
            value = False
    elif datatype in string_value_types:
        value = usr_input

    return value


def add_value_to_element(element, value, type):
    if type == MetricDataType.Int8:
        element.int_value = value
    elif type == MetricDataType.Int16:
        element.int_value = value
    elif type == MetricDataType.Int32:
        element.int_value = value
    elif type == MetricDataType.Int64:
        element.long_value = value
    elif type == MetricDataType.UInt8:
        element.int_value = value
    elif type == MetricDataType.UInt16:
        element.int_value = value
    elif type == MetricDataType.UInt32:
        element.int_value = value
    elif type == MetricDataType.UInt64:
        element.long_value = value
    elif type == MetricDataType.Float:
        element.float_value = value
    elif type == MetricDataType.Double:
        element.double_value = value
    elif type == MetricDataType.Boolean:
        element.boolean_value = value
    elif type == MetricDataType.String:
        element.string_value = value
    elif type == MetricDataType.DateTime:
        element.long_value = value
    elif type == MetricDataType.Text:
        element.string_value = value
    else:
        print("Invalid: " + str(type))


def forge_dataset_metric(payload, metric):
    dataset = initDatasetMetric(payload, metric.name, metric.alias,
                                metric.dataset_value.columns,
                                metric.dataset_value.types)

    new_row = True
    while new_row:
        row = dataset.rows.add()
        for (col, datatype) in zip(metric.dataset_value.columns, metric.dataset_value.types):
            name = "%s/%s" % (metric.name, col)
            value = prompt_user_simple_datatype(name, datatype)
            element = row.elements.add()
            add_value_to_element(element, value, datatype)
        new_row = query_yes_no("new row ?")
    print(payload)


def forge_payload_from_metric(payload, metric):
    """Add a user modified version of metric to payload"""
    simple_datatype = int_value_types + long_value_types + boolean_value_types
    if metric.datatype in int_value_types + long_value_types:
        value = prompt_user_simple_datatype(metric.name, metric.datatype)
        addMetric(payload, None, metric.alias, metric.datatype, value)
    elif metric.datatype == MetricDataType.DataSet:
        forge_dataset_metric(payload, metric)
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
        metrics = []
        for m in self.metrics:
            if m.alias == alias:
                metrics.append(m)
        return metrics

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


class SPLogger(object):
    """Log every Sparkplug Payload on a specified topic"""
    __loggers = list()
    __timestamp = datetime.datetime.today().strftime('%Y-%m-%d_%H%M%S')

    def __new__(cls, *args, **kwargs):
        topic = args[0]
        instance = cls.get_by_topic(topic)
        if instance is None:
            instance = super(SPLogger, cls).__new__(cls)
            cls.__loggers.append(instance)
        else:
            print("Logger for %s already exist" % (topic))
            instance = None
        return instance

    def __init__(self, topic):
        self.subscribed_topic = topic
        mqtt_if = MQTTInterface()
        mqtt_if.subscribe(topic)
        topic_sanitized = topic.replace("+", "").replace("#", "").replace("//", "/").rstrip("/")
        self.path = "logs_" + self.__timestamp + "/" + topic_sanitized + ".txt"
        pathlib.Path(os.path.dirname(self.path)).mkdir(parents=True, exist_ok=True)
        self.fd = open(self.path, 'w')

    @classmethod
    def list(cls):
        idx = 0
        for l in cls.__loggers:
            print("%d) %s" % (idx, l.subscribed_topic))
            idx += 1

    @classmethod
    def get_by_topic(cls, topic):
        for logger in cls.__loggers:
            if topic == logger.subscribed_topic:
                return logger
        return None

    @classmethod
    def get_all_matching_topic(cls, topic):
        matches = []
        for logger in cls.__loggers:
            if mqtt.topic_matches_sub(logger.subscribed_topic, topic):
                matches.append(logger)
        return matches

    def stop_instance(self):
        self.fd.close()
        mqtt_if = MQTTInterface()
        mqtt_if.unsubscribe(self.subscribed_topic)
        self.__loggers.remove(self)

    @classmethod
    def stop(cls, topic):
        logger = cls.get_by_topic(topic)
        if logger is None:
            print("Error: %s is not an active logger" % (topic))
        else:
            logger.stop_instance()
        return

    @classmethod
    def stop_all(cls):
        for l in cls.__loggers:
            l.stop_instance()

    def process_payload(self, payload):
        self.fd.write(str(payload))


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
        # Remove any existing EoN
        old_eon = self.find_eon(eon.birth_topic)
        if old_eon is not None:
            self.eon_nodes.remove(old_eon)
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

    parser_list = cmd2.Cmd2ArgumentParser()
    parser_list.add_argument('--short', action='store_true', default=False,
                             help="display short path to device instead of full group/eon/device")

    @cmd2.with_argparser(parser_list)
    def do_list(self, args):
        """Show list of birthed Edge of Network Nodes (EoN) and devices"""
        sp_net = SparkplugNetwork()
        for eon in sp_net.eon_nodes:
            print("- %s/%s" % (eon.birth_topic.group_id, eon.birth_topic.edge_node_id))
            for dev in eon.devices:
                if not args.short:
                    print("   * %s/%s/%s" % (eon.birth_topic.group_id,
                                             eon.birth_topic.edge_node_id,
                                             dev.birth_topic.device_id))
                else:
                    print("   * %s" % (dev.birth_topic.device_id))

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
                print(m)

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

    parser_send = cmd2.Cmd2ArgumentParser()
    send_cmd_choices = ['NCMD', 'DCMD', 'NDATA', 'DDATA']
    parser_send.add_argument('cmd_type', choices=send_cmd_choices,
                             help='Command type the payload is sent with')
    parser_send.add_argument('sparkplug_id',
                             help='Id of EoN or device as returned by command "list"')

    def choose_metric(self, sp_dev):
        metrics = []
        for m in sp_dev.metrics:
            if m.name == "bdSeq":
                continue
            metrics.append((m.alias, m.name))
        alias = self.select(metrics, "metric ? ")
        return alias

    @cmd2.with_argparser(parser_send)
    def do_send(self, args):
        """Forge a payload to send for a particular EoN or device"""
        sp_net = SparkplugNetwork()
        sparkplug_id = args.sparkplug_id.split("/")
        if len(sparkplug_id) == 2:
            group_id = sparkplug_id[0]
            cmd = args.cmd_type
            eon_id = sparkplug_id[1]
            dev_id = None
        elif len(sparkplug_id) == 3:
            group_id = sparkplug_id[0]
            cmd = args.cmd_type
            eon_id = sparkplug_id[1]
            dev_id = sparkplug_id[2]
        else:
            print("Error: invalid sparkplug_id: %s" % (args.sparkplug_id))
            return

        topic = SparkplugTopic.create(group_id, cmd, eon_id, dev_id)
        if dev_id is None:
            sp_dev = sp_net.find_eon(topic)
        else:
            sp_dev = sp_net.find_dev(topic)

        alias = int(self.choose_metric(sp_dev))
        metric_candidates = sp_dev.get_metric(alias)
        assert(len(metric_candidates) > 0)
        if len(metric_candidates) > 1:
            print("More than one metric with alias %d" % (alias))
            idx = 0
            for m in metric_candidates:
                print("%d: %s" % (idx, m.name))
                idx += 1
            while True:
                try:
                    usr_input = input("Enter metric index")
                    idx = int(usr_input)
                    metric = metric_candidates[idx]
                except:
                    print("Invalid index: %s" % usr_input)
                    continue
                else:
                    break
        else:
            metric = metric_candidates[0]

        payload = sparkplug_b_pb2.Payload()

        forge_payload_from_metric(payload, metric)
        byte_array = bytearray(payload.SerializeToString())
        mqtt_if = MQTTInterface()
        mqtt_if.publish(str(topic), byte_array, 0, False)

    def logger_list(self, args):
        SPLogger.list()

    def logger_stop(self, args):
        SPLogger.stop(args.logger_id)

    def logger_spid(self, args):
        sparkplug_id = args.sparkplug_id.split("/")
        cmd = "+"
        if len(sparkplug_id) == 2:
            dev_id = None
        elif len(sparkplug_id) == 3:
            dev_id = sparkplug_id[2]
        else:
            print("Error: invalid sparkplug_id: %s" % (args.sparkplug_id))
            return
        group_id = sparkplug_id[0]
        eon_id = sparkplug_id[1]

        topic = SparkplugTopic.create(group_id, cmd, eon_id, dev_id)
        logger = SPLogger(str(topic))

    parser_logger = cmd2.Cmd2ArgumentParser()
    subparser_logger = parser_logger.add_subparsers(help='logger subcommands')
    parser_logger_spid = subparser_logger.add_parser('spid', help='Start logging messages exchanged '
                                                     'with a sparkplug_id')
    parser_logger_spid.add_argument('sparkplug_id',
                                    help='Id of EoN or device as returned by command "list"')
    parser_logger_spid.set_defaults(func=logger_spid)

    parser_logger_list = subparser_logger.add_parser('list', help='List active loggers and id to stop them')
    parser_logger_list.set_defaults(func=logger_list)

    parser_logger_stop = subparser_logger.add_parser('stop', help='Stop an active logger')
    parser_logger_stop.add_argument('logger_id',
                                    help='Logger id to stop as returned by command "logger list"')
    parser_logger_stop.set_defaults(func=logger_stop)

    @cmd2.with_argparser(parser_logger)
    def do_logger(self, args):
        """Log payloads related to a topic or a sparkplug id"""
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

    def publish(self, topic, byte_array, qos, retain):
        self.client.publish(topic, byte_array, qos, retain)

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
        inboundPayload = sparkplug_b_pb2.Payload()
        inboundPayload.ParseFromString(msg.payload)
        if topic.is_nbirth():
            print("Register node birth: %s" % (topic))
            node = EdgeNode(topic, inboundPayload.metrics)
            sp_net.add_eon(node)
        elif topic.is_dbirth():
            print("Register device birth: %s" % (topic))
            eon = sp_net.find_eon(topic)
            assert eon is not None, "Device birth before Node birth is not allowed"
            dev = SPDev(topic, inboundPayload.metrics)
            eon.add_dev(dev)
        elif topic.is_ddata():
            dev = sp_net.find_dev(topic)
            if dev is None:
                print("Unknown device for topic : %s" % (topic))

        loggers = SPLogger.get_all_matching_topic(msg.topic)
        for l in loggers:
            l.process_payload(inboundPayload)

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
    ret = spshell.cmdloop("Sparkplug Shell")
    MQTTInterface().join()
    SPLogger.stop_all()
    sys.exit(ret)
######################################################################


if __name__ == "__main__":
    main()
