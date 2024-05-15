"""Constants."""

from enum import Enum
from typing import Any, Final

from strenum import StrEnum

from .logger_api import api_logger

log = api_logger("Bakalari API").get()

REQUEST_TIMEOUT: int = 10


class Errors(StrEnum):
    """Returned errors."""

    INVALID_METHOD: str = "ID2084"
    INVALID_LOGIN: str = "ID2024"
    MISSING_LOGIN: str = "ID2059"
    ACCESS_TOKEN_EXPIRED: str = "ID2019"
    INVALID_TOKEN: str = "ID2004"
    REFRESH_TOKEN_EXPIRED: str = "ID2012"
    INVALID_REFRESH_TOKEN: str = "ID2003"
    REFRESH_TOKEN_REDEEMD: str = "ID2012"


class EndPoint(Enum):
    """List of endpoints."""

    VERSION: Final = {"endpoint": "/api", "method": "get"}
    LOGIN: Final = {"endpoint": "/api/login", "method": "post"}
    SCHOOL_LIST: Final = {
        "endpoint": "https://sluzby.bakalari.cz/api/v1/municipality",
        "method": "get",
    }
    KOMENS_UNREAD: Final = {
        "endpoint": "/api/3/komens/messages/received",
        "method": "post",
    }
    KOMENS_UNREAD_COUNT: Final = {
        "endpoint": "/api/3/komens/messages/received/unread",
        "method": "get",
    }
    KOMENS_ATTACHMENT = {
        "endpoint": "/api/3/komens/attachment",
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

    USER_ID: str = "bak:UserId"
    ACCESS_TOKEN: str = "access_token"
    REFRESH_TOKEN: str = "refresh_token"
    USERNAME: str = "username"
