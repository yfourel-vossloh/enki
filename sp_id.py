"""Sparkplug ID management."""

import sp_topic

class SparkplugId:
    """Handles Sparkplug ID."""

    def __init__(self, group_id, eon_id, dev_id=None):
        self.group_id = group_id
        self.eon_id = eon_id
        self.dev_id = dev_id

    @staticmethod
    def create_from_topic(topic):
        """Create Instance from MQTT topic"""
        tokens = topic.split("/")
        if len(tokens) == 4:
            sp_id = SparkplugId(tokens[1], tokens[3])
        elif len(tokens) == 5:
            sp_id = SparkplugId(tokens[1], tokens[3], tokens[4])
        else:
            sp_id = None
        return sp_id

    @staticmethod
    def create_from_str(sparkplug_id):
        """Create instance from sparkplug id string (<grpId>/<EonID>[/<devId>])."""
        tokens = sparkplug_id.split("/")
        if len(tokens) == 2:
            sp_id = SparkplugId(tokens[0], tokens[1])
        elif len(tokens) == 3:
            sp_id = SparkplugId(tokens[0], tokens[1], tokens[2])
        else:
            sp_id = None
        return sp_id

    def get_topic(self, msg_type):
        """Return topic for requested message type."""
        if self.dev_id is None:
            topic = "%s/%s/%s/%s" % (sp_topic.SP_NAMESPACE,
                                     self.group_id,
                                     msg_type,
                                     self.eon_id)
        else:
            topic = "%s/%s/%s/%s/%s" % (sp_topic.SP_NAMESPACE,
                                        self.group_id,
                                        msg_type,
                                        self.eon_id,
                                        self.dev_id)
        return topic

    def get_cmd_topic(self):
        """Return xCMD topic for instance."""
        if self.dev_id is None:
            msg_type = "NCMD"
        else:
            msg_type = "DCMD"
        return self.get_topic(msg_type)

    def get_data_topic(self):
        """Return xDATA topic for instance."""
        if self.dev_id is None:
            msg_type = "NDATA"
        else:
            msg_type = "DDATA"
        return self.get_topic(msg_type)

    def get_birth_topic(self):
        """Return xBIRTH topic for instance."""
        if self.dev_id is None:
            msg_type = "NBIRTH"
        else:
            msg_type = "DBIRTH"
        return self.get_topic(msg_type)

    def get_death_topic(self):
        """Return xDEATH topic for instance."""
        if self.dev_id is None:
            msg_type = "NDEATH"
        else:
            msg_type = "DDEATH"
        return self.get_topic(msg_type)

    def __str__(self):
        if self.dev_id is None:
            string = "%s/%s" % (self.group_id, self.eon_id)
        else:
            string = "%s/%s/%s" % (self.group_id, self.eon_id, self.dev_id)
        return string
