"""Enki shell interface."""
import time

import cmd2

import sparkplug_b_pb2
from sparkplug_b import MetricDataType, addMetric, initDatasetMetric

import sp_helpers
from sp_helpers import MsgType
from mqtt_if import MQTTInterface
from sp_dev import SPDev
from sp_network import SPNet


def str_to_int(string):
    """Convert string to int.

    String must be a decimal or hexadecimal value with 0x prefix
    """
    string = string.strip()
    if string[0:2] == '0x':
        return int(string, 16)
    return int(string)

def get_bytearray_str(bytes_array):
    """String representation of a bytearray value."""
    size = len(bytes_array)
    res = f"Bytes array of length {size}"
    if size:
        excerpt = bytes_array[0:10]
        excerpt = "[" + " ".join([f"0x{val:02X}" for val in excerpt])
        if size > 10:
            excerpt += " ..."
        excerpt += "]"
        res = res + " " + excerpt
    return res

def get_dataset_row_str(dataset, row):
    """String representation of a dataset row."""
    return tuple(get_typed_value_str(col_type, row.elements[idx])
                 for (idx, col_type) in enumerate(dataset.types))

def get_dataset_str(dataset):
    """String representation of a dataset value."""
    columns = [f"{col}({sp_helpers.datatype_to_str(col_type)})"
               for (col, col_type)
               in zip(dataset.columns, dataset.types)]
    rows = [get_dataset_row_str(dataset, row) for row in dataset.rows]
    res = f"Dataset {len(dataset.rows)}x{len(dataset.types)}:\n"
    res += f"\t\tColumns: {columns}\n"
    res += f"\t\tRows: {rows}"
    return res

def get_typed_value_str(datatype, container):
    """String representation of a metric/property's value."""
    if hasattr(container, "is_null") and container.is_null:
        return "<Null>"
    if datatype == MetricDataType.Bytes:
        return get_bytearray_str(container.bytes_value)
    if datatype == MetricDataType.DataSet:
        return get_dataset_str(container.dataset_value)
    return str(sp_helpers.get_typed_value(datatype, container))

def get_property_value_str(prop):
    """String representation of a property."""
    prop_type = sp_helpers.datatype_to_str(prop.type)
    prop_value = get_typed_value_str(prop.type, prop)
    res = f"\t\t\ttype: {prop_type}"
    res += f"\n\t\t\tvalue: {prop_value}"
    return res

def get_common_info_str(metric):
    """Common metric information string."""
    datatype_str = sp_helpers.datatype_to_str(metric.datatype)
    res = f"\ttimestamp: {metric.timestamp}"
    res += f"\n\tdatatype: {datatype_str}"
    if len(metric.properties.keys):
        res = res + "\n\tproperties:"
        props = metric.properties
        for idx, prop_name in enumerate(props.keys):
            prop_value = get_property_value_str(props.values[idx])
            res = res + f"\n\t\t{prop_name}:\n{prop_value}"
    else:
        res = res + "\n\tproperties: None"
    return res

def get_metric_str(metric) -> str:
    """Return a string describing metric if it is known to Device"""
    value_str: str = get_typed_value_str(metric.datatype, metric)
    common = get_common_info_str(metric)
    return f"{metric.name}[{metric.alias}]:\n{common}\n\tvalue: {value_str}\n"


