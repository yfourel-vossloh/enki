"""Manages Logging of Sparkplug Payloads."""
import os
import datetime
import pathlib
import paho.mqtt.client as mqtt
from mqtt_if import MQTTInterface


class SPLogger():
    """Log every Sparkplug Payload from a specified topic.

    A class attributes references all created loggers in order to manage them
    with class methods.
    """
    __loggers = []
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
        self.log_fd = open(self.path, 'w')

    @classmethod
    def list(cls):
        """List active loggers."""
        idx = 0
        for logger in cls.__loggers:
            print("%d) %s" % (idx, logger.subscribed_topic))
            idx += 1

    @classmethod
    def get_by_topic(cls, topic):
        """Return logger attached to a topic."""
        for logger in cls.__loggers:
            if topic == logger.subscribed_topic:
                return logger
        return None

    @classmethod
    def get_all_matching_topic(cls, topic):
        """Get all loggers for which 'topic' matches their subscription."""
        matches = []
        for logger in cls.__loggers:
            if mqtt.topic_matches_sub(logger.subscribed_topic, topic):
                matches.append(logger)
        return matches

    def stop_instance(self):
        """Stop logger."""
        self.log_fd.close()
        mqtt_if = MQTTInterface()
        mqtt_if.unsubscribe(self.subscribed_topic)
        self.__loggers.remove(self)

    @classmethod
    def stop(cls, topic):
        """Stop logger attached to specified topic."""
        logger = cls.get_by_topic(topic)
        if logger is None:
            print("Error: %s is not an active logger" % (topic))
        else:
            logger.stop_instance()

    @classmethod
    def stop_all(cls):
        """Stop all loggers"""
        for logger in cls.__loggers:
            logger.stop_instance()

    def process_payload(self, payload):
        """Method called by mqtt callback when message received on appropriate topic."""
        self.log_fd.write(str(payload))
