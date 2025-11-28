"""API clinet tests."""

import asyncio
import logging
from typing import Any

import aiohttp
from aiohttp import hdrs
from aioresponses import aioresponses
from async_bakalari_api.api_client import ApiClient
from async_bakalari_api.const import Errors
from async_bakalari_api.exceptions import Ex
import pytest


@pytest.mark.asyncio
async def test_session_context_manager_creates_and_closes_session():
    """Tests that session context manager creates and closes session."""
    client = ApiClient()
    async with client as c:
        assert c._session is not None  # noqa: SLF001
        assert getattr(c._session, "closed", False) is False  # noqa: SLF001
        assert c._session_owner is True  # noqa: SLF001
    # after exit it should be closed and cleared
    assert client._session is None  # noqa: SLF001
    assert client._session_owner is False  # noqa: SLF001


@pytest.mark.asyncio
async def test_reuses_external_session_and_does_not_close_it():
    """Tests that external session is reused and not closed."""
    session = aiohttp.ClientSession()
    try:
        client = ApiClient(session=session)
        async with client as c:
            assert c._session is session  # noqa: SLF001
            assert c._session_owner is False  # noqa: SLF001
        # external session must remain open
        assert session.closed is False
    finally:
        await session.close()


@pytest.mark.asyncio
async def test_request_success_json_and_metrics_logging(
    caplog: pytest.LogCaptureFixture,
):
    """Tests that request success with JSON response and metrics logging."""
    caplog.set_level(logging.DEBUG, logger="async_bakalari_api.api_client")
    url = "https://example.com/api"
    payload = {"ok": True}

    with aioresponses() as m:
        async with ApiClient() as client:
            m.get(
                url,
                status=200,
                headers={"Content-Type": "application/json"},
                payload=payload,
            )

            res = await client.request(url, hdrs.METH_GET)

        assert res == payload
        # metrics log emitted
        records = [
            r
            for r in caplog.records
            if r.name == "async_bakalari_api.api_client" and r.msg == "api_request"
        ]
        assert records, "Expected api_request metric log"
        rec = records[-1]
        assert getattr(rec, "event", None) == "api_request"
        assert getattr(rec, "status", None) == 200
        assert getattr(rec, "method", None) == hdrs.METH_GET
        assert getattr(rec, "url", None) == url
        assert getattr(rec, "retries", None) == 0


@pytest.mark.asyncio
async def test_request_success_octet_stream_filename_and_bytes(
    caplog: pytest.LogCaptureFixture,
):
    """Tests that request success with octet-stream response and filename extraction."""
    caplog.set_level(logging.DEBUG, logger="async_bakalari_api.api_client")
    url = "https://example.com/download"
    data = b"binary-data"
    # Content-Disposition includes RFC5987 filename* with UTF-8'' prefix
    cd = "attachment; filename*=UTF-8''my%20file.bin"

    with aioresponses() as m:
        async with ApiClient() as client:
            m.get(
                url,
                status=200,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Disposition": cd,
                },
                body=data,
            )

            filename, filebytes = await client.request(url, hdrs.METH_GET)
        assert filename == "my file.bin"
        assert filebytes == data

        # metrics log emitted
        records = [r for r in caplog.records if r.msg == "api_request"]
        assert records and getattr(records[-1], "status", None) == 200


@pytest.mark.asyncio
async def test_request_timeout_maps_to_timeout_exception_and_logs_metric(
    caplog: pytest.LogCaptureFixture,
):
    """Tests that request timeout maps to TimeoutException and logs metric."""
    caplog.set_level(logging.DEBUG, logger="async_bakalari_api.api_client")

    class FakeRespCM:
        async def __aenter__(self):
            raise TimeoutError

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeSession:
        closed = False

        def request(self, *a, **k):
            return FakeRespCM()

    async with ApiClient() as client:
        # Monkeypatch ensure_session to use fake session
        client._session_owner = True  # noqa: SLF001

        async def fake_ensure():
            return FakeSession()

        client._ensure_session = fake_ensure  # type: ignore[assignment]

        with pytest.raises(Ex.TimeoutException):
            await client.request("https://timeout", hdrs.METH_GET)

        # metric with error=timeout
        records = [r for r in caplog.records if r.msg == "api_request"]
        assert records and getattr(records[-1], "error", None) == "timeout"


