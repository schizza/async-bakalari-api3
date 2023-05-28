"""Async Bakalari v3 API connector."""
from __future__ import annotations

import datetime
import logging
import asyncio
from urllib import parse
from typing import Any

import aiohttp
from aiohttp import hdrs

import async_timeout


from exceptions import Ex
from const import REQUEST_TIMEOUT, Errors, EndPoint
from datastructure import Credentials, Schools


async def schools_list() -> Schools:
    """Returns list of schools with their API points."""

    _schools_list = Schools()
    request = "https://sluzby.bakalari.cz/api/v1/municipality"
    headers = {"Accept": "application/json"}
    session = aiohttp.ClientSession()

    try:
        async with async_timeout.timeout(REQUEST_TIMEOUT):
            response = await session.request(
                method=hdrs.METH_GET, url=request, ssl=True, headers=headers
            )
    except asyncio.TimeoutError as err:
        raise Ex.TimeoutException(
            f"Timeout occurred while connecting to server {request}."
        ) from err

    except aiohttp.ClientConnectionError as err:
        raise Ex.BadRequestException(f"Connection error: {request}.") from err

    try:
        response_json = await response.json()
    except Exception as err:
        await session.close()
        raise Ex.InvalidResponse("Invalid response from server.") from err

    schools: list = []
    for town in response_json:
        town_name = str(town["name"])
        if town_name == "":
            continue
        if "." in town_name:
            town_name = town_name[: town_name.find(".")]

        request_town = f"{request}/{parse.quote(town_name)}"
        response_town = await session.request(
            method=hdrs.METH_GET, url=request_town, ssl=True, headers=headers
        )
        schools: dict = await response_town.json()
        for _schools in schools.get("schools"):
            _schools_list.append_school(
                name=_schools.get("name"),
                api_point=_schools.get("schoolUrl"),
                town=town_name,
            )

    await session.close()

    return _schools_list


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
        self.new_token = False

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

        Create access and refresh tokens.
        """

        login_url = f"client_id=ANDR&grant_type=password&username={username}&password={password}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        _credentials = await self.send_request(
            EndPoint.LOGIN, data=login_url, headers=headers
        )
        if isinstance(_credentials, Ex):
            return _credentials

        _credentials.update({"username":username})
        return Credentials.get(_credentials)

    async def refresh_access_token(self):
        """Refresh access token using refresh token.

        returns new Credentials if success, else RefreshTokenExpired exception
        """

        login_url = f"client_id=ANDR&grant_type=refresh_token&refresh_token={self.credentials.refresh_token}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        _credentials = await self.send_request(
            EndPoint.LOGIN, data=login_url, headers=headers
        )
        if isinstance(_credentials, Ex):
            return _credentials

        self.credentials = Credentials.get(_credentials)

        return self.credentials

    async def send_request(self, request: EndPoint, method=hdrs.METH_POST, **kwargs):
        """Send request to server."""

        request = f"{self.server}{request}"

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

        except asyncio.TimeoutError as err:
            raise Ex.TimeoutException(
                f"Timeout occurred while connecting to server {request}."
            ) from err
        except aiohttp.ClientConnectionError as err:
            raise Ex.BadRequestException(f"Connection error: {request}.") from err

        if (response.status == 401) and (
            Errors.ACCESS_TOKEN_EXPIRED in response.headers["WWW-Authenticate"]
        ):
            try:
                new_credentials = await self.refresh_access_token()
            except Ex.RefreshTokenExpired as exc:
                raise Ex.TokensExpired(
                    "Unable to refresh access token. Refresh token has been redeemd."
                ) from exc
            self.credentials = new_credentials
            self.new_token = True
            raise Ex.AccessTokenExpired

        if (response.status == 400) and (
            Errors.INVALID_METHOD in response_json["error_uri"]
        ):
            raise Ex.InvalidHTTPMethod

        if (response.status == 400) and (
            Errors.INVALID_LOGIN in response_json["error_uri"]
        ):
            raise Ex.InvalidLogin

        if (response.status == 400) and (
            Errors.REFRESH_TOKEN_EXPIRED in response_json["error_uri"]
        ):
            raise Ex.RefreshTokenExpired("Refresh token already redeemd!")

        if response.status in [400, 401]:
            raise Ex.BadRequestException(response, response_json)
            # TODO - remove response_json in final

        if response.status == 200:
            return response_json

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
        return await self._bak.send_request(EndPoint.KOMENS_UNREAD)

    def unread_messages(self):
        pass
