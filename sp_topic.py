#!/usr/bin/env python
"""Sparkplug Topic management tools."""

SP_NAMESPACE = "spBv1.0"


class SparkplugTopic:
    """Handles a Sparkplug Topic."""

    @staticmethod
    def create(group_id, cmd, eon_id, dev_id=None):
        """Create Sparkplug Topic from parameters."""
        topic_str = "%s/%s/%s/%s" % (SP_NAMESPACE, group_id, cmd, eon_id)
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
        """True for node birth topics."""
        return self.message_type == "NBIRTH"

    def is_dbirth(self):
        """True for device birth topics."""
        return self.message_type == "DBIRTH"

    def is_ndata(self):
        """True for node data topics."""
        return self.message_type == "NDATA"

    def is_ddata(self):
        """True for device data topics."""
        return self.message_type == "DDATA"

    def is_ddeath(self):
        """True for device death topics."""
        return self.message_type == "DDEATH"

    def eon_id(self):
        """Return Edge of Network Node ID."""
        return self.edge_node_id

    def __repr__(self):
        return "%s(\"%s\")" % (type(self).__name__, self.topic)

    def __str__(self):
        return "%s" % (self.topic)
