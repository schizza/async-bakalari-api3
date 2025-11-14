"""Tests for async_bakalari_api.__main__."""

import runpy


def test_main_module_invokes_demo_main(monkeypatch):
    """Execute async_bakalari_api.__main__ and verify that bakalari_demo.main() is called.

    We monkeypatch the real demo main to avoid running the actual demo logic.
    """

    calls = {"count": 0}

    def fake_main():
        calls["count"] += 1

    # Patch the entrypoint the way __main__ imports it: `from async_bakalari_api.bakalari_demo import main`
    monkeypatch.setattr(
        "async_bakalari_api.bakalari_demo.main", fake_main, raising=False
    )

    # Execute the package __main__ as a script
    runpy.run_module("async_bakalari_api.__main__", run_name="__main__")

    assert calls["count"] == 1
