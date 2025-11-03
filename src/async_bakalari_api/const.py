"""Constants."""

from enum import Enum
from typing import Any

from strenum import StrEnum

from .logger_api import api_logger

log = api_logger("Bakalari API").get()

REQUEST_TIMEOUT: int = 10


class Errors(StrEnum):
    """Returned errors."""

    INVALID_METHOD = "ID2084"
    INVALID_LOGIN = "ID2024"
    MISSING_LOGIN = "ID2059"
    ACCESS_TOKEN_EXPIRED = "ID2019"
    INVALID_TOKEN = "ID2004"
    REFRESH_TOKEN_EXPIRED = "ID2012"
    INVALID_REFRESH_TOKEN = "ID2003"
    REFRESH_TOKEN_REDEEMD = "ID2012"


class EndPoint(Enum):
    """List of endpoints."""

    VERSION = {"endpoint": "/api", "method": "get"}
    LOGIN = {"endpoint": "/api/login", "method": "post"}
    SCHOOL_LIST = {
        "endpoint": "https://sluzby.bakalari.cz/api/v1/municipality",
        "method": "get",
    }
    KOMENS_UNREAD = {
        "endpoint": "/api/3/komens/messages/received",
        "method": "post",
    }
    KOMENS_UNREAD_COUNT = {
        "endpoint": "/api/3/komens/messages/received/unread",
        "method": "get",
    }
    KOMENS_ATTACHMENT = {
        "endpoint": "/api/3/komens/attachment",
        "method": "get",
    }

    MARKS = {
        "endpoint": "/api/3/marks",
        "method": "get",
    }
    TIMETABLE_ACTUAL = {
        "endpoint": "/api/3/timetable/actual",
        "method": "get",
    }
    TIMETABLE_PERMANENT = {
        "endpoint": "/api/3/timetable/permanent",
        "method": "get",
    }

    def get(self, key: str) -> Any:
        """Get key value."""
        if not (ret := self.value.get(key)):
            log.error(f"Requested key ({key}) is not valid. Check for spelling.")
            return False
        return ret

    @property
    def endpoint(self) -> str:
        """Endpoint property."""

        return self.get("endpoint")

    @property
    def method(self) -> str:
        """Method property."""
        return self.get("method")


class Token(StrEnum):
    """Token."""

    USER_ID = "bak:UserId"
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    USERNAME = "username"