@pytest.mark.asyncio
async def test_request_connection_error_maps_to_bad_request_and_logs_metric(
    caplog: pytest.LogCaptureFixture,
):
    """Tests that request connection error maps to BadRequestException and logs metric."""
    caplog.set_level(logging.DEBUG, logger="async_bakalari_api.api_client")

    class FakeRespCM:
        async def __aenter__(self):
            raise aiohttp.ClientConnectionError

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeSession:
        closed = False

        def request(self, *a, **k):
            return FakeRespCM()

    async with ApiClient() as client:
        client._session_owner = True  # noqa: SLF001

        async def fake_ensure():
            return FakeSession()

        client._ensure_session = fake_ensure  # type: ignore[assignment]

        with pytest.raises(Ex.BadRequestException) as exc:
            await client.request("https://conn-error", hdrs.METH_GET)
        assert "Connection error:" in str(exc.value)

        records = [r for r in caplog.records if r.msg == "api_request"]
        assert records and getattr(records[-1], "error", None) == "connection_error"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("header", "exc_cls"),
    [
        (Errors.ACCESS_TOKEN_EXPIRED, Ex.AccessTokenExpired),
        (Errors.REFRESH_TOKEN_EXPIRED, Ex.RefreshTokenExpired),
        (Errors.INVALID_TOKEN, Ex.InvalidToken),
        ("some other", Ex.BadRequestException),
    ],
)
async def test_request_401_header_mappings(header: str, exc_cls: type[Exception]):
    """Tests that request 401 header mappings work correctly."""
    url = "https://example.com/protected"
    with aioresponses() as m:
        async with ApiClient() as client:
            m.get(url, status=401, headers={"WWW-Authenticate": header}, payload={})
            with pytest.raises(exc_cls):
                await client.request(url, hdrs.METH_GET)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error_uri", "exc_cls"),
    [
        (Errors.INVALID_METHOD, Ex.InvalidHTTPMethod),
        (Errors.INVALID_LOGIN, Ex.InvalidLogin),
        (Errors.REFRESH_TOKEN_REDEEMD, Ex.RefreshTokenRedeemd),
        (Errors.INVALID_REFRESH_TOKEN, Ex.InvalidRefreshToken),
        ("unknown", Ex.BadRequestException),
    ],
)
async def test_request_400_error_uri_mappings(error_uri: str, exc_cls: type[Exception]):
    """Tests that request 400 error URI mappings work correctly."""
    url = "https://example.com/bad"
    with aioresponses() as m:
        async with ApiClient() as client:
            m.get(url, status=400, headers={}, payload={"error_uri": error_uri})
            with pytest.raises(exc_cls):
                await client.request(url, hdrs.METH_GET)


@pytest.mark.asyncio
async def test_request_404_and_500_map_to_bad_request():
    """Tests that request 404 and 500 errors map to BadRequestException."""
    url = "https://example.com/notfound"
    with aioresponses() as m:
        async with ApiClient() as client:
            m.get(url, status=404, payload={})
            with pytest.raises(Ex.BadRequestException):
                await client.request(url, hdrs.METH_GET)

    url2 = "https://example.com/error"
    with aioresponses() as m:
        async with ApiClient() as client:
            m.get(url2, status=500, payload={"error": "x"})
            with pytest.raises(Ex.BadRequestException):
                await client.request(url2, hdrs.METH_GET)


