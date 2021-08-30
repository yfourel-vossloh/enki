"""Sparkplug Nodes and Devices Management."""


class SparkplugNetwork():
    """Manage a fleet of Sparkplug Nodes and devices."""
    __instance = None

    def __new__(cls):
        if SparkplugNetwork.__instance is None:
            SparkplugNetwork.__instance = object.__new__(cls)
        return SparkplugNetwork.__instance

    def __init__(self):
        if "eon_nodes" not in self.__dict__:
            self.eon_nodes = []

    def __str__(self):
        display = ""
        for eon in self.eon_nodes:
            display += "%s" % (eon)
        return display

    def add_eon(self, eon):
        """Add an Edge of Network Node."""
        # Remove any existing EoN
        old_eon = self.find_eon(eon.birth_topic)
        if old_eon is not None:
            self.eon_nodes.remove(old_eon)
        self.eon_nodes.append(eon)

    def find_eon(self, topic):
        """Find Edge of Network node from topic."""
        for eon in self.eon_nodes:
            if (eon.birth_topic.namespace == topic.namespace and
                    eon.birth_topic.group_id == topic.group_id and
                    eon.birth_topic.edge_node_id == topic.edge_node_id):
                return eon
        return None

    def find_dev(self, topic):
        """Find Device from topic."""
        assert topic.device_id is not None, \
                "Invalid device topic: %s" % (topic)
        eon = self.find_eon(topic)
        if eon is None:
            return None
        for dev in eon.devices:
            if dev.birth_topic.device_id == topic.device_id:
                return dev
        return None
