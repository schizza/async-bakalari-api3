"""Async Bakalari v3 API connector."""

from __future__ import annotations

import asyncio
from asyncio.locks import Lock
import logging
from typing import Self
from typing_extensions import Any, Never
from urllib import parse

import aiohttp
from aiohttp import hdrs
import orjson

from .const import REQUEST_TIMEOUT, EndPoint, Errors
from .datastructure import Credentials, Schools
from .exceptions import Ex
from .logger_api import api_logger

log = api_logger("Bakalari API", loglevel=logging.ERROR).get()


class Bakalari:
    """Root class of Bakalari."""

    response: None
    response_json: None

    _close_session:bool = False

    def __init__(
        self,
        server: str | None = None,
        credentials: Credentials | None = None,
        auto_cache_credentials: bool = False,
        cache_filename: str | None = None,
        session: aiohttp.ClientSession | None = None
    ):
        """Root class of Bakalari.

        Holds credentials, sends requests and perform first login.

        Args:
            server (str): Url of endpoint server.
            credentials (Credentials): Credentials object.
            auto_cache_credentials (bool, optional): If you want to cache credentials locally to file. Defaults to False.
            cache_filename (str, optional): Cache file name, if `auto_cache_credentials`. Defaults to None.

        """

        self._server: str | None = server
        self._credentials: Credentials = credentials if isinstance(credentials, Credentials) else Credentials()
        self._new_token: bool = False
        self._auto_cache_credentials: bool = auto_cache_credentials
        self._cache_filename: str | None = cache_filename
        self._session: aiohttp.ClientSession | None = session
        self._session_owner: bool = session is None
        self._refresh_lock: Lock = asyncio.Lock()
        self.schools: Schools = Schools()

        if self.auto_cache_credentials and not self.cache_filename:
            raise Ex.CacheError("Auto-cache is enabled, but no filename is provided!")

        if self._auto_cache_credentials and self._cache_filename:
            self.load_credentials(self._cache_filename)

    @property
    def credentials(self) -> Credentials:
        return self._credentials

    @credentials.setter
    def credentials(self, _value: Credentials) -> Never:
        raise AttributeError("Credentials are read-only. Use login/refresh methods.")

    @property
    def auto_cache_credentials(self) -> bool:
        return self._auto_cache_credentials

    @property
    def cache_filename(self) -> str | None:
        return self._cache_filename

    @property
    def server(self) -> str | None:
        return self._server

    async def _ensure_session(self) -> None:
        """Ensure aiohttp session exists (create if needed)."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                trust_env=True
            )
            self._session_owner = True

    # def __del__(self):
    #     """Destructor."""
    #     # Close connection when this object is destroyed
    #     try:
    #         loop = asyncio.get_event_loop()
    #     except RuntimeError:
    #         loop = asyncio.new_event_loop()
    #         asyncio.set_event_loop(loop)

    #     if loop.is_running():
    #         return loop.create_task(self._session.close())
    #     else:
    #         loop.run_until_complete(self._session.close())

    async def send_auth_request(
        self, request_endpoint: EndPoint, extend: str | None = None, **kwargs
    ):
        """Send authorized request with access token or refresh token."""

        request = self.get_request_url(request_endpoint)

        if extend:
            request += extend

        method = hdrs.METH_POST if "post" in request_endpoint.method else hdrs.METH_GET

        access_token_invalid = False
        result = None

        if not self.credentials.access_token and not self.credentials.refresh_token:
            raise Ex.TokenMissing("Access token or Refresh token is missing!")

        headers_access_token = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {self.credentials.access_token}",
        }

        #try access token
        try:
            log.debug("Trying access token ...")
            return await self._send_request(request, method=method, headers=headers_access_token, **kwargs)
        except (Ex.AccessTokenExpired, Ex.InvalidToken):
            log.debug("Access token expired or invalid!")
            await self.refresh_access_token()
            headers_access_token = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Bearer {self.credentials.access_token}",
            }
            try:
                return await self._send_request(request, method=method, headers=headers_access_token, **kwargs)
            except Ex.RefreshTokenExpired as ex:
                log.error("Refresh token expired! Login with username/password")
                raise ex from ex


        # while True:
        #     if self.credentials.access_token and not access_token_invalid:
        #         log.debug("Trying access token ...")
        #         try:
        #             headers_access_token = {
        #                 "Content-Type": "application/x-www-form-urlencoded",
        #                 "Authorization": f"Bearer {self.credentials.access_token}",
        #             }

        #             result = await self._send_request(
        #                 request, method=method, headers=headers_access_token
        #             )

        #         except Ex.AccessTokenExpired:
        #             access_token_invalid = True
        #             continue
        #         except Ex.InvalidToken:
        #             access_token_invalid = True
        #             continue
        #         except Exception as ex:
        #             raise ex from ex
        #         else:
        #             return result

        #     if access_token_invalid and self.refresh_access_token:
        #         try:
        #             await self.refresh_access_token()
        #         except Ex.RefreshTokenExpired as ex:
        #             log.error("Refresh token expired! Login with username/password")
        #             raise ex from ex
        #         except Exception as ex:
        #             raise ex from ex
        #         access_token_invalid = False

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

        await self._ensure_session()

        filedata = None
        filename = None

        if method == hdrs.METH_GET:
            session = self._session.get
        else:
            session = self._session.post

        log.debug("Requesting URL %s, kwargs: %s", url, kwargs)
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with session(
                    url, ssl=True, headers=headers, **kwargs
                ) as response:
                    if (
                        response.headers.get(aiohttp.hdrs.CONTENT_TYPE)
                        == "application/octet-stream"
                    ):
                        filedata = await response.read()
                        filename = response.headers[aiohttp.hdrs.CONTENT_DISPOSITION]
                        filename = parse.unquote(
                            filename[filename.rindex("filename*=") + 17 :]
                        )
                    else:
                        response_json = await response.json()
                        log.debug(f"Response: {response_json}")

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
            case 404:
                raise Ex.BadRequestException(f"Not found! ({url})")
            case 200:
                return [filename, filedata] if filedata else response_json
            case _:
                raise Ex.BadRequestException(f"{url} with message: {response_json}")

    async def schools_list(
        self, town: str | None = None, recursive: bool = True
    ) -> Schools:
        """Return list of schools with their API points."""

        _schools_list = Schools()
        headers = {"Accept": "application/json"}

        log.debug("Gathering list of towns ...")
        try:
            towns_json = await self.send_unauth_request(EndPoint.SCHOOL_LIST, headers)
        except Exception as exc:
            log.error(f"Error while gathering schools endpoints. {exc}")
            return None

        if town and recursive:
            towns_json = [
                town_element
                for town_element in towns_json
                if town in town_element["name"]
            ]
        if town and not recursive:
            towns_json = [
                town_element
                for town_element in towns_json
                if town_element["name"].startswith(town)
            ]

        schools: list = []
        tasks = []

        for _town in towns_json:
            town_name = str(_town["name"])
            if town_name == "" or None:
                continue
            if "." in town_name:
                town_name = town_name[: town_name.find(".")]

            log.debug("Gathering schools for town: %s", town_name)

            endpoint = f"{EndPoint.SCHOOL_LIST.endpoint}/{parse.quote(town_name)}"

            task = asyncio.create_task(
                self._send_request(endpoint, hdrs.METH_GET, headers), name=town_name
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        for response_town in responses:
            schools: dict = response_town
            for _schools in schools.get("schools"):
                _schools_list.append_school(
                    name=_schools.get("name"),
                    api_point=_schools.get("schoolUrl"),
                    town=response_town.get("name"),
                )

        self.schools = _schools_list

        return _schools_list

    async def first_login(self, username: str, password: str) -> Credentials:
        """First login.

        Create access and refresh tokens.
        """

        login_params = parse.urlencode(
            {
                "client_id": "ANDR",
                "grant_type": "password",
                "username": username,
                "password": password,
            }
        )

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            log.debug(f"Trying to login with username: {username}")
            _credentials = await self.send_unauth_request(
                EndPoint.LOGIN, data=login_params, headers=headers
            )
        except Ex.InvalidLogin as ex:
            log.error("Invalid username / password provided.")
            raise ex from ex
        if isinstance(_credentials, dict):
            _credentials.update({"username": username})

        self._credentials = Credentials.create(_credentials)

        log.info(f"Successfully logged in with username: {username}")

        if self._auto_cache_credentials:
            self.save_credentials()
        return self.credentials

    async def refresh_access_token(self) -> Credentials:
        """Refresh access token using refresh token.

        returns new Credentials if success, else RefreshTokenExpired exception
        """
        async with self._refresh_lock:
            if not self.credentials.refresh_token:
                raise Ex.RefreshTokenExpired("No refresh token available")

            login_body = parse.urlencode(
                {
                "client_id": "ANDR",
                "grant_type": "refresh_token",
                    "refresh_token": self.credentials.refresh_token,
                }
            )

            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            try:
                log.debug("Trying refresh token ... ")
                _credentials = await self.send_unauth_request(
                EndPoint.LOGIN, headers=headers, data=login_body
                )
            except Ex.RefreshTokenExpired as ex:
                log.error("Refresh token expired! Login with username/password")
                raise ex from ex

            self._credentials = Credentials.create(_credentials)

            if self._auto_cache_credentials:
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
            else f"{self._server}{request_endpoint.endpoint}"
        )

        if not request.lower().startswith(("http", "https")):
            raise Ex.BadEndpointUrl(f"Bad endpoint url ({request})")

        return request

    def save_credentials(self, filename: str | None = None) -> bool:
        """Save credentials to file in JSON format.

        If auto_save_credentials are enabled, parameters could be ommited.
        """

        filename = filename or self._cache_filename
        try:
            with open(filename, "wb") as file:
                file.write(orjson.dumps(self.credentials, option=orjson.OPT_INDENT_2))
                log.debug(f"Credentials saved to file {filename}")
        except OSError as err:
            log.error(f"Error while saving credentials to file {filename}. {str(err)}")
            return False

        return True

    def load_credentials(self, filename: str) -> Credentials | bool:
        """Load credentials from file."""

        try:
            with open(filename, "rb") as file:
                data = orjson.loads(file.read())
                self._credentials = Credentials.create_from_json(data)
                return self.credentials

        except (OSError, orjson.JSONDecodeError):
            log.error(f"Error while loading credentials from file {filename}")
            self._credentials = Credentials()
            return False

    async def aclose(self) -> None:
        """Close the session."""

        if self._session and self._session_owner and not self._session.closed:
            await self._session.close()
        self._session = None
        self._session_owner = False

    async def __aenter__(self) -> Self:
        await self._ensure_session()

        return self  # pragma: no cover

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
            _exc_info: Exec type.

        """

        await self.aclose()

        return  # pragma: no cover
