"""Datastructure."""
from __future__ import annotations
from typing import Any
import json
from dataclasses import dataclass

from const import Token


@dataclass
class Credentials:
    """Credentials holder."""

    username: str = None
    access_token: str = None
    refresh_token: str = None
    user_id: str = None

    @classmethod
    def get(cls, data: dict[str, Any]) -> Credentials:
        """ "Return class object."""
        return cls(
            user_id=data[Token.USER_ID],
            access_token=data[Token.ACCESS_TOKEN],
            refresh_token=data[Token.REFRESH_TOKEN],
        )

    def get_json(self, **kwargs) -> str:
        """Return json object."""

        _json = {}
        _json[Token.USER_ID] = self.user_id
        _json[Token.ACCESS_TOKEN] = self.access_token
        _json[Token.REFRESH_TOKEN] = self.refresh_token
        _json["username"] = self.username

        return json.dumps(_json, **kwargs)
