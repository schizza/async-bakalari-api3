"""Tests for async_bakalari_api.logger_api."""

import io
import logging

from async_bakalari_api.logger_api import CustomFormatter, api_logger, configure_logging
import pytest


def _clear_pkg_logger():
    """Remove handlers from the package root logger to avoid cross-test interference."""
    pkg = logging.getLogger("async_bakalari_api")
    for h in list(pkg.handlers):
        pkg.removeHandler(h)
    pkg.setLevel(logging.NOTSET)
    pkg.propagate = True


def test_custom_formatter_injects_defaults_for_missing_extra_keys():
    """CustomFormatter must not raise KeyError and must inject '-' defaults for extra fields."""
    logger_name = "UNITTEST-CF"
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(CustomFormatter())

    logger = logging.getLogger(logger_name)
    # Isolate this logger from any global/root handlers
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # No "extra" provided; formatter must inject defaults and render them
    logger.info("Hello formatter")

    out = buf.getvalue()
    assert "Message: Hello formatter" in out
    # Defaults present
    for key in ("event", "url", "method", "latency", "retries", "status", "error"):
        assert f"{key}=-" in out


def test_configure_logging_sets_handler_level_and_is_idempotent():
    """configure_logging should attach a single StreamHandler with CustomFormatter and respect level."""
    _clear_pkg_logger()

    # First call: INFO
    pkg = configure_logging("INFO")
    assert pkg.name == "async_bakalari_api"
    assert pkg.propagate is False
    assert pkg.level == logging.INFO

    shandlers = [h for h in pkg.handlers if isinstance(h, logging.StreamHandler)]
    assert len(shandlers) == 1
    assert isinstance(shandlers[0].formatter, CustomFormatter)
    # Handler should let logger filter the records
    assert shandlers[0].level == logging.NOTSET

    # Second call: DEBUG – must not create a second handler, but should update level
    pkg2 = configure_logging("DEBUG")
    assert pkg2 is pkg
    shandlers2 = [h for h in pkg2.handlers if isinstance(h, logging.StreamHandler)]
    assert len(shandlers2) == 1
    assert pkg2.level == logging.DEBUG

    _clear_pkg_logger()


def test_configure_logging_uses_env_level_when_level_is_none(
    monkeypatch: pytest.MonkeyPatch,
):
    """If level=None, configure_logging should parse BAKALARI_LOG_LEVEL from environment."""
    _clear_pkg_logger()
    monkeypatch.setenv("BAKALARI_LOG_LEVEL", "warning")

    pkg = configure_logging(None)
    assert pkg.level == logging.WARNING

    # Clean up env and handlers
    monkeypatch.delenv("BAKALARI_LOG_LEVEL", raising=False)
    _clear_pkg_logger()


def test_api_logger_root_uses_configure_logging_and_custom_formatter():
    """api_logger for 'async_bakalari_api' should behave like configure_logging."""
    _clear_pkg_logger()

    inst = api_logger("async_bakalari_api", logging.ERROR)
    log = inst.get()
    assert log.name == "async_bakalari_api"
    assert log.level == logging.ERROR
    assert log.propagate is False

    shandlers = [h for h in log.handlers if isinstance(h, logging.StreamHandler)]
    assert len(shandlers) == 1
    assert isinstance(shandlers[0].formatter, CustomFormatter)

    _clear_pkg_logger()


def test_api_logger_non_root_sets_level_only_if_notset():
    """api_logger for non-root names sets level only when current is NOTSET."""
    # Case 1: Logger already has a level -> must remain unchanged
    name1 = "UNITTEST-LOGGER-SET"
    logger1 = logging.getLogger(name1)
    logger1.handlers.clear()
    logger1.setLevel(logging.WARNING)

    inst1 = api_logger(name1, logging.DEBUG)
    log1 = inst1.get()
    assert log1 is logger1
    assert log1.level == logging.WARNING  # unchanged

    # Case 2: Logger level NOTSET -> should be set to provided loglevel
    name2 = "UNITTEST-LOGGER-NOTSET"
    logger2 = logging.getLogger(name2)
    logger2.handlers.clear()
    logger2.setLevel(logging.NOTSET)

    inst2 = api_logger(name2, logging.INFO)
    log2 = inst2.get()
    assert log2 is logger2
    assert log2.level == logging.INFO


def test_configure_logging_idempotent_overrides_formatter_and_preserves_notset():
    """Second call to configure_logging should reset handler formatter and keep NOTSET level."""
    _clear_pkg_logger()
    # First configure
    pkg = configure_logging("INFO")
    # Grab single stream handler
    shandlers = [h for h in pkg.handlers if isinstance(h, logging.StreamHandler)]
    assert len(shandlers) == 1
    h = shandlers[0]
    # Manually override formatter and level to ensure second call actually resets them
    h.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
    h.setLevel(logging.WARNING)

    # Second configure with different level; must not add handler, but must reset formatter and level
    pkg2 = configure_logging("DEBUG")
    assert pkg2 is pkg

    sh2 = [x for x in pkg2.handlers if isinstance(x, logging.StreamHandler)]
    assert len(sh2) == 1
    h2 = sh2[0]

    # Level must be set back to NOTSET so logger filters records
    assert h2.level == logging.NOTSET
    # Formatter must be our CustomFormatter again (proves setFormatter ran)
    assert isinstance(h2.formatter, CustomFormatter)
    # And logger level changed as requested
    assert pkg2.level == logging.DEBUG
