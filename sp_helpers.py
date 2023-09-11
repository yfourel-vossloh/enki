"""Variables and helper functions to handle Sparkplug."""

import ctypes
from typing import Optional
from enum import Enum

from sparkplug_b import MetricDataType


# Sparkplug namespace used
SP_NAMESPACE = "spBv1.0"

class MsgType(Enum):
    """High level message type with no differences between EoN and devices."""
    BIRTH = 1
    DEATH = 2
    DATA = 3
    CMD = 4
    STATE = 5

# Metric datatypes as strings
_DATATYPES_STR = {
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

def ctype_converter(ctype):
    """Returns a converter that transforms a value into a C-style variable value."""
    return lambda value: ctype(value).value

def string_value_converter(string):
    """Adds quotes and length to a string value."""
    return f"\"{str(string)}\" ({len(str(string))} bytes)"

#Functions to convert a metric/property value to the appropriate type
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
    MetricDataType.String: string_value_converter,
    MetricDataType.DateTime: ctype_converter(ctypes.c_uint64),
    MetricDataType.Text: string_value_converter,
    MetricDataType.UUID: string_value_converter,
    MetricDataType.Bytes: bytearray,
    MetricDataType.File: bytearray
}

#
# Functions to convert a value to the appropriate type
# for storage in a metric/property.
#
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

# Metric/property attributes to store a value according to its datatype
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

def get_msg_type_str(msg_type: MsgType, eon: bool) -> str:
    """
    Returns the message type part of a Sparkplug topic.

    :param msg_type: The high level message type without distinction between EoN
    and devices.
    :param eon: True if the message is from/to an EoN. False for devices.
    """
    if msg_type == MsgType.BIRTH:
        return "NBIRTH" if eon else "DBIRTH"
    if msg_type == MsgType.DEATH:
        return "NDEATH" if eon else "DDEATH"
    if msg_type == MsgType.DATA:
        return "NDATA" if eon else "DDATA"
    if msg_type == MsgType.CMD:
        return "NCMD" if eon else "DCMD"
    if msg_type == MsgType.STATE:
        return "STATE"
    return "Unknown"

def msg_type_from_str(type_str: str) -> Optional[MsgType]:
    """
    Converts the msg type part of a topic to a high level
    MsgType without distinction between the Eon or device.
    """
    if type_str in ("NBIRTH", "DBIRTH"):
        return MsgType.BIRTH
    if type_str in ("NDEATH", "DDEATH"):
        return MsgType.DEATH
    if type_str in ("NDATA", "DDATA"):
        return MsgType.DATA
    if type_str in ("NCMD", "DCMD"):
        return MsgType.CMD
    if type_str == "STATE":
        return MsgType.STATE
    return None

def get_dev_id_str(dev_id: Optional[str]) -> str:
    """
    Returns the device Id part of a topic/device handle
    or an empty string if there dev_id is None.
    """
    if dev_id:
        return f"/{dev_id}"
    return ""

def datatype_to_str(datatype) -> str:
    """Converts a Sparkplug datatype to a string."""
    return _DATATYPES_STR.get(datatype, "Unknown")

def get_typed_value(datatype, container):
    """Returns the value with the given datatype from a container."""
    if datatype in _DTYPE_TO_VAR:
        value = getattr(container, _DTYPE_TO_VAR[datatype])
        if datatype in _FROM_DTYPE_CONVERTERS:
            converter = _FROM_DTYPE_CONVERTERS[datatype]
            value = converter(value)
        return value
    return None

def set_typed_value(datatype, container, value):
    """Sets the appropriate container attribute according to the datatype."""
    if datatype in _DTYPE_TO_VAR:
        if datatype in _TO_DTYPES_CONVERTERS:
            value = _TO_DTYPES_CONVERTERS[datatype](value)
        setattr(container, _DTYPE_TO_VAR[datatype], value)

def is_same_metric(metric_a, metric_b):
    """Helper function to compare metrics.

    The comparison is made on the name if present, or on the alias.
    """
    return (((metric_a.name and metric_b.name and metric_a.name == metric_b.name)
             or (not metric_a.name and not metric_b.name and metric_a.alias == metric_b.alias))
            and metric_a.datatype == metric_b.datatype)