@pytest.mark.asyncio
async def test_authorized_request_refresh_and_retry_success(
    caplog: pytest.LogCaptureFixture,
):
    """Tests that authorized request refresh and retry success works correctly."""
    caplog.set_level(logging.DEBUG, logger="async_bakalari_api.api_client")

    class Creds:
        def __init__(self, access_token: str | None, refresh_token: str | None):
            self.access_token = access_token
            self.refresh_token = refresh_token

    creds = Creds(access_token="old", refresh_token="r")

    calls: list[dict[str, Any]] = []

    async def fake_request(self, url, method, headers=None, *, retry=0, **kwargs):
        calls.append({"headers": dict(headers or {}), "retry": retry})
        if retry == 0:
            raise Ex.AccessTokenExpired("expired")
        return {"ok": True}

    async with ApiClient() as client:
        # patch instance method
        client.request = fake_request.__get__(client, ApiClient)  # type: ignore[assignment]

        async def refresh_cb():
            return Creds(access_token="new", refresh_token="r")

        res = await client.authorized_request(
            "https://example.com/protected",
            hdrs.METH_GET,
            credentials=creds,
            refresh_callback=refresh_cb,
        )
        assert res == {"ok": True}

    # first call used old token
    assert calls[0]["headers"].get("Authorization") == "Bearer old"
    # second call after refresh used new token and retry incremented
    assert calls[1]["headers"].get("Authorization") == "Bearer new"
    assert calls[1]["retry"] == 1

    # summary log must be present
    recs = [r for r in caplog.records if r.msg == "authorized_request"]
    assert recs and getattr(recs[-1], "retries", None) == 1


@pytest.mark.asyncio
async def test_authorized_request_refresh_token_expired_logs_and_raises(
    caplog: pytest.LogCaptureFixture,
):
    """Tests that authorized request refresh token expired logs and raises."""
    caplog.set_level(logging.DEBUG, logger="async_bakalari_api.api_client")

    class Creds:
        def __init__(self, access_token: str | None, refresh_token: str | None):
            self.access_token = access_token
            self.refresh_token = refresh_token

    creds = Creds(access_token=None, refresh_token="r")

    async def fake_request(self, url, method, headers=None, *, retry=0, **kwargs):
        raise Ex.RefreshTokenExpired("nope")

    async with ApiClient() as client:
        client.request = fake_request.__get__(client, ApiClient)  # type: ignore[assignment]
        with pytest.raises(Ex.RefreshTokenExpired):
            await client.authorized_request(
                "https://example.com/protected",
                hdrs.METH_GET,
                credentials=creds,
                refresh_callback=lambda: asyncio.sleep(0),  # not called
            )

    # summary log with error
    recs = [r for r in caplog.records if r.msg == "authorized_request"]
    assert recs and getattr(recs[-1], "error", None) == "refresh_expired"


@pytest.mark.asyncio
async def test_invalid_token_max_retries(
    caplog: pytest.LogCaptureFixture,
):
    """Tests that authorized request retries are bounded and attempts are counted."""
    caplog.set_level(logging.DEBUG, logger="async_bakalari_api.api_client")

    class Creds:
        def __init__(self, access_token: str | None, refresh_token: str | None):
            self.access_token = access_token
            self.refresh_token = refresh_token

    creds = Creds(access_token="a", refresh_token="r")
    _calls: int = 0

    async def refresh_cred():
        return creds

    async def fake_request(self, url, method, headers=None, *, retry=0, **kwargs):
        nonlocal _calls
        _calls += 1
        raise Ex.InvalidToken("nope")

    async with ApiClient() as client:
        client.request = fake_request.__get__(client, ApiClient)  # type: ignore[assignment]
        with pytest.raises(Ex.InvalidToken):
            await client.authorized_request(
                "https://example.com/protected",
                hdrs.METH_GET,
                credentials=creds,
                refresh_callback=lambda: refresh_cred(),
                max_retries=3,
            )

    # request was attempted exactly max_retries + 1 times (initial + retries)

    recs = [r for r in caplog.records if r.msg == "authorized_request"]
    assert recs and getattr(recs[-1], "error", None) == "auth failed:InvalidToken"
    assert getattr(recs[-1], "retries", None) == 3
    assert _calls == 4


