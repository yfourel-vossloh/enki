#!/usr/bin/env python
"""Setting up and starting of the Enki application."""
import os
import sys
import argparse
import signal

from sparkplug_b_pb2 import Payload

from mqtt_if import MQTTInterface
from sp_topic import SPTopic
from sp_network import SPNet
from sp_helpers import MsgType
from shell import SPShell


def on_message(_mqtt_client: MQTTInterface, msg) -> None:
    """Callback called by the MQTT interface when a message is received."""
    topic = SPTopic.from_str(msg.topic)
    if not topic:
        return

    payload = Payload()
    payload.ParseFromString(msg.payload)
    if topic.get_msg_type() == MsgType.BIRTH:
        SPNet().add_from_birth(topic.get_id(), payload.metrics)
    elif topic.get_msg_type() == MsgType.DATA:
        SPNet().update_metrics(topic.get_id(), payload.metrics)
    elif topic.get_msg_type() == MsgType.DEATH:
        SPNet().remove_by_id(topic.get_id())


def handle_signal(_sig_num, frame):
    """Used to exit the app on some signals."""
    sys.exit(1)


def main():
    """Main function of the enki application."""
    if os.name != "nt":
        signal.signal(signal.SIGHUP, handle_signal)

    parser = argparse.ArgumentParser(description="View and send Sparkplug payloads")
    parser.add_argument('--host',
                        help='MQTT broker address', default='localhost')
    parser.add_argument('--port',
                        help='MQTT broker port', default=1883, type=int)
    parser.add_argument('--ca-certificate',
                        help='Provide CA Certificate of broker. When this option is provided the '
                        'connection will be made with TLS', default=None, type=str)
    args = parser.parse_args()

    mqtt_if = MQTTInterface()
    mqtt_if.set_server(args.host, args.port, args.ca_certificate)
    mqtt_if.message_callback = on_message

    user_interface = SPShell(mqtt_if)
    mqtt_if.connect_callback = user_interface.on_broker_connected
    mqtt_if.disconnect_callback = user_interface.on_broker_disconnected
    SPNet().set_ui(user_interface)

    ret = user_interface.run()
    MQTTInterface().join()
    if ret is not None:
        sys.exit(ret)
    sys.exit(0)


if __name__ == "__main__":
    main()
