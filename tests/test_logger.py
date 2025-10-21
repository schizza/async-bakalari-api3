import logging

from async_bakalari_api.logger_api import api_logger, CustomFormatter


def test_api_logger_streamhandler_dedup(monkeypatch):

    logger_name = "UNITTEST-LOGGER"
    logger = logging.getLogger(logger_name)

    logger.handlers.clear()
    sh = logging.StreamHandler()
    logger.addHandler(sh)

    log = api_logger(logger_name, logging.INFO)
    inst = log
    assert any(isinstance(h, logging.StreamHandler) for h in inst.logger.handlers)

    assert isinstance(inst.get(), logging.Logger)


def test_api_logger_level_prefers_verbose(monkeypatch):
    name = "BAK-VRB"
    logg1 = api_logger(name, logging.DEBUG)
    logg2 = api_logger(name, logging.ERROR)
    assert logg2.logger.level == logging.DEBUG


def test_formatter_formats_each_level():
    # CustomFormatter řádně vrací barevné řetězce všech úrovní
    formatter = CustomFormatter()
    record = logging.LogRecord(
        "foo", logging.DEBUG, "dummy", 1, "Debug msg", None, None
    )
    debug_line = formatter.format(record)
    assert "Debug msg" in debug_line

    record = logging.LogRecord("foo", logging.INFO, "dummy", 2, "Info msg", None, None)
    info_line = formatter.format(record)
    assert "Info msg" in info_line

    record = logging.LogRecord(
        "foo", logging.WARNING, "dummy", 3, "Warning msg", None, None
    )
    warn_line = formatter.format(record)
    assert "Warning msg" in warn_line

    record = logging.LogRecord(
        "foo", logging.ERROR, "dummy", 4, "Error msg", None, None
    )
    error_line = formatter.format(record)
    assert "Error msg" in error_line

    record = logging.LogRecord(
        "foo", logging.CRITICAL, "dummy", 5, "Critical msg", None, None
    )
    crit_line = formatter.format(record)
    assert "Critical msg" in crit_line


def test_api_logger_create_classmethod():
    logger_name = "BAK-CLASS"
    logger = api_logger.create(logger_name, loglevel=logging.INFO)
    assert isinstance(logger, logging.Logger)
