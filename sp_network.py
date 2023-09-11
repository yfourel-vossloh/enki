"""Sparkplug Nodes and Devices Management."""

from copy import copy
from typing import Optional

from sp_dev import SPDev, EdgeNode, Device
from sp_id import SPId
from ui import UI, UIStub

class SPNet():
    """Manage a fleet of Sparkplug Nodes and devices."""
    __instance = None

    def __new__(cls):
        if SPNet.__instance is None:
            SPNet.__instance = object.__new__(cls)
        return SPNet.__instance

    def __init__(self):
        if "eon_nodes" not in self.__dict__:
            self.eon_nodes = []
            self.ui: UI = UIStub()

    def set_ui(self, ui: UI) -> None:
        """Sets the user interface object to send events to."""
        if self.ui is not None:
            self.ui = ui

    def __str__(self):
        display = ""
        for eon in self.eon_nodes:
            display += str(eon)
        return display

    def find_handle(self, handle: str) -> Optional[SPDev]:
        """Returns an EoN or Device from its handle."""
        tokens = handle.split("/")
        if len(tokens) == 2 or len(tokens) == 3:
            sp_id = SPId(*tokens)
            if sp_id:
                return self.find_id(sp_id)
        return None

    def find_id(self, sp_id: SPId) -> Optional[SPDev]:
        """Find an EoN or a device from its Id"""
        eon: Optional[EdgeNode] = self.find_eon(sp_id)
        if eon is None or sp_id.is_eon():
            return eon
        return next((dev for dev in eon.devices
                     if dev.get_id() == sp_id), None)

    def find_eon(self, sp_id: SPId) -> Optional[EdgeNode]:
        """Find the EoN from a sparkplug Id while ignoring the device Id part."""
        tmp = copy(sp_id)
        tmp.dev_id = None
        return next((eon for eon in self.eon_nodes
                     if eon.get_id() == tmp), None)

    def add_from_birth(self, sp_id: SPId, metrics) -> None:
        """
        Adds an EoN/Device from a BIRTH message.

        :param sp_id: The ID used in the BIRTH message/
        :param metrics: The metrics in the BIRTH message's payload.
        """
        eon = self.find_eon(sp_id)
        if sp_id.is_eon():
            if eon is not None:
                self.remove_by_dev(eon)
            eon = EdgeNode(sp_id, metrics)
            self.eon_nodes.append(eon)
            self.ui.on_device_added(eon)
        elif eon is not None:
            dev = Device(sp_id, metrics, eon)
            eon.add_dev(dev)
            self.ui.on_device_added(dev)
        else:
            print(f"Device birth ({sp_id}) with unknown EoN")

    def remove_by_dev(self, sp_dev: SPDev) -> None:
        """Removes the given EoN/Device from the fleet."""
        if sp_dev.is_eon():
            self.eon_nodes.remove(sp_dev)
            self.ui.on_device_removed(sp_dev)
        else:
            eon = self.find_eon(sp_dev.get_id())
            if eon:
                eon.devices.remove(sp_dev)
                self.ui.on_device_removed(sp_dev)

    def remove_by_id(self, sp_id: SPId) -> None:
        """Removes the EoN/Device with the given ID from the fleet."""
        sp_dev = self.find_id(sp_id)
        if sp_dev:
            self.remove_by_dev(sp_dev)

    def update_metrics(self, sp_id: SPId, metrics) -> None:
        """Updates the metrics of the device with the given Id."""
        sp_dev: Optional[SPDev] = SPNet().find_id(sp_id)
        if sp_dev is not None:
            for metric in metrics:
                sp_dev.update_metric(metric)
                self.ui.on_metric_updated(sp_dev, metric)
        else:
            print(f"DATA from unknown device {sp_id}")
