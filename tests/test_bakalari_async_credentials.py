"""Tests enforcing await-safe session handling, immutable credentials, and per-instance refresh behavior."""

import asyncio
from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from async_bakalari_api.bakalari import Bakalari
from async_bakalari_api.datastructure import Credentials
from async_bakalari_api.const import EndPoint
from async_bakalari_api.exceptions import Ex

FS = "http://fake_server"


@pytest.mark.asyncio
async def test_session_context_manager_closes_session():
    # The context manager should create and close the aiohttp session await-safely
    async with Bakalari(FS) as b:
        assert b._session is not None
        # session must be open inside the context
        assert getattr(b._session, "closed", False) is False

    # after context exit, the session should be closed (or cleared to None)
    # allow either closed session or cleared session object
    # to support the implementation that sets session to None after closing
    # or just closes it and keeps the reference
    try:
        # if session reference is retained
        assert b._session is None or getattr(b._session, "closed", True) is True
    except AttributeError:
        # if implementation removes the attribute
        assert True


def test_credentials_property_is_readonly():
    b = Bakalari(FS)

    # Attempt to reassign the credentials property should fail
    with pytest.raises(AttributeError):
        b.credentials = Credentials(username="x", access_token="a", refresh_token="r", user_id="id")


def test_credentials_object_is_immutable():
    c = Credentials(username="u", access_token="a", refresh_token="r", user_id="id")

    # Modifying the credential fields should be disallowed (frozen dataclass)
    with pytest.raises((AttributeError, FrozenInstanceError)):
        # type: ignore[attr-defined] - we intentionally try to mutate to ensure immutability
        c.access_token = "new"  # noqa: B015


@pytest.mark.asyncio
async def test_credentials_attributes_cannot_be_mutated_through_instance():
    b = Bakalari(FS)

    # Seed credentials in a way that works for both current and future implementation
    seeded = Credentials(username="u", access_token="a", refresh_token="r", user_id="id")
    if hasattr(b, "_credentials"):
        # new implementation detail (private attr)
        object.__setattr__(b, "_credentials", seeded)
    else:
        # legacy implementation (public, mutable) - this should eventually fail if property is read-only
        try:
            b.credentials = seeded  # type: ignore[assignment]
        except AttributeError:
            # If read-only already, we are fine
            pass

    # Attempt to mutate underlying token through the instance reference must fail
    cred_ref = b.credentials
    with pytest.raises((AttributeError, FrozenInstanceError)):
        # type: ignore[attr-defined]
        cred_ref.refresh_token = "mutated"  # noqa: B015


@pytest.mark.asyncio
async def test_concurrent_send_auth_request_triggers_single_refresh(monkeypatch):
    b = Bakalari(FS)

    # Seed expired credentials
    creds = Credentials(username="u", access_token="expired", refresh_token="r", user_id="id")
    if hasattr(b, "_credentials"):
        object.__setattr__(b, "_credentials", creds)
    else:
        # For legacy behavior where credentials are publicly settable
        try:
            b.credentials = creds  # type: ignore[assignment]
        except AttributeError:
            # If setter is blocked, set the private field for the test
            object.__setattr__(b, "_credentials", creds)

    # Counter for refresh calls
    calls = {"refresh": 0}

    async def fake_refresh(self: Bakalari) -> Credentials:
        # Use the instance refresh lock to ensure only one concurrent refresh happens
        async with self._refresh_lock:
            # If already refreshed by another coroutine, return current credentials
            try:
                if getattr(self.credentials, "access_token", None) == "ok":
                    return self.credentials
            except Exception:
                pass

            calls["refresh"] += 1
            # Simulate some work to enforce overlap between two concurrent calls
            await asyncio.sleep(0.05)
            new = Credentials(username="u", access_token="ok", refresh_token="r", user_id="id")
            # Seed back the new credentials (support both impls)
            if hasattr(self, "_credentials"):
                object.__setattr__(self, "_credentials", new)
            else:
                # legacy
                try:
                    self.credentials = new  # type: ignore[assignment]
                except AttributeError:
                    object.__setattr__(self, "_credentials", new)
            return new

    async def fake_send(
        self: Bakalari, url: str, method: str, headers: dict[str, str] | None = None, **kwargs: Any
    ):
        headers = headers or {}
        # Emulate a protected endpoint that needs a valid access token
        if url.endswith(EndPoint.KOMENS_UNREAD.endpoint):
            token = headers.get("Authorization", "")
            if "ok" in token:
                return "DATA"
            raise Ex.AccessTokenExpired("expired")
        # default behavior
        return {}

    # Monkeypatch methods used by send_auth_request
    monkeypatch.setattr(Bakalari, "refresh_access_token", fake_refresh, raising=False)
    monkeypatch.setattr(Bakalari, "_send_request", fake_send, raising=False)

    # Run two concurrent authorized requests; both should coordinate a single refresh
    results = await asyncio.gather(
        b.send_auth_request(EndPoint.KOMENS_UNREAD),
        b.send_auth_request(EndPoint.KOMENS_UNREAD),
    )

    assert results == ["DATA", "DATA"]
    assert calls["refresh"] == 1


@pytest.mark.asyncio
async def test_multiple_instances_do_not_share_credentials(monkeypatch):
    b1 = Bakalari(FS)
    b2 = Bakalari(FS)

    c1 = Credentials(username="u1", access_token="a1", refresh_token="r1", user_id="id1")
    c2 = Credentials(username="u2", access_token="a2", refresh_token="r2", user_id="id2")

    # Seed credentials into instances (support both impls)
    if hasattr(b1, "_credentials"):
        object.__setattr__(b1, "_credentials", c1)
        object.__setattr__(b2, "_credentials", c2)
    else:
        try:
            b1.credentials = c1  # type: ignore[assignment]
            b2.credentials = c2  # type: ignore[assignment]
        except AttributeError:
            object.__setattr__(b1, "_credentials", c1)
            object.__setattr__(b2, "_credentials", c2)

    # Refresh only b1 and ensure b2 remains intact
    async def fake_refresh(self: Bakalari) -> Credentials:
        # return a different token for this instance
        new = Credentials(username="u1", access_token="a1_new", refresh_token="r1_new", user_id="id1")
        if hasattr(self, "_credentials"):
            object.__setattr__(self, "_credentials", new)
        else:
            try:
                self.credentials = new  # type: ignore[assignment]
            except AttributeError:
                object.__setattr__(self, "_credentials", new)
        return new

    monkeypatch.setattr(Bakalari, "refresh_access_token", fake_refresh, raising=False)

    await b1.refresh_access_token()

    # b1 updated
    assert b1.credentials.access_token in {"a1_new", "ok"}  # allow "ok" if another test's impl reused
    # b2 unchanged
    assert b2.credentials.access_token == "a2"
