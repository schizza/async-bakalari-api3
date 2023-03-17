"""Constants."""

from typing import Final
from strenum import StrEnum

REQUEST_TIMEOUT: int = 10


class Errors(StrEnum):
    """Returned errors."""

    INVALID_METHOD: str = "ID2084"
    INVALID_LOGIN: str = "ID2024"
    MISSING_LOGIN: str = "ID2059"
    ACCESS_TOKEN_EXPIRED: str = "ID2019"


class EndPoint(StrEnum):
    """List of endpoins."""

    VERSION: Final = "/api"
    LOGIN: Final = "/api/login"
    KOMENS_UNREAD: Final = "/api/3/komens/messages/received"
    
class Token(StrEnum):
    """Token."""
    
    USER_ID: str = "bak:UserId"
    ACCESS_TOKEN: str = "access_token"
    REFRESH_TOKEN: str = "refresh_token"
    
    
