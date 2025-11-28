"""Internal HTTP client utilities for the Bakalari API."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack
import logging
import time
from typing import Any, Self
from urllib import parse

import aiohttp

from .const import REQUEST_TIMEOUT, Errors
from .exceptions import Ex

log = logging.getLogger(__name__)


class ApiClient:
    """Thin wrapper around :mod:`aiohttp` with structured logging and metrics."""

    def __init__(
        self,
        *,
        session: aiohttp.ClientSession | None = None,
        timeout: float = REQUEST_TIMEOUT,
    ) -> None:
        """Thin wrapper around :mod:`aiohttp` with structured logging and metrics."""

        self._timeout = timeout
        self._external_session = session
        self._session: aiohttp.ClientSession | None = session
        self._session_owner = session is None
        self._exit_stack = AsyncExitStack()

    async def __aenter__(self) -> Self:
        """Enter the async context manager."""
        await self._ensure_session()
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Exit the async context manager."""
        await self.close()

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            if not self._session_owner and self._external_session is not None:
                self._session = self._external_session
            else:
                session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self._timeout), trust_env=True
                )
                self._session = await self._exit_stack.enter_async_context(session)
                self._session_owner = True
        return self._session

    async def close(self) -> None:
        """Close the managed session."""

        if self._session_owner:
            await self._exit_stack.aclose()
            # Recreate the exit stack so this client can be reused later
            self._exit_stack = AsyncExitStack()
        self._session = None
        self._session_owner = False

    async def request(  # noqa: C901
        self,
        url: str,
        method: str,
        headers: dict[str, str] | None = None,
        *,
        retry: int = 0,
        **kwargs: Any,
    ) -> Any:
        """Execute HTTP request and map errors to domain exceptions."""

        session = await self._ensure_session()
        headers = headers or {}
        start = time.perf_counter()
        try:
            async with asyncio.timeout(self._timeout):
                async with session.request(
                    method,
                    url,
                    ssl=True,
                    headers=headers,
                    **kwargs,
                ) as response:
                    payload: Any
                    if response.status == 204:
                        # No content; avoid attempting to parse JSON.
                        payload = None
                    elif (
                        response.headers.get(aiohttp.hdrs.CONTENT_TYPE)
                        == "application/octet-stream"
                    ):
                        filedata = await response.read()
                        filename = response.headers[aiohttp.hdrs.CONTENT_DISPOSITION]
                        filename = parse.unquote(
                            filename[filename.rindex("filename*=") + 17 :]
                        )
                        payload = [filename, filedata]
                    else:
                        try:
                            payload = await response.json()
                        except aiohttp.ContentTypeError:
                            # Empty body or non-JSON when we expected JSON; treat as None.
                            payload = None
                    latency = (time.perf_counter() - start) * 1000
                    self._log_metrics(
                        url,
                        method,
                        latency,
                        retry=retry,
                        status=response.status,
                    )
        except TimeoutError as err:
            latency = (time.perf_counter() - start) * 1000
            self._log_metrics(url, method, latency, retry=retry, error="timeout")
            raise Ex.TimeoutException(
                f"Timeout occurred while connecting to server {url}"
            ) from err
        except aiohttp.ClientConnectionError as err:
            latency = (time.perf_counter() - start) * 1000
            self._log_metrics(
                url, method, latency, retry=retry, error="connection_error"
            )
            raise Ex.BadRequestException(f"Connection error: {url}") from err

        match response.status:
            case 401:
                if Errors.ACCESS_TOKEN_EXPIRED in response.headers.get(
                    "WWW-Authenticate", ""
                ):
                    raise Ex.AccessTokenExpired("Access token expired.")
                if Errors.REFRESH_TOKEN_EXPIRED in response.headers.get(
                    "WWW-Authenticate", ""
                ):
                    raise Ex.RefreshTokenExpired("Refresh token expired.")
                if Errors.INVALID_TOKEN in response.headers.get("WWW-Authenticate", ""):
                    raise Ex.InvalidToken("Invalid token provided.")
                raise Ex.BadRequestException(f"{url} with message: {payload}")
            case 400:
                match (payload or {}).get("error_uri", {}):
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
                        raise Ex.BadRequestException(f"{url} with message: {payload}")
            case 404:
                raise Ex.BadRequestException(f"Not found! ({url})")
            case 200:
                return payload
            case 204:
                # No Content (e.g. mark-as-read). Return None to signal success without payload.
                return None
            case _:
                raise Ex.BadRequestException(f"{url} with message: {payload}")

    async def authorized_request(
        self,
        url: str,
        method: str,
        *,
        credentials: Any,
        refresh_callback: Callable[[], Awaitable[Any]],
        headers: dict[str, str] | None = None,
        max_retries: int = 1,
        **kwargs: Any,
    ) -> Any:
        """Make authorized request."""

        if not getattr(credentials, "access_token", None) and not getattr(
            credentials, "refresh_token", None
        ):
            raise Ex.TokenMissing("Access token or Refresh token is missing!")

        headers = {
            **(headers or {}),
        }
        if credentials.access_token:
            headers["Authorization"] = f"Bearer {credentials.access_token}"
        else:
            headers.pop("Authorization", None)

        retries = 0
        total_start = time.perf_counter()

        while True:
            try:
                result = await self.request(
                    url, method=method, headers=headers, retry=retries, **kwargs
                )
                latency = (time.perf_counter() - total_start) * 1000
                self._log_request_summary(url, method, latency, retries)

            except (Ex.AccessTokenExpired, Ex.InvalidToken) as auth_err:
                if retries >= max_retries:
                    latency = (time.perf_counter() - total_start) * 1000
                    self._log_request_summary(
                        url,
                        method,
                        latency,
                        retries,
                        error=f"auth failed:{auth_err.__class__.__name__}",
                    )
                    raise
                retries += 1
                log.warning(
                    "access_token_refresh",
                    extra={
                        "event": "token_refresh",
                        "url": url,
                        "method": method,
                        "retry": retries,
                    },
                )
                credentials = await refresh_callback()
                if credentials.access_token:
                    headers["Authorization"] = f"Bearer {credentials.access_token}"
                else:
                    headers.pop("Authorization", None)
            except Ex.RefreshTokenExpired:
                latency = (time.perf_counter() - total_start) * 1000
                self._log_request_summary(
                    url, method, latency, retries, error="refresh_expired"
                )
                raise
            else:
                return result

    async def close_and_wait(self) -> None:
        """Alias for :meth:`close` for backwards compatibility."""

        await self.close()

    def _log_metrics(
        self,
        url: str,
        method: str,
        latency_ms: float,
        *,
        retry: int = 0,
        status: int | None = None,
        error: str | None = None,
    ) -> None:
        extra = {
            "event": "api_request",
            "url": url,
            "method": method,
            "latency_ms": round(latency_ms, 2),
            "retries": retry,
        }
        if status is not None:
            extra["status"] = status
        if error is not None:
            extra["error"] = error
        log.debug("api_request", extra=extra)

    def _log_request_summary(
        self,
        url: str,
        method: str,
        latency_ms: float,
        retries: int,
        *,
        error: str | None = None,
    ) -> None:
        extra = {
            "event": "authorized_request",
            "url": url,
            "method": method,
            "latency_ms": round(latency_ms, 2),
            "retries": retries,
        }
        if error:
            extra["error"] = error
        log.debug("authorized_request", extra=extra)
