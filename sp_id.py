"""Sparkplug ID management."""

from typing import Optional

import sp_helpers

class SPId:
    """Handles the ID of a Sparkplug EoN/device."""

    def __init__(self, group_id: str, eon_id: str, dev_id: Optional[str] = None):
        self.group_id = group_id
        self.eon_id = eon_id
        self.dev_id = dev_id

    @staticmethod
    def from_str(topic: str) -> Optional[str]:
        """Create a SPId object from a topic string"""
        tokens = topic.split("/")
        if (len(tokens) == 4 or len(tokens) == 5) and tokens[0] == sp_helpers.SP_NAMESPACE:
            del tokens[2]
            return SPId(*tokens[1:])
        return None

    def __str__(self) -> str:
        """Returns a string representation of the Id."""
        return f"{self.group_id}/{self.eon_id}{sp_helpers.get_dev_id_str(self.dev_id)}"

    def __eq__(self, other) -> bool:
        return ((self.group_id == other.group_id)
                and (self.eon_id == other.eon_id)
                and (self.dev_id == other.dev_id))

    def is_eon(self) -> bool:
        """Returns True if this Id belongs to an EoN."""
        return self.dev_id is None

    def is_dev(self) -> bool:
        """Returns True if this Id belongs to a Device"""
        return not self.is_eon()
