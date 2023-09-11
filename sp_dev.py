"""Manages Edge Of Netork or Devices."""

from sp_topic import SPTopic
from sp_id import SPId
from sp_helpers import MsgType
import sp_helpers


class SPDev:
    """Base class for Edge of Network Nodes or Devices"""
    def __init__(self, sp_id: SPId, metrics):
        self.sp_id = sp_id
        self.parent = None
        self.metrics = list(metrics)

    def __repr__(self):
        return f"{type(self).__name__}(\"{str(self.sp_id)}\")"

    def get_id(self) -> SPId:
        """Returns the Sparkplug Id."""
        return self.sp_id

    def is_eon(self) -> bool:
        """Returns True if this is an EoN."""
        return self.sp_id.is_eon()

    def is_dev(self) ->bool:
        """Returns True if this is a device."""
        return self.sp_id.is_dev()

    def add_metric(self, new_metric):
        """Add a metric to a device

        The alias of the added metric must not already exists in the metrics
        attached to the Device
        """
        for metric in self.metrics:
            assert metric.alias == new_metric.alias, \
                f"Alias {metric.alias} already exists in device"
        self.metrics.append(new_metric)

    def update_metric(self, new_metric):
        """Update a device metric.
        
        The registered metric's value is updated with a new value received from
        the device.
        """
        for idx, metric in enumerate(self.metrics):
            if sp_helpers.is_same_metric(metric, new_metric):
                self.metrics[idx] = new_metric
                return
        print(f"No metric {new_metric.name}/{new_metric.alias} "
              f"in {self.get_handle()}")

    def get_metric(self, name, alias=None):
        """Get metric object from its name or alias"""
        for metric in self.metrics:
            if metric.name == name:
                return metric
            if alias is not None and metric.alias == alias:
                return metric
        return None

    def get_msg_topic(self, msg_type: MsgType) -> SPTopic:
        """Return message topic for SPDev's."""
        return SPTopic(self.sp_id, msg_type)

    def get_handle(self):
        """Returns the Sparkplug handle of this device."""
        return str(self.sp_id)


class EdgeNode(SPDev):
    """Edge of Network Node."""
    def __init__(self, sp_id: SPId, metrics):
        super().__init__(sp_id, metrics)
        self.devices: list[SPDev] = []

    def add_dev(self, device: SPDev):
        """Adds a device to EdgeNode."""
        if device in self.devices:
            print(f"Device {device.get_handle()} already exists")
        else:
            self.devices.append(device)

    def remove_dev(self, device: SPDev):
        """Removes a device from EdgeNode."""
        self.devices.remove(device)

class Device(SPDev):
    """Sparkplug device belonging to an EoN."""
    def __init__(self, sp_id: SPId, metrics, eon: SPDev):
        super().__init__(sp_id, metrics)
        self.parent = eon