@pytest.mark.asyncio
async def test_close_and_wait_alias_closes():
    """Tests that close_and_wait alias closes the client."""
    client = ApiClient()
    await client._ensure_session()  # noqa: SLF001
    assert client._session is not None  # noqa: SLF001
    await client.close_and_wait()
    assert client._session is None  # noqa: SLF001


@pytest.mark.asyncio
async def test_aenter_returns_self():
    """__aenter__ should return self to allow `as client` usage and cover return line."""
    client = ApiClient()
    c = await client.__aenter__()
    assert c is client
    # ensure we exit properly
    await client.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_authorized_request_token_missing_raises():
    """authorized_request should raise TokenMissing when no tokens are provided."""

    class Creds:
        def __init__(self):
            self.access_token = None
            self.refresh_token = None

    creds = Creds()
    async with ApiClient() as client:
        with pytest.raises(Ex.TokenMissing):
            await client.authorized_request(
                "https://example.com/protected",
                hdrs.METH_GET,
                credentials=creds,
                refresh_callback=lambda: asyncio.sleep(0),  # not called
            )


@pytest.mark.asyncio
async def test_can_reuse_after_close_creates_new_session():
    """Ensure ApiClient can be reused after close() by recreating AsyncExitStack and session."""
    client = ApiClient()
    # First lifecycle
    async with client as c:
        assert c._session is not None  # noqa: SLF001
    # Closed
    assert client._session is None  # noqa: SLF001

    # Reuse the same client instance: request should create a brand new session and not raise
    url = "https://example.com/reuse"
    with aioresponses() as m:
        m.get(
            url,
            status=200,
            headers={"Content-Type": "application/json"},
            payload={"ok": True},
        )
        res = await client.request(url, hdrs.METH_GET)
        assert res == {"ok": True}

    # Clean up
    await client.close()


@pytest.mark.asyncio
async def test___aexit_calls_close():
    """Ensure __aexit__ calls close() on the client."""
    client = ApiClient()
    called = {"v": False}
    orig_close = client.close

    async def counting_close():
        called["v"] = True
        await orig_close()

    # Monkeypatch the instance close before entering context
    client.close = counting_close  # type: ignore[assignment]

    async with client:
        # nothing, just ensure exit path is executed
        pass

    assert called["v"] is True


@pytest.mark.asyncio
async def test_authorized_request_refresh_no_access_token_pops_header():
    """After refresh returns no access_token, Authorization header must be removed."""

    class Creds:
        def __init__(self, access_token: str | None, refresh_token: str | None):
            self.access_token = access_token
            self.refresh_token = refresh_token

    creds = Creds(access_token="old", refresh_token="r")
    calls: list[dict[str, Any]] = []

    async def fake_request(self, url, method, headers=None, *, retry=0, **kwargs):
        # Snapshot headers to avoid mutation across retries
        calls.append({"headers": dict(headers or {}), "retry": retry})
        if retry == 0:
            raise Ex.AccessTokenExpired("expired")
        return {"ok": True}

    async with ApiClient() as client:
        # Bind fake request to this instance
        client.request = fake_request.__get__(client, ApiClient)  # type: ignore[assignment]

        async def refresh_cb():
            # Simulate refresh that does NOT provide access_token
            return Creds(access_token=None, refresh_token="r")

        res = await client.authorized_request(
            "https://example.com/protected",
            hdrs.METH_GET,
            credentials=creds,
            refresh_callback=refresh_cb,
        )
        assert res == {"ok": True}

    # First attempt had Authorization
    assert calls[0]["headers"].get("Authorization") == "Bearer old"
    # Second attempt after refresh must not carry Authorization anymore
    assert "Authorization" not in calls[1]["headers"]
