#!/usr/bin/env python
"""Sparkplug Topic management tools."""

from typing import Optional
import sp_helpers
from sp_helpers import MsgType
from sp_id import SPId


class SPTopic:
    """Handles a Sparkplug Topic."""

    @staticmethod
    def from_str(topic: str) -> Optional[str]:
        """Create Sparkplug Topic from a string"""
        tokens = topic.split("/")
        sp_id = SPId.from_str(topic)
        msg_type: Optional[MsgType] = sp_helpers.msg_type_from_str(tokens[2])
        if sp_id and msg_type:
            return SPTopic(sp_id, msg_type)
        return None

    def __init__(self,
                 sp_id: SPId,
                 msg_type: MsgType):
        self.sp_id = sp_id
        self.msg_type = msg_type

    def get_id(self) -> SPId:
        """Returns the Sparplug Id."""
        return self.sp_id

    def get_msg_type(self) -> MsgType:
        """Returns the message type."""
        return self.msg_type

    def __repr__(self) -> str:
        return f"{type(self).__name__}(\"{str(self)}\")"

    def __str__(self) -> str:
        topic = sp_helpers.SP_NAMESPACE
        topic += "/" + self.sp_id.group_id
        topic += "/" + sp_helpers.get_msg_type_str(self.msg_type, self.sp_id.is_eon())
        topic += "/" + self.sp_id.eon_id
        topic += sp_helpers.get_dev_id_str(self.sp_id.dev_id)
        return topic
