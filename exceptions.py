"""Exceptions."""

from logger_api import api_logger

logger = api_logger("Bakalari API").get


class APIException(Exception):
    """General API exception."""

    def __init__(self, message, *args, **kwargs):
        super().__init__(message)
        logger.error(f"({self.__class__.__name__}): {self}")
        
class Ex(APIException):
    """Root exception class."""

    class InvalidCredentials(APIException):
        """Invalid credentials."""

    class InvalidResponse(APIException):
        """Invalid response from server."""

    class TimeoutException(APIException):
        """Server timeout."""

    class BadRequestException(APIException):
        """Bad request."""

    class InvalidHTTPMethod(APIException):
        """Invalid HTTP method."""

    class InvalidLogin(APIException):
        """Invalid login (username/password)."""

    class AccessTokenExpired(APIException):
        """Access token expired. Refresh with refresh token."""

    class RefreshTokenExpired(APIException):
        """Refresh token expired. You have to login with username and password."""

    class TokensExpired(APIException):
        """Access token and refresh token expired."""
