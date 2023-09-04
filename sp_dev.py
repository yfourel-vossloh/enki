"""Manages Edge Of Netork or Devices."""

import ctypes
from sparkplug_b import MetricDataType

def ctype_converter(ctype):
    return lambda value: ctype(value).value

_FROM_DTYPE_CONVERTERS = {
    MetricDataType.Int8: ctype_converter(ctypes.c_int8),
    MetricDataType.Int16: ctype_converter(ctypes.c_int16),
    MetricDataType.Int32: ctype_converter(ctypes.c_int32),
    MetricDataType.Int64: ctype_converter(ctypes.c_int64),
    MetricDataType.UInt8: ctype_converter(ctypes.c_uint8),
    MetricDataType.UInt16: ctype_converter(ctypes.c_uint16),
    MetricDataType.UInt32: ctype_converter(ctypes.c_uint32),
    MetricDataType.UInt64: ctype_converter(ctypes.c_uint64),
    MetricDataType.Float: ctype_converter(ctypes.c_float),
    MetricDataType.Double: ctype_converter(ctypes.c_double),
    MetricDataType.Boolean: bool,
    MetricDataType.String: str,
    MetricDataType.DateTime: ctype_converter(ctypes.c_uint64),
    MetricDataType.Text: str,
    MetricDataType.UUID: str,
    MetricDataType.Bytes: bytearray,
    MetricDataType.File: bytearray
}

_TO_DTYPES_CONVERTERS = {
    MetricDataType.Int8: ctype_converter(ctypes.c_uint32),
    MetricDataType.Int16: ctype_converter(ctypes.c_uint32),
    MetricDataType.Int32: ctype_converter(ctypes.c_uint32),
    MetricDataType.Int64: ctype_converter(ctypes.c_uint64),
    MetricDataType.UInt8: ctype_converter(ctypes.c_uint32),
    MetricDataType.UInt16: ctype_converter(ctypes.c_uint32),
    MetricDataType.UInt32: ctype_converter(ctypes.c_uint32),
    MetricDataType.UInt64: ctype_converter(ctypes.c_uint64),
    MetricDataType.Float: ctype_converter(ctypes.c_float),
    MetricDataType.Double: ctype_converter(ctypes.c_double),
    MetricDataType.Boolean: bool,
    MetricDataType.String: str,
    MetricDataType.DateTime: ctype_converter(ctypes.c_uint64),
    MetricDataType.Text: str,
    MetricDataType.UUID: str,
    MetricDataType.Bytes: bytearray,
    MetricDataType.File: bytearray
}

_DTYPE_TO_VAR = {
    MetricDataType.Int8: "int_value",
    MetricDataType.Int16: "int_value",
    MetricDataType.Int32: "int_value",
    MetricDataType.Int64: "long_value",
    MetricDataType.UInt8: "int_value",
    MetricDataType.UInt16: "int_value",
    MetricDataType.UInt32: "long_value",
    MetricDataType.UInt64: "long_value",
    MetricDataType.Float: "float_value",
    MetricDataType.Double: "double_value",
    MetricDataType.Boolean: "boolean_value",
    MetricDataType.String: "string_value",
    MetricDataType.DateTime: "long_value",
    MetricDataType.Text: "string_value",
    MetricDataType.UUID: "string_value",
    MetricDataType.Bytes: "bytes_value",
    MetricDataType.File: "bytes_value",
    MetricDataType.Template: "template_value"
}

DATATYPES_STR = {
    MetricDataType.Int8: "Int8",
    MetricDataType.Int16: "Int16",
    MetricDataType.Int32: "Int32",
    MetricDataType.Int64: "Int64",
    MetricDataType.UInt8: "UInt8",
    MetricDataType.UInt16: "UInt16",
    MetricDataType.UInt32: "Uint32",
    MetricDataType.UInt64: "Uint64",
    MetricDataType.Float: "Float",
    MetricDataType.Double: "Double",
    MetricDataType.Boolean: "Boolean",
    MetricDataType.String: "String",
    MetricDataType.DateTime: "DateTime",
    MetricDataType.Text: "Text",
    MetricDataType.UUID: "UUID",
    MetricDataType.Bytes: "Bytes",
    MetricDataType.File: "File",
    MetricDataType.Template: "Template",
    MetricDataType.DataSet: "DataSet"
}

def get_typed_value(datatype, container):
    if datatype in _DTYPE_TO_VAR:
        value = getattr(container, _DTYPE_TO_VAR[datatype])
        if datatype in _FROM_DTYPE_CONVERTERS:
            converter = _FROM_DTYPE_CONVERTERS[datatype]
            value = converter(value)
        return value
    return None

