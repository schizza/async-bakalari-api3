"""Async Bakalari v3 API connector."""
from __future__ import annotations

import datetime
import asyncio
from typing import Any
import json

import aiohttp
from aiohttp import hdrs

import async_timeout


from exceptions import Ex
from const import REQUEST_TIMEOUT, Errors, EndPoint
from datastructure import Credentials


class Bakalari:
    """Root class of Bakalari."""

    session: aiohttp.client.ClientSession | None = None
    response: None
    response_json: None

    _close_session = False

    def __init__(
        self,
        credentials: Credentials,
        server: str = None,
    ):
        self.server = server
        self.credentials = credentials

    @staticmethod
    def purge_request(request=str) -> str:
        """Clean request.

        TODO
        """
        return request

    async def first_login(
        self, username: str = None, password: str = None
    ) -> Credentials:
        """First login.

        Create access and refrest token.
        """

        login_url = f"client_id=ANDR&grant_type=password&username={username}&password={password}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        _credentials = await self.send_request(
            f"{self.server}{EndPoint.LOGIN}", data=login_url, headers=headers
        )
        if isinstance(_credentials, Ex):
            return _credentials

        _credentials["username"] = username
        return Credentials.get(_credentials)

    async def refresh_access_token(self):
        """Refresh access token using refresh token.

        returns new Credentials if success, else RefreshTokenExpired exception
        """

        login_url = f"client_id=ANDR&grant_type=refresh_token&refresh_token={self.credentials.refresh_token}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        _credentials = await self.send_request(
            f"{self.server}{EndPoint.LOGIN}", data=login_url, headers=headers
        )
        if isinstance(_credentials, Ex):
            return _credentials

        self.credentials = Credentials.get(_credentials)

        return self.credentials

    async def send_request(self, request, method=hdrs.METH_POST, **kwargs):
        """Send request to server."""

        request = self.purge_request(request)

        if (self.credentials.access_token) and ("headers" not in kwargs):
            headers_access_token = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Bearer {self.credentials.access_token}",
            }
            headers = headers_access_token
        elif "headers" in kwargs:
            headers = kwargs.pop("headers")

        if self.session is None:
            self.session = aiohttp.ClientSession()
            self._close_session = True

        try:
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                response = await self.session.request(
                    method=method, url=request, ssl=True, headers=headers, **kwargs
                )
                response_json = await response.json()

        except asyncio.TimeoutError:
            return Ex.TimeoutException(
                f"Timeout occurred while connecting to server {request}."
            )

        if (response.status == 401) and (
            Errors.ACCESS_TOKEN_EXPIRED in response.headers["WWW-Authenticate"]
        ):
            return Ex.AccessTokenExpired

        if (response.status == 400) and (
            response_json["error_uri"] == Errors.INVALID_METHOD
        ):
            return Ex.InvalidHTTPMethod

        if (response.status == 400) and (
            response_json["error_uri"] == Errors.INVALID_LOGIN
        ):
            return Ex.InvalidLogin

        elif response.status == 400:
            return (
                Ex.BadRequestException,
                response_json,
            )  # TODO - remove response_json in final

        elif response.status == 200:
            return response_json

        return response_json, response

    async def close(self) -> None:
        """Close open client session."""

        if self.session:
            await self.session.close()
            self.session = None

    async def __aenter__(self):
        """Async enter.

        Returns:
            Bakalari object.
        """
        return self

    async def __aexit__(self, *_exc_info: Any) -> None:
        """Async exit.
        Args:
            _exc_info: Exec type.
        """
        await self.close()


class Komens:
    """Class for manipulating Komens messages."""

    def __init__(self, bak: Bakalari):
        """Initialize class."""
        self._bak = bak

    async def messages(self):
        """Get unread messages."""

        request = f"{self._bak.server}{EndPoint.KOMENS_UNREAD}"
        return await self._bak.send_request(request)

    def unread_messages(self):
        pass
