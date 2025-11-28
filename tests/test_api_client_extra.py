"""Additional tests to raise coverage for ApiClient.

focus on 204 handling,
octet-stream attachments, ContentTypeError fallback, external session usage,
and specific authorized_request branches.

"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from aiohttp import hdrs
from aioresponses import aioresponses
from async_bakalari_api.api_client import ApiClient
from async_bakalari_api.exceptions import Ex
import pytest


class Creds:
    """Simple credentials stub used in tests."""

    def __init__(self, access_token: str | None, refresh_token: str | None):
        """Initialize a new instance of Creds."""
        self.access_token = access_token
        self.refresh_token = refresh_token


# ---------------------------------------------------------------------------
# request() specific branch tests
# ---------------------------------------------------------------------------


async def test_request_204_returns_none_and_logs_status(
    caplog: pytest.LogCaptureFixture,
):
    """Ensure 204 No Content is returned as None and status is logged."""
    caplog.set_level(logging.DEBUG, logger="async_bakalari_api.api_client")
    url = "https://example.com/no-content"
    with aioresponses() as m:
        m.get(url, status=204, headers={})
        async with ApiClient() as client:
            res = await client.request(url, hdrs.METH_GET)
    assert res is None
    # Find api_request log with status=204
    recs = [
        r
        for r in caplog.records
        if r.msg == "api_request" and getattr(r, "status", None) == 204
    ]
    assert recs, "Expected api_request log record for 204 response."


async def test_request_octet_stream_parses_filename_and_bytes(
    caplog: pytest.LogCaptureFixture,
):
    """Ensure application/octet-stream is parsed into [filename, bytes]."""
    caplog.set_level(logging.DEBUG, logger="async_bakalari_api.api_client")
    url = "https://example.com/file"
    content = b"FILEDATA"
    # Content-Disposition must include filename*=utf-8''...
    headers = {
        "Content-Type": "application/octet-stream",
        "Content-Disposition": "attachment; filename*=utf-8''test-name.txt",
    }
    with aioresponses() as m:
        m.get(url, status=200, body=content, headers=headers)
        async with ApiClient() as client:
            res = await client.request(url, hdrs.METH_GET)
    assert isinstance(res, list) and len(res) == 2
    assert res[0] == "test-name.txt"
    assert res[1] == content
    # Confirm metrics logged with status 200
    assert any(
        r.msg == "api_request" and getattr(r, "status", None) == 200
        for r in caplog.records
    )


async def test_request_non_json_content_type_error_fallback_to_none():
    """If response.json() raises ContentTypeError, payload should become None."""
    url = "https://example.com/text"
    headers = {"Content-Type": "text/plain"}
    with aioresponses() as m:
        # Return plain text; aiohttp response.json() should raise ContentTypeError
        m.get(url, status=200, body="plain text", headers=headers)
        async with ApiClient() as client:
            res = await client.request(url, hdrs.METH_GET)
    assert res is None


# ---------------------------------------------------------------------------
# _ensure_session / context manager ownership branches
# ---------------------------------------------------------------------------


async def test_api_client_external_session_not_closed_on_exit():
    """External session should remain open after context exit."""
    session = aiohttp.ClientSession()
    client = ApiClient(session=session)
    async with client as c:
        # _session points to external, owner flag should be False
        assert c._session is session  # noqa: SLF001
        assert c._session_owner is False  # noqa: SLF001
    # After exit, internal _session cleared but external still open
    assert client._session is None  # noqa: SLF001
    assert not session.closed
    await session.close()


async def test_api_client_internal_session_closed_on_exit():
    """Internally managed session should be closed after exit."""
    async with ApiClient() as client:
        internal = client._session  # noqa: SLF001
        assert internal is not None
        assert client._session_owner is True  # noqa: SLF001
    # After exit
    assert client._session is None  # noqa: SLF001
    # internal session should be closed
    assert internal.closed  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# authorized_request branches
# ---------------------------------------------------------------------------


async def test_authorized_request_simple_success_with_access_token(
    caplog: pytest.LogCaptureFixture,
):
    """Covers branch where first request succeeds (no retries)."""
    caplog.set_level(logging.DEBUG, logger="async_bakalari_api.api_client")
    url = "https://example.com/ok"
    with aioresponses() as m:
        m.get(url, status=200, payload={"done": True})
        async with ApiClient() as client:
            creds = Creds(access_token="AT", refresh_token="RT")
            res = await client.authorized_request(
                url,
                hdrs.METH_GET,
                credentials=creds,
                refresh_callback=lambda: asyncio.sleep(0),
            )
    assert res == {"done": True}
    # authorized_request summary log with retries=0
    assert any(
        r.msg == "authorized_request" and getattr(r, "retries", None) == 0
        for r in caplog.records
    )


async def test_authorized_request_refresh_after_access_token_expired_then_success(
    caplog: pytest.LogCaptureFixture,
):
    """Simulate expired access token -> refresh -> retry success."""
    caplog.set_level(logging.DEBUG, logger="async_bakalari_api.api_client")
    url = "https://example.com/protected"
    creds = Creds(access_token="OLD", refresh_token="R")

    # We emulate .request by patching the instance method to raise AccessTokenExpired once.
    async with ApiClient() as client:
        calls: list[str] = []

        async def fake_request(
            self, url_: str, method: str, headers: dict[str, str], retry: int, **kw: Any
        ):
            calls.append(f"try{retry}")
            if retry == 0:
                raise Ex.AccessTokenExpired("expired")
            return {"secure": True}

        # Bind fake_request
        client.request = fake_request.__get__(client, ApiClient)  # type: ignore[assignment]

        async def refresh_cb():
            # Provide new access token after refresh
            return Creds(access_token="NEW", refresh_token="R")

        result = await client.authorized_request(
            url,
            hdrs.METH_GET,
            credentials=creds,
            refresh_callback=refresh_cb,
        )

    assert result == {"secure": True}
    assert calls == ["try0", "try1"]
    # Verify summary log indicates 1 retry
    assert any(
        r.msg == "authorized_request" and getattr(r, "retries", None) == 1
        for r in caplog.records
    )


async def test_authorized_request_no_access_token_header_removed_and_success(
    caplog: pytest.LogCaptureFixture,
):
    """Start without access_token -> header Authorization removed -> success."""
    caplog.set_level(logging.DEBUG, logger="async_bakalari_api.api_client")
    url = "https://example.com/no-auth-token"
    creds = Creds(access_token=None, refresh_token="R")

    async with ApiClient() as client:
        recorded_headers: list[dict[str, str]] = []

        async def fake_request(
            self, url_: str, method: str, headers: dict[str, str], retry: int, **kw: Any
        ):
            # Authorization must not be present
            recorded_headers.append(headers.copy())
            return {"ok": True}

        client.request = fake_request.__get__(client, ApiClient)  # type: ignore[assignment]
        res = await client.authorized_request(
            url,
            hdrs.METH_GET,
            credentials=creds,
            refresh_callback=lambda: asyncio.sleep(0),
        )

    assert res == {"ok": True}
    assert recorded_headers and "Authorization" not in recorded_headers[0]


async def test_authorized_request_token_missing_raises():
    """Explicit coverage for TokenMissing raise branch (redundant but ensures new file executes it)."""
    creds = Creds(access_token=None, refresh_token=None)
    async with ApiClient() as client:
        with pytest.raises(Ex.TokenMissing):
            await client.authorized_request(
                "https://example.com/any",
                hdrs.METH_GET,
                credentials=creds,
                refresh_callback=lambda: asyncio.sleep(0),
            )


# ---------------------------------------------------------------------------
# request() error mapping for connection error (alternate path)
# ---------------------------------------------------------------------------


async def test_request_client_connection_error_maps_to_bad_request():
    """Simulate connection error using an async context manager to trigger branch cleanly."""
    url = "https://conn-error-alt"
    async with ApiClient() as client:

        class FakeRespCM:
            async def __aenter__(self):
                raise aiohttp.ClientConnectionError

            async def __aexit__(self, exc_type, exc, tb):
                return False

        class FakeSession:
            closed = False

            def request(self, *a, **k):
                # Return an object usable in `async with` that raises on enter
                return FakeRespCM()

            async def close(self):
                self.closed = True

        async def fake_ensure():
            return FakeSession()

        client._ensure_session = fake_ensure  # type: ignore[assignment]
        with pytest.raises(Ex.BadRequestException):
            await client.request(url, hdrs.METH_GET)


async def test_close_and_wait_alias():
    """Ensure close_and_wait properly closes internal session and resets state."""
    async with ApiClient() as client:
        # Force creation
        await client._ensure_session()
        assert client._session is not None  # noqa: SLF001
        await client.close_and_wait()
        assert client._session is None  # noqa: SLF001


async def test_request_400_without_error_uri_maps_bad_request():
    """400 without error_uri key should map to BadRequestException (generic branch)."""
    url = "https://example.com/bad400"
    with aioresponses() as m:
        m.get(
            url, status=400, payload={}
        )  # empty dict -> (payload or {}).get('error_uri') is None
        async with ApiClient() as client:
            with pytest.raises(Ex.BadRequestException):
                await client.request(url, hdrs.METH_GET)
