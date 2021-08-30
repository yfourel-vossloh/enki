"""Manages Edge Of Netork or Devices."""


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
            if metric.alias == req_metric.alias:
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
