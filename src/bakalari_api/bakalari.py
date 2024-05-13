"""Async Bakalari v3 API connector."""

from __future__ import annotations

import asyncio
import logging
from typing import Self
from urllib import parse

import aiohttp
from aiohttp import hdrs
import aiohttp.web_response
import orjson

from .const import REQUEST_TIMEOUT, EndPoint, Errors
from .datastructure import Credentials, Schools
from .exceptions import Ex
from .logger_api import api_logger

log = api_logger("Bakalari API", loglevel=logging.ERROR).get()


class Bakalari:
    """Root class of Bakalari."""

    session: aiohttp.ClientSession | None = None
    response: None
    response_json: None

    _close_session = False

    def __init__(
        self,
        server: str | None = None,
        auto_cache_credentials: bool = False,
        cache_filename: str | None = None,
    ):
        """Root class of Bakalari.

        Holds credentials, sends requests and perform first login.

        Args:
            server (str): Url of endpoint server.
            auto_cache_credentials (bool, optional): If you want to cache credentials locally to file. Defaults to False.
            cache_filename (str, optional): Cache file name, if `auto_cache_credentials`. Defaults to None.

        """

        self.server = server
        self.credentials = Credentials
        self.new_token = False
        self.auto_cache_credentials = auto_cache_credentials
        self.cache_filename = cache_filename

        if self.auto_cache_credentials and not self.cache_filename:
            raise Ex.CacheError("Auto-cache is enabled, but no filename is provided!")

    async def send_auth_request(self, request_endpoint: EndPoint, **kwargs):
        """Send authorized request with access token or refresh token."""

        request = self.get_request_url(request_endpoint)
        method = hdrs.METH_POST if "post" in request_endpoint.method else hdrs.METH_GET

        access_token_invalid = False
        result = None

        if not self.credentials.access_token and not self.credentials.refresh_token:
            raise Ex.TokenMissing("Access token or Refresh token is missing!")

        while True:
            if self.credentials.access_token and not access_token_invalid:
                log.debug("Trying access token ...")
                try:
                    headers_access_token = {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Authorization": f"Bearer {self.credentials.access_token}",
                    }

                    result = await self._send_request(
                        request, method=method, headers=headers_access_token
                    )

                except Ex.AccessTokenExpired:
                    access_token_invalid = True
                    continue
                except Ex.InvalidToken:
                    access_token_invalid = True
                    continue
                except Exception as ex:
                    raise ex from ex
                else:
                    return result

            if access_token_invalid and self.refresh_access_token:
                log.debug("Trying refresh token ...")
                try:
                    await self.refresh_access_token()
                except Ex.RefreshTokenExpired as ex:
                    log.error("Refresh token expired! Login with username/password")
                    raise ex from ex
                except Exception as ex:
                    raise ex from ex
                access_token_invalid = False

    async def send_unauth_request(
        self, request: EndPoint, headers: dict[str, str] | None = None, **kwargs
    ) -> str | None:
        """Send unauthorized request to endpoint.

        Args:
            request (EndPoint): endpoint
            headers (str): headers for request
            **kwargs (dict): kwargs

        Returns:
            str: JSON response or None

        """
        method = hdrs.METH_GET if "get" in request.method else hdrs.METH_POST

        _request_url = self.get_request_url(request)

        try:
            _request = await self._send_request(
                _request_url, method=method, headers=headers, **kwargs
            )

        except Exception as err:
            log.error(f"Sending unauthorized request failed. Error: {err}  ")
            raise err from err

        return _request

    async def _send_request(
        self,
        url: str,
        method: hdrs.METH_POST | hdrs.METH_GET,
        headers: dict[str, str],
        **kwargs,
    ) -> str:
        """Send request to server.

        Args:
            url (str): requested endpoint
            method (hdrs.METH_POST | hdrs.METH_GET): which method to use
            headers (str): request headers
            **kwargs: kwargs

        Raises:
            Ex.TimeoutException: _description_
            Ex.BadRequestException: _description_
            Ex.TokensExpired: _description_
            Ex.AccessTokenExpired: _description_
            Ex.InvalidHTTPMethod: _description_
            Ex.InvalidLogin: _description_
            Ex.RefreshTokenExpired: _description_

        Returns:
            str: response in json format

        """

        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

        log.debug("Requesting URL %s, kwargs: %s", url, kwargs)
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self.session:
                    if method == hdrs.METH_GET:
                        response = await self.session.get(
                            url, ssl=True, headers=headers, **kwargs
                        )
                    else:
                        response = await self.session.post(
                            url, ssl=True, headers=headers, **kwargs
                        )
                    response_json = await response.json()
                    log.debug(f"Response: {response}")

        except TimeoutError as err:
            raise Ex.TimeoutException(
                f"Timeout occurred while connecting to server {url}"
            ) from err
        except aiohttp.ClientConnectionError as err:
            raise Ex.BadRequestException(f"Connection error: {url}") from err

        match response.status:
            case 401:
                if Errors.ACCESS_TOKEN_EXPIRED in response.headers.get(
                    "WWW-Authenticate"
                ):
                    raise Ex.AccessTokenExpired("Access token expired.")
                if Errors.REFRESH_TOKEN_EXPIRED in response.headers.get(
                    "WWW-Authenticate"
                ):
                    raise Ex.RefreshTokenExpired("Refresh token expired.")

                if Errors.INVALID_TOKEN in response.headers.get("WWW-Authenticate"):
                    raise Ex.InvalidToken("Invalid token provided.")

                raise Ex.BadRequestException(f"{url} with message: {response_json}")
            case 400:
                match response_json.get("error_uri"):
                    case x if Errors.INVALID_METHOD in x:
                        raise Ex.InvalidHTTPMethod(
                            f"Invalid HTTP method. Method '{method}' is not supported for '{url}'"
                        )
                    case x if Errors.INVALID_LOGIN in x:
                        raise Ex.InvalidLogin("Invalid login!")
                    case x if Errors.REFRESH_TOKEN_REDEEMD in x:
                        raise Ex.RefreshTokenRedeemd("Refresh token already redeemd!")
                    case x if Errors.INVALID_REFRESH_TOKEN in x:
                        raise Ex.InvalidRefreshToken("Invalid refresh token!")
                    case _:
                        raise Ex.BadRequestException(
                            f"{url} with message: {response_json}"
                        )
            case 200:
                return response_json
            case _:
                raise Ex.BadRequestException(f"{url} with message: {response_json}")

    async def async_schools_list(self) -> Schools:
        """Return list of schools with their API points."""

        _schools_list = Schools()
        headers = {"Accept": "application/json"}

        log.debug("Gathering list of towns ...")
        try:
            towns_json = await self.send_unauth_request(EndPoint.SCHOOL_LIST, headers)
        except Exception as exc:
            log.error(f"Error while gathering schools endpoints. {exc}")
            return None

        schools: list = []

        for town in towns_json:
            town_name = str(town["name"])
            if town_name == "":
                continue
            if "." in town_name:
                town_name = town_name[: town_name.find(".")]

            log.debug("Gathering schools for town: %s", town_name)

            endpoint = f"{EndPoint.SCHOOL_LIST.endpoint}/{parse.quote(town_name)}"

            response_town = await self._send_request(endpoint, hdrs.METH_GET, headers)

            schools: dict = response_town
            for _schools in schools.get("schools"):
                _schools_list.append_school(
                    name=_schools.get("name"),
                    api_point=_schools.get("schoolUrl"),
                    town=town_name,
                )

        return _schools_list

    async def first_login(self, username: str, password: str) -> Credentials:
        """First login.

        Create access and refresh tokens.
        """

        login_url = f"client_id=ANDR&grant_type=password&username={username}&password={password}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            log.debug("Trying to login with username and password ...")
            _credentials = await self.send_unauth_request(
                EndPoint.LOGIN, data=login_url, headers=headers
            )
        except Ex.InvalidLogin as ex:
            log.error("Invalid username / password provided.")
            raise ex from ex
        _credentials.update({"username": username})
        self.credentials = Credentials.create(_credentials)

        if self.auto_cache_credentials:
            self.save_credentials()
        return self.credentials

    async def refresh_access_token(self):
        """Refresh access token using refresh token.

        returns new Credentials if success, else RefreshTokenExpired exception
        """
        login_body = f"client_id=ANDR&grant_type=refresh_token&refresh_token={self.credentials.refresh_token}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            log.debug("Trying refresh token ... ")
            _credentials = await self.send_unauth_request(
                EndPoint.LOGIN, headers=headers, data=login_body
            )
        except Ex.RefreshTokenExpired as ex:
            raise ex from ex

        self.credentials = Credentials.create(_credentials)

        if self.auto_cache_credentials:
            self.save_credentials()

        return self.credentials

    def get_request_url(self, request_endpoint: EndPoint) -> str | Ex.BadEndpointUrl:
        """Get requested url from endpoint.

        Args:
            request_endpoint (EndPoint): EndPoint

        Raises:
            Ex.BadEndpointUrl: if no server is specified

        Returns:
            str: full url of endpoint

        """
        request = (
            request_endpoint.endpoint
            if request_endpoint.endpoint.lower().startswith(("http", "https"))
            else f"{self.server}{request_endpoint.endpoint}"
        )

        if not request.lower().startswith(("http", "https")):
            raise Ex.BadEndpointUrl(f"Bad endpoint url ({request})")

        return request

    def save_credentials(self, filename: str | None = None) -> bool:
        """Save credentials to file in JSON format.

        If auto_save_credentials are enabled, parameters could be ommited.
        """

        if not filename and self.auto_cache_credentials:
            filename = self.cache_filename
        try:
            with open(filename, "wb") as file:
                file.write(orjson.dumps(self.credentials, option=orjson.OPT_INDENT_2))
            file.close()
        except OSError:
            return False

        return True

    def load_credentials(self, filename: str) -> Credentials | bool:
        """Load credentials from file."""

        try:
            with open(filename, "rb") as file:
                data = orjson.loads(file.read())
            file.close()
        except OSError:
            return False

        self.credentials = Credentials.create_from_json(data)
        return self.credentials

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns:
            Bakalari object.

        """
        return self  # pragma: no cover

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
            _exc_info: Exec type.

        """
        return  # pragma: no cover
