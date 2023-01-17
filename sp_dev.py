"""Manages Edge Of Netork or Devices."""

from sparkplug_b import MetricDataType

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
        self.metrics = metrics

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
        for metric in self.metrics:
            if is_same_metric(metric, new_metric):
                metric.timestamp = new_metric.timestamp
                if metric.datatype == MetricDataType.Int8:
                    metric.int_value = new_metric.int_value
                elif metric.datatype == MetricDataType.Int16:
                    metric.int_value = new_metric.int_value
                elif metric.datatype == MetricDataType.Int32:
                    metric.int_value = new_metric.int_value
                elif metric.datatype == MetricDataType.Int64:
                    metric.long_value = new_metric.long_value
                elif metric.datatype == MetricDataType.UInt8:
                    metric.int_value = new_metric.int_value
                elif metric.datatype == MetricDataType.UInt16:
                    metric.int_value = new_metric.int_value
                elif metric.datatype == MetricDataType.UInt32:
                    metric.long_value = new_metric.long_value
                elif metric.datatype == MetricDataType.UInt64:
                    metric.long_value = new_metric.long_value
                elif metric.datatype == MetricDataType.Float:
                    metric.float_value = new_metric.float_value
                elif metric.datatype == MetricDataType.Double:
                    metric.double_value = new_metric.double_value
                elif metric.datatype == MetricDataType.Boolean:
                    metric.boolean_value = new_metric.boolean_value
                elif metric.datatype == MetricDataType.String:
                    metric.string_value = new_metric.string_value
                elif metric.datatype == MetricDataType.DateTime:
                    metric.long_value = new_metric.long_value
                elif metric.datatype == MetricDataType.Text:
                    metric.string_value = new_metric.string_value
                break
                               
    def get_metric(self, name):
        """Get metric object from its name"""
        for metric in self.metrics:
            if metric.name == name:
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

    @classmethod
    def get_metric_val_str(cls, metric):
        """Use google's protobuf backend to print metric."""
        return "%s" % (metric)

    def get_metric_str(self, req_metric):
        """Return string describing metric if it is known to Device"""
        for metric in self.metrics:
            if is_same_metric(metric, req_metric):
                return "%s: %s" % (metric.name, self.get_metric_val_str(req_metric))
        return None

    def print_metric(self, metric):
        """Print received metric using list of known metrics"""
        metric_str = self.get_metric_str(metric)
        if metric_str is None:
            print("Unknown metric %d for Edge Node %s" % (metric.alias,
                                                          self.edge_node_id))
        else:
            print(metric_str)


class EdgeNode(SPDev):
    """Edge of Network Node."""
    def __init__(self, birth_topic, metrics):
        super().__init__(birth_topic, metrics)
        self.devices = []

    def add_dev(self, device):
        """Adds a device to EdgeNode."""
        # TODO: check if device does not already exist.
        self.devices.append(device)
