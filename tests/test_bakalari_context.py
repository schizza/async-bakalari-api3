"""Tests for async_bakalari_api.bakalari_context."""

from async_bakalari_api.bakalari import Bakalari
import pytest


class _FakeClient:
    def __init__(self, suppress: bool = False):
        """Initialize the fake client."""
        self.entered = False
        self.exited = False
        self.last_exc = None
        self._suppress = suppress

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.exited = True
        self.last_exc = (exc_type, exc, tb)
        return self._suppress


@pytest.mark.asyncio
async def test_bakalari_async_context_calls_client_enter_exit():
    """Bakalari async context should call underlying ApiClient __aenter__/__aexit__ and return self."""
    b = Bakalari()
    fake = _FakeClient(suppress=False)
    # Replace internal client with our fake to observe calls
    object.__setattr__(b, "_api_client", fake)

    async with b as ctx:
        assert ctx is b
        assert fake.entered is True
        # While inside context, __aexit__ not yet called
        assert fake.exited is False

    # After context, __aexit__ must be called with no exception
    assert fake.exited is True
    assert fake.last_exc == (None, None, None)


@pytest.mark.asyncio
async def test_bakalari_async_context_passes_exception_to_client_and_is_propagated():
    """Bakalari async context should pass exceptions to the client __aexit__ and propagate them."""
    b = Bakalari()
    fake = _FakeClient(suppress=True)
    object.__setattr__(b, "_api_client", fake)

    # Exception is propagated because Bakalari.__aexit__ does not suppress it
    with pytest.raises(RuntimeError):
        async with b as ctx:
            assert ctx is b
            raise RuntimeError("boom")

    # Verify __aexit__ received the exception info
    exc_type, exc, tb = fake.last_exc
    assert exc_type is RuntimeError
    assert isinstance(exc, RuntimeError)
    assert tb is not None