def get_bytearray_str(bytes_array):
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
    
def get_typed_value_str(datatype, container):
    if datatype == MetricDataType.Bytes:
        return get_bytearray_str(container.bytes_value)
    return str(get_typed_value(datatype, container))

def get_property_value_str(prop):
    prop_type = DATATYPES_STR.get(prop.type, "Unknown")
    prop_value = get_typed_value_str(prop.type, prop)
    return f"\t\t\ttype: {prop_type}\n\t\t\tvalue: {prop_value}"
    
def get_common_info_str(metric):
    datatype_str = DATATYPES_STR.get(metric.datatype, "Unknown")
    res = "\ttimestamp: {}\n\tdatatype: {}".format(metric.timestamp,
                                                   datatype_str)
    if len(metric.properties.keys):
        res = res + "\n\tproperties:"
        props = metric.properties
        for idx in range(len(props.keys)):
            prop_name = props.keys[idx]
            prop_value = get_property_value_str(props.values[idx])
            res = res + f"\n\t\t{prop_name}:\n{prop_value}"
    else:
        res = res + "\n\tproperties: None"
    return res

def is_same_metric(metric_a, metric_b):
    """Helper function to compare metrics
    
    The comparison is made on the name if present, or on the alias.
    """
    return (((metric_a.name and metric_b.name and metric_a.name == metric_b.name)
             or (not metric_a.name and not metric_b.name and metric_a.alias == metric_b.alias))
            and metric_a.datatype == metric_b.datatype)

class SPDev:
    """Base class for Edge of Network Nodes or Devices"""
    def __init__(self, birth_topic, metrics):
        self.birth_topic = birth_topic
        self.edge_node_id = birth_topic.edge_node_id
        self.metrics = list(metrics)

    def __repr__(self):
        return "%s(\"%s\")" % (type(self).__name__, self.birth_topic)

    def add_metric(self, new_metric):
        """Add a metric to a device

        The alias of the added metric must not already exists in the metrics
        attached to the Device
        """
        for metric in self.metrics:
            assert metric.alias == new_metric.alias, \
                    "Alias %d already exists in device" % (metric.alias)

        self.metrics.append(new_metric)

    def update_metric(self, new_metric):
        """Update a device metric
        
        The registered metric's value is updated with a new value received from
        the device.
        """
        for idx, metric in enumerate(self.metrics):
            if is_same_metric(metric, new_metric):
                self.metrics[idx] = new_metric

    def get_metric(self, name, alias=None):
        """Get metric object from its name or alias"""
        for metric in self.metrics:
            if metric.name == name:
                return metric
            elif alias is not None and metric.alias == alias:
                return metric
        return None

    def get_cmd_topic(self):
        """Return xCMD topic for SPDev's."""
        if self.birth_topic.is_nbirth():
            cmd = "NCMD"
            device = ""
        else:
            cmd = "DCMD"
            device = "/%s" % (self.birth_topic.device_id)
        topic = "%s/%s/%s/%s%s" % (self.birth_topic.namespace,
                                   self.birth_topic.group_id,
                                   cmd,
                                   self.birth_topic.edge_node_id,
                                   device)
        return topic

    def get_metric_str(self, req_metric):
        """Return string describing metric if it is known to Device"""
        for metric in self.metrics:
            if is_same_metric(metric, req_metric):
                return "{}[{}]:\n{}\n\tvalue: {}\n".format(req_metric.name,
                                                           req_metric.alias,
                                                           get_common_info_str(req_metric),
                                                           get_typed_value_str(req_metric.datatype, req_metric))
        return None

    def print_metric(self, metric):
        """Print received metric using list of known metrics"""
        metric_str = self.get_metric_str(metric)
        if metric_str is None:
            print("Unknown metric %d for Edge Node %s" % (metric.alias,
                                                          self.edge_node_id))
        else:
            print(metric_str)

    def get_short_handle(self):
        """Returns a string representing the device."""
        return "%s/%s/%s" % (self.birth_topic.group_id,
                             self.edge_node_id,
                             self.birth_topic.device_id)


class EdgeNode(SPDev):
    """Edge of Network Node."""
    def __init__(self, birth_topic, metrics):
        super().__init__(birth_topic, metrics)
        self.devices = []

    def add_dev(self, device):
        """Adds a device to EdgeNode."""
        if device in self.devices:
            print("Device %s already exists" % dev.get_short_handle())
        else:
            self.devices.append(device)

    def remove_dev(self, device):
        """Removes a device from EdgeNode."""
        self.devices.remove(device)
