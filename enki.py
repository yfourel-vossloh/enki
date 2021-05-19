#!/usr/bin/env python
import sys
sys.path.insert(0, "tahu/client_libraries/python/")

import paho.mqtt.client as mqtt
import sparkplug_b as sparkplug
import time
import random
import string

from sparkplug_b import *

# Application Variables
serverUrl = "localhost"
myGroupId = "Sparkplug B Devices"
myNodeName = "enki"
myUsername = "admin"
myPassword = "changeme"

######################################################################
# The callback for when the client receives a CONNACK response from the server.
######################################################################
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected with result code "+str(rc))
    else:
        print("Failed to connect with result code "+str(rc))
        sys.exit()

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("spBv1.0/" + myGroupId + "/#")
    client.subscribe("spBv1.0/" + myGroupId + "/#")
######################################################################

######################################################################
# The callback for when a PUBLISH message is received from the server.
######################################################################
def on_message(client, userdata, msg):
    print("Message arrived: " + msg.topic)
    tokens = msg.topic.split("/")

    inboundPayload = sparkplug_b_pb2.Payload()
    inboundPayload.ParseFromString(msg.payload)
    for metric in inboundPayload.metrics:
        print( "name: %s" % (metric.name))
        print( "datatype: %s" % (metric.datatype))
        print( "alias: %d" % (metric.alias))

    print("Done publishing")
######################################################################

######################################################################
# Main Application
######################################################################
def main():
    print("Starting main application")

    # Create the node death payload
    deathPayload = sparkplug.getNodeDeathPayload()

    # Start of main program - Set up the MQTT client connection
    client = mqtt.Client(serverUrl + "enki", 1883, 60)
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(myUsername, myPassword)
    deathByteArray = bytearray(deathPayload.SerializeToString())
    client.will_set("spBv1.0/" + myGroupId + "/NDEATH/" + myNodeName, deathByteArray, 0, False)
    client.connect(serverUrl, 1883, 60)

    # Short delay to allow connect callback to occur
    time.sleep(.1)
    client.loop_start()

    while True:

        # Sit and wait for inbound or outbound events
        for _ in range(50):
            time.sleep(.1)
######################################################################

if __name__ == "__main__":
    main()
