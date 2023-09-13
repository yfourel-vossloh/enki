"""Protocol that defines how to interact with the User Interface."""
from typing import Protocol, Optional
from sp_dev import SPDev


class UI(Protocol):
    """
    Python protocol class for an User Interface.
    """

    def on_broker_connected(self) -> None:
        """Called when the connection to the broker is established."""

    def on_broker_disconnected(self) -> None:
        """Called when the connection to the broker is lost."""

    def on_device_added(self, sp_dev: SPDev) -> None:
        """Called when a device is added."""

    def on_device_removed(self, sp_dev: SPDev) -> None:
        """Called when a device is removed."""

    def on_metric_updated(self, sp_dev: SPDev, metric) -> None:
        """Called when a metric is updated."""

    def run(self) -> Optional[int]:
        """
        Starts the UI loop.
        Should block until exit.
        May return an exit code.
        """


class UIStub:
    """UI Stub class that does nothing."""
    def __init__(self):
        """Does nothing."""

    def on_broker_connected(self) -> None:
        """Does nothing."""

    def on_broker_disconnected(self) -> None:
        """Does nothing."""

    def on_device_added(self, sp_dev: SPDev) -> None:
        """Does nothing."""

    def on_device_removed(self, sp_dev: SPDev) -> None:
        """Does nothing."""

    def on_metric_updated(self, sp_dev: SPDev, metric) -> None:
        """Does nothing."""

    def run(self) -> Optional[int]:
        """Does nothing."""
        return 0
