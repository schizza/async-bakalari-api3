"""Exceptions."""

from .logger_api import api_logger

logger = api_logger("Bakalari API").get()


class APIException(Exception):
    """General API exception."""

    def __init__(self, message, *args, **kwargs):
        """General API Exception."""

        super().__init__(message)
        logger.error("(%s): %s", self.__class__.__name__, self)


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

    class RefreshTokenRedeemd(APIException):
        """Refresh token already redeemd. Use access token."""

    class InvalidRefreshToken(APIException):
        """Refresh token is invalid."""

    class TokensExpired(APIException):
        """Access token and refresh token expired."""

    class BadEndpointUrl(APIException):
        """Bad endpoint url."""

    class TokenMissing(APIException):
        """Either Access token or Refresh token is missing."""

    class InvalidToken(APIException):
        """Specified token is invalid."""

    class CacheError(APIException):
        """Auto-cache is enabled, but no filename is provided."""
