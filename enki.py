#!/usr/bin/env python
import sys
import shlex
import time
import argparse
import cmd2


import sparkplug_b_pb2
from sparkplug_b import MetricDataType, addMetric, initDatasetMetric
from sp_topic import SparkplugTopic
from sp_logger import SPLogger
from mqtt_if import MQTTInterface
from sp_network import SparkplugNetwork
from sp_id import SparkplugId

# Application Variables
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
    if datatype == MetricDataType.Int8:
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

def get_dev_from_sparkplug_id(sparkplug_id):
        sparkplug_id = sparkplug_id.split("/")

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
            return None

        topic = SparkplugTopic.create(group_id, cmd, eon_id, dev_id)
        sp_net = SparkplugNetwork()
        if dev_id is None:
            sp_dev = sp_net.find_eon(topic)
        else:
            sp_dev = sp_net.find_dev(topic)

        return sp_dev

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

    def build_target_list(self, include_eon, include_dev):
        res = []
        sp_net = SparkplugNetwork()
        for eon in sp_net.eon_nodes:
            eon_id = f"{eon.birth_topic.group_id}/{eon.birth_topic.edge_node_id}"
            if include_eon:
                res.append(eon_id)
            if include_dev:
                for dev in eon.devices:
                    res.append(f"{eon_id}/{dev.birth_topic.device_id}")
        return res

    def get_all_targets(self):
        return self.build_target_list(include_eon=True, include_dev=True)

    def get_all_eons(self):
        return self.build_target_list(include_eon=True, include_dev=False)

    def get_all_devices(self):
        return self.build_target_list(include_eon=False, include_dev=True)

    def help_metrics(self):
        print("metrics <sparkplug_id>")
        print("  Show metrics available for an Edge of Network Node or a device")
        print("")
        print("sparkplug_id:")
        print(" Unique string identifying the node or device requested")
        print(" EoN format: <group_id>/<eon_id>")
        print(" Devices format: <group_id>/<eon_id>/<device_id>")

    metrics_parser = cmd2.Cmd2ArgumentParser()
    metrics_parser.add_argument("sparkplug_id", choices_provider=get_all_targets)

    @cmd2.with_argparser(metrics_parser)
    def do_metrics(self, args):
        sp_dev = get_dev_from_sparkplug_id(args.sparkplug_id)
        if sp_dev is not None:
            for m in sp_dev.metrics:
                sp_dev.print_metric(m)
        else:
            print("Error: Invalid sparkplug_id: %s" % (args.sparkplug_id))
            self.help_metrics()

    def get_metrics_of_sparkplug_id(self, sparkplug_id):
        sp_dev = get_dev_from_sparkplug_id(sparkplug_id)
        if sp_dev is not None:
            return [m.name for m in sp_dev.metrics]
        return []

    def choices_dev_metrics_provider(self, arg_tokens):
        if "metric_name" in arg_tokens and "sparkplug_id" in arg_tokens:
            sparkplug_id = arg_tokens["sparkplug_id"]
            if isinstance(sparkplug_id, list) and sparkplug_id:
                return self.get_metrics_of_sparkplug_id(sparkplug_id[0])
        return self.get_all_targets()

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

    parser_print = cmd2.Cmd2ArgumentParser()
    parser_print.add_argument("sparkplug_id", choices_provider=choices_dev_metrics_provider, help="EoN Id or Device Id")
    parser_print.add_argument("metric_name", choices_provider=choices_dev_metrics_provider, help="Metric name")

    @cmd2.with_argparser(parser_print)
    def do_print(self, args):
        """Prints the metric current value for a specific Edge of Network Node or device"""
        sp_dev = get_dev_from_sparkplug_id(args.sparkplug_id)
        if sp_dev is not None:
            metric = sp_dev.get_metric(args.metric_name)
            if metric is not None:
                sp_dev.print_metric(metric)
            else:
                print(f"No metric '{args.metric_name}' belonging to '{args.sparkplug_id}'")
        else:
            print(f"Unknown sparkplug Id '{args.sparkplug_id}'")

    @cmd2.with_argparser(parser_broker)
    def do_broker(self, args):
        """Manage broker subscriptions"""
        args.func(self, args)

    parser_send = cmd2.Cmd2ArgumentParser()
    send_cmd_choices = ['NCMD', 'DCMD', 'NDATA', 'DDATA']
    parser_send.add_argument('cmd_type', choices=send_cmd_choices,
                             help='Command type the payload is sent with')
    parser_send.add_argument('sparkplug_id',
                             choices_provider=get_all_targets,
                             help='Id of EoN or device as returned by command "list"')

    def choose_metric(self, sp_dev):
        metrics = []
        for m in sp_dev.metrics:
            if m.name == "bdSeq":
                continue
            metrics.append(m.name)
        metric_name = self.select(metrics, "metric ? ")
        metric = sp_dev.get_metric(metric_name)
        assert metric is not None, "Could not find requested metric"
        return metric

    def query_yes_no(self, prompt):
        yesses = ["yes", "y", "YES", "Yes"]
        nos = ["no", "n", "NO", "No"]
        while True:
            usr_input = self.read_input(prompt + "[y/n]", choices=yesses + nos,
                                        completion_mode=cmd2.utils.CompletionMode.CUSTOM)
            if usr_input in yesses:
                return True
            elif usr_input in nos:
                return False
            print("Invalid choice: %s" % usr_input)

    def prompt_user_simple_datatype(self, name, datatype):
        prompt = "[%s] %s: " % (datatype_to_str(datatype), name)
        if datatype in boolean_value_types:
            usr_input = self.select(["True", "False"], prompt)
            if usr_input == "True":
                value = True
            else:
                value = False
        elif datatype in int_value_types + long_value_types:
            usr_input = self.read_input(prompt)
            value = str_to_int(usr_input)
        elif datatype in string_value_types:
            value = self.read_input(prompt)

        return value

    def forge_dataset_metric(self, payload, metric):
        dataset = initDatasetMetric(payload, metric.name, metric.alias,
                                    metric.dataset_value.columns,
                                    metric.dataset_value.types)

        new_row = True
        while new_row:
            row = dataset.rows.add()
            for (col, datatype) in zip(metric.dataset_value.columns, metric.dataset_value.types):
                name = "%s/%s" % (metric.name, col)
                value = self.prompt_user_simple_datatype(name, datatype)
                element = row.elements.add()
                add_value_to_element(element, value, datatype)
            new_row = self.query_yes_no("new row ?")

    def forge_payload_from_metric(self, payload, metric):
        """Add a user modified version of metric to payload"""
        simple_datatypes = int_value_types + long_value_types
        simple_datatypes += boolean_value_types
        if metric.datatype in simple_datatypes:
            value = self.prompt_user_simple_datatype(metric.name,
                                                     metric.datatype)
            addMetric(payload, metric.name, metric.alias, metric.datatype,
                      value)
        elif metric.datatype == MetricDataType.DataSet:
            self.forge_dataset_metric(payload, metric)
        else:
            print("not implemented")

    @cmd2.with_argparser(parser_send)
    def do_send(self, args):
        """Forge a payload to send for a particular EoN or device"""
        sp_dev = get_dev_from_sparkplug_id(args.sparkplug_id)

        if sp_dev is None:
            print("Error: invalid sparkplug_id: %s" % (args.sparkplug_id))
            return

        topic = SparkplugTopic.create(sp_dev.birth_topic.group_id,
                                      args.cmd_type,
                                      sp_dev.birth_topic.edge_node_id,
                                      sp_dev.birth_topic.device_id)
        payload = sparkplug_b_pb2.Payload()
        new_metric = True
        while new_metric:
            metric = self.choose_metric(sp_dev)
            self.forge_payload_from_metric(payload, metric)
            new_metric = self.query_yes_no("new metric ?")

        byte_array = bytearray(payload.SerializeToString())
        mqtt_if = MQTTInterface()
        mqtt_if.publish(str(topic), byte_array, 0, False)

    @staticmethod
    def logger_list(args):
        SPLogger.list()

    @staticmethod
    def logger_stop(args):
        SPLogger.stop(args.logger_id)

    @staticmethod
    def logger_spid(args):
        sparkplug_id = SparkplugId.create_from_str(args.sparkplug_id)
        if sparkplug_id is None:
            print("Error: invalid sparkplug_id: %s" % (args.sparkplug_id))
            return

        topic = sparkplug_id.get_topic("+")
        logger = SPLogger(str(topic))

    parser_logger = cmd2.Cmd2ArgumentParser()
    subparser_logger = parser_logger.add_subparsers(help='logger subcommands')
    parser_logger_spid = subparser_logger.add_parser('spid', help='Start logging messages exchanged '
                                                     'with a sparkplug_id')
    parser_logger_spid.add_argument('sparkplug_id',
                                    help='Id of EoN or device as returned by command "list"')
    parser_logger_spid.set_defaults(func=logger_spid.__func__)

    parser_logger_list = subparser_logger.add_parser('list', help='List active loggers and id to stop them')
    parser_logger_list.set_defaults(func=logger_list.__func__)

    parser_logger_stop = subparser_logger.add_parser('stop', help='Stop an active logger')
    parser_logger_stop.add_argument('logger_id',
                                    help='Logger id to stop as returned by command "logger list"')
    parser_logger_stop.set_defaults(func=logger_stop.__func__)

    @cmd2.with_argparser(parser_logger)
    def do_logger(self, args):
        """Log payloads related to a topic or a sparkplug id"""
        args.func(args)


######################################################################
# Main Application
######################################################################
def main():
    parser = argparse.ArgumentParser(description="View and manipulate sparkplug payload")
    parser.add_argument('--host',
                        help='MQTT broker address', default='localhost')
    parser.add_argument('--port',
                        help='MQTT broker port', default=1883, type=int)
    args = parser.parse_args()

    mqtt_if = MQTTInterface()
    mqtt_if.set_server(args.host, args.port)
    mqtt_if.start()
    time.sleep(.1)

    spshell = SPShell()
    ret = spshell.cmdloop("Sparkplug Shell")
    MQTTInterface().join()
    SPLogger.stop_all()
    sys.exit(ret)
######################################################################


if __name__ == "__main__":
    main()
