"""Tests for async_bakalari_api.first_login."""

from async_bakalari_api import first_login as fl
import pytest


@pytest.mark.asyncio
async def test_first_login_function_runs_with_stubs(monkeypatch):
    """Tests that async_bakalari_api.first_login.first_login() runs with stubs.

    Execute async_bakalari_api.first_login.first_login() while stubbing I/O and network.

    - Stub Schools.load_from_file to avoid filesystem access.
    - Stub Schools.get_url to return a fake server URL.
    - Stub Bakalari to avoid real network/API calls and record parameters.

    This verifies that the code path in the module executes without raising and with
    expected arguments being passed through.
    """

    calls: dict[str, object] = {}
    created: dict[str, object] = {}

    class FakeSchools:
        def load_from_file(self, path: str):
            calls["load"] = path
            return self

        def get_url(self, name: str) -> str:
            calls["get_url"] = name
            return "http://fake"

    class FakeBakalari:
        def __init__(
            self,
            server: str | None,
            auto_cache_credentials: bool,
            cache_filename: str | None,
        ):
            created["server"] = server
            created["auto_cache_credentials"] = auto_cache_credentials
            created["cache_filename"] = cache_filename

        async def first_login(self, username: str, password: str):
            created["username"] = username
            created["password"] = password
            # Return a dummy structure to emulate success (original code ignores return value)
            return {"access_token": "a", "refresh_token": "r"}

    # Monkeypatch symbols as imported in the module under test
    monkeypatch.setattr(fl, "Schools", FakeSchools, raising=False)
    monkeypatch.setattr(fl, "Bakalari", FakeBakalari, raising=False)

    # Run the function under test; it doesn't return anything in the real code.
    result = await fl.first_login()
    assert result is None or isinstance(result, dict)

    # Verify I/O paths and arguments were exercised as expected
    assert calls.get("load") == "schools_data.json"
    assert calls.get("get_url") == "Your school"

    assert created.get("server") == "http://fake"
    assert created.get("auto_cache_credentials") is True
    assert created.get("cache_filename") == "new_data.json"
    assert created.get("username") == "username"
    assert created.get("password") == "password"