@cmd2.with_default_category('Enki')
class SPShell(cmd2.Cmd):
    # pylint: disable=too-many-instance-attributes, too-many-public-methods
    """Enki Shell Interface"""

    def __init__(self, mqtt_if: MQTTInterface):
        cmd2.Cmd.__init__(self, allow_cli_args=False)
        self.mqtt_if = mqtt_if
        self.prompt = "enki> "

    def do_exit(self, *_args):
        """Exits the app."""
        return True

    parser_list = cmd2.Cmd2ArgumentParser()
    parser_list.add_argument('--short', action='store_true', default=False,
                             help="display short path to device instead of full group/eon/device")

    @cmd2.with_argparser(parser_list)
    def do_list(self, args):
        """Show list of birthed Edge of Network Nodes (EoN) and devices"""
        sp_net = SPNet()
        for eon in sp_net.eon_nodes:
            print(f"- {eon.get_handle()}")
            for dev in eon.devices:
                if not args.short:
                    print(f"   * {dev.get_handle()}")
                else:
                    print(f"   * {dev.get_id().dev_id}")

    def build_target_list(self, include_eon, include_dev):
        """Returns a list of potentatial handles for autocompletion purposes."""
        res = []
        sp_net = SPNet()
        for eon in sp_net.eon_nodes:
            eon_id = f"{eon.get_id().group_id}/{eon.get_id().eon_id}"
            if include_eon:
                res.append(eon_id)
            if include_dev:
                for dev in eon.devices:
                    res.append(f"{eon_id}/{dev.get_id().dev_id}")
        return res

    def get_all_targets(self):
        """Returns all known handles."""
        return self.build_target_list(include_eon=True, include_dev=True)

    def get_all_eons(self):
        """Returns all known EoN handles."""
        return self.build_target_list(include_eon=True, include_dev=False)

    def get_all_devices(self):
        """Returns all known device handles."""
        return self.build_target_list(include_eon=False, include_dev=True)

    def help_metrics(self):
        """Prints the help string for the 'print' command."""
        print("metrics <handle>")
        print("  Show metrics available for an Edge of Network Node or a device")
        print("")
        print("handle:")
        print(" Unique string identifying the node or device requested")
        print(" EoN format: <group_id>/<eon_id>")
        print(" Devices format: <group_id>/<eon_id>/<device_id>")

    metrics_parser = cmd2.Cmd2ArgumentParser()
    metrics_parser.add_argument("handle", choices_provider=get_all_targets)

    @cmd2.with_argparser(metrics_parser)
    def do_metrics(self, args):
        """Command to print all metrics of an EoN/device."""
        sp_dev = SPNet().find_handle(args.handle)
        if sp_dev is not None:
            for metric in sp_dev.metrics:
                print(get_metric_str(metric))
        else:
            print(f"Error: Invalid handle: {args.handle}")
            self.help_metrics()

    def get_metrics_from_handle(self, handle):
        """Returns the list of metrics belonging to the given handle."""
        sp_dev = SPNet().find_handle(handle)
        if sp_dev is not None:
            return [metric.name for metric in sp_dev.metrics]
        return []

    def choices_dev_metrics_provider(self, arg_tokens):
        """Autocomplete function for device and metric selection."""
        if "metric_name" in arg_tokens and "handle" in arg_tokens:
            handle = arg_tokens["handle"]
            if isinstance(handle, list) and handle:
                return self.get_metrics_from_handle(handle[0])
        return self.get_all_targets()

    def broker_list_topics(self, _args):
        """Prints the list of subscribed topics."""
        for topic in self.mqtt_if.get_subscribed_topics():
            print(topic)

    def broker_sub(self, args):
        """Subscribe to a topic."""
        self.mqtt_if.subscribe(args.topic)

    def broker_unsub(self, args):
        """Unsubscribe from a topic."""
        self.mqtt_if.unsubscribe(args.topic)

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
    parser_print.add_argument("handle",
                              choices_provider=choices_dev_metrics_provider,
                              help="Handle of a Sparkplug device")
    parser_print.add_argument("metric_name",
                              choices_provider=choices_dev_metrics_provider,
                              help="Metric name")

    @cmd2.with_argparser(parser_print)
    def do_print(self, args):
        """Prints the metric current value for a specific EoN or device."""
        sp_dev = SPNet().find_handle(args.handle)
        if sp_dev is not None:
            metric = sp_dev.get_metric(args.metric_name)
            if metric is not None:
                print(get_metric_str(metric))
            else:
                print(f"No metric '{args.metric_name}' belonging to '{args.handle}'")
        else:
            print(f"Unknown handle '{args.handle}'")

    @cmd2.with_argparser(parser_broker)
    def do_broker(self, args):
        """Manage broker subscriptions"""
        args.func(self, args)

    def choose_metric(self, sp_dev):
        """Ask the user to choose among the metrics of the given device."""
        metrics = []
        for metric in sp_dev.metrics:
            if metric.name == "bdSeq":
                continue
            metrics.append(metric.name)
        metric_name = self.select(metrics, "metric ? ")
        metric = sp_dev.get_metric(metric_name)
        assert metric is not None, "Could not find requested metric"
        return metric

    def query_yes_no(self, prompt):
        """Ask the user to choose between yes or no options."""
        yesses = ["yes", "y", "YES", "Yes"]
        nos = ["no", "n", "NO", "No"]
        while True:
            usr_input = self.read_input(prompt + "[y/n]", choices=yesses + nos,
                                        completion_mode=cmd2.utils.CompletionMode.CUSTOM)
            if usr_input in yesses:
                return True
            if usr_input in nos:
                return False
            print(f"Invalid choice: {usr_input}")

    def prompt_user_simple_datatype(self, name, datatype):
        """Ask the user to give a value for simple datatypes."""
        prompt = f"[{sp_helpers.datatype_to_str(datatype)}] {name}: "
        if datatype in sp_helpers.boolean_value_types:
            usr_input = self.select([(True, "True"),
                                     (False, "False")], prompt)
            value = usr_input
        elif datatype in sp_helpers.int_value_types + sp_helpers.long_value_types:
            usr_input = self.read_input(prompt)
            value = str_to_int(usr_input)
        elif datatype in sp_helpers.string_value_types:
            value = self.read_input(prompt)
        return value

    def forge_dataset_metric(self, payload, metric):
        """Ask the user to fill a dataset."""
        dataset = initDatasetMetric(payload, metric.name, metric.alias,
                                    metric.dataset_value.columns,
                                    metric.dataset_value.types)

        new_row = True
        while new_row:
            row = dataset.rows.add()
            for (col, datatype) in zip(metric.dataset_value.columns, metric.dataset_value.types):
                name = f"{metric.name}/{col}"
                value = self.prompt_user_simple_datatype(name, datatype)
                element = row.elements.add()
                sp_helpers.set_typed_value(datatype, element, value)
            new_row = self.query_yes_no("new row ?")

    def forge_payload_from_metric(self, payload, metric):
        """Add a user modified version of metric to payload"""
        simple_datatypes = sp_helpers.int_value_types + sp_helpers.long_value_types
        simple_datatypes += sp_helpers.boolean_value_types
        simple_datatypes += sp_helpers.string_value_types
        if metric.datatype in simple_datatypes:
            value = self.prompt_user_simple_datatype(metric.name,
                                                     metric.datatype)
            addMetric(payload, metric.name, metric.alias, metric.datatype,
                      value)
        elif metric.datatype == MetricDataType.DataSet:
            self.forge_dataset_metric(payload, metric)
        else:
            print("not implemented")

    parser_send = cmd2.Cmd2ArgumentParser()
    send_msg_choices = ['CMD', 'DATA']
    parser_send.add_argument('msg_type', choices=send_msg_choices,
                             help='Message type the payload is sent with')
    parser_send.add_argument('handle',
                             choices_provider=get_all_targets,
                             help='Id of EoN or device as returned by command "list"')

    @cmd2.with_argparser(parser_send)
    def do_send(self, args):
        """Forge a payload to send for a particular EoN or device."""
        sp_dev = SPNet().find_handle(args.handle)
        if sp_dev is None:
            print(f"Error: invalid handle: {args.handle}")
            return

        msg_type = MsgType.CMD if args.msg_type == "CMD" else MsgType.DATA
        topic = sp_dev.get_msg_topic(msg_type)
        payload = sparkplug_b_pb2.Payload()
        new_metric = True
        while new_metric:
            metric = self.choose_metric(sp_dev)
            self.forge_payload_from_metric(payload, metric)
            new_metric = self.query_yes_no("new metric ?")

        byte_array = bytearray(payload.SerializeToString())
        self.mqtt_if.publish(str(topic), byte_array, 0, False)

    def on_broker_connected(self) -> None:
        """Callback used when the broker connection is established."""
        print(f"Connected to {self.mqtt_if.get_uri()} as '{self.mqtt_if.client_name}'")

    def on_broker_disconnected(self) -> None:
        """Callback used when disconnected from the broker."""
        print(f"Disconnected from {self.mqtt_if.get_uri()}")

    def on_device_added(self, sp_dev: SPDev) -> None:
        """Called when an EoN/Device is added."""
        print(f"New device '{sp_dev.get_handle()}'")

    def on_device_removed(self, sp_dev: SPDev) -> None:
        """Called when an EoN/Device is removed."""
        print(f"Removed device '{sp_dev.get_handle()}'")

    def on_metric_updated(self, sp_dev: SPDev, metric) -> None:
        """Called when a metric is updated on the device."""
        print(f"{sp_dev.get_handle()}: metric update:")
        print(get_metric_str(metric))

    def run(self) -> int:
        """Run this interface."""
        self.mqtt_if.start()
        time.sleep(.1)
        ret = self.cmdloop("Sparkplug Shell")
        return ret
