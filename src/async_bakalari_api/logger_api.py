"""Bakalari API logger."""

import logging
import os


class CustomFormatter(logging.Formatter):
    """Custom formater for module."""

    black = "\u001b[30m"
    yellow = "\u001b[33m"
    red = "\u001b[31m"
    bold_red = "\x1b[31;1m"
    reset = "\u001b[0m"
    green = "\u001b[32m"
    grey = "\u001b[30m"
    blue = "\u001b[34m"
    magenta = "\u001b[35m"
    cyan = "\u001b[36m"
    white = "\u001b[37m"

    _format = (
        f"%(asctime)s - %(name)s - %(levelname)s - %(threadName)s:\n"
        f"   {cyan}Message: %(message)s\n"
        f"   {blue}event=%(event)s method=%(method)s url=%(url)s "
        f"latency=%(latency_ms)s ms retries=%(retries)s status=%(status)s error=%(error)s\n"
        f"{magenta}@(%(filename)s:%(lineno)d)"
    )
    dateformat = "%d/%m/%Y %H:%M:%S"

    FORMATS = {
        logging.DEBUG: cyan + _format + reset,
        logging.INFO: green + _format + reset,
        logging.WARNING: yellow + _format + reset,
        logging.ERROR: bold_red + _format + reset,
        logging.CRITICAL: bold_red + _format + reset,
    }

    def format(self, record):
        """Format string."""

        for key, default in (
            ("event", "-"),
            ("url", "-"),
            ("method", "-"),
            ("latency_ms", "-"),
            ("retries", "-"),
            ("status", "-"),
            ("error", "-"),
        ):
            if not hasattr(record, key):
                setattr(record, key, default)

        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt=self.dateformat)
        return formatter.format(record)


def _parse_level(level: int | str | None, default: int = logging.ERROR) -> int:
    """Parse log level."""

    if isinstance(level, int):
        return level
    if isinstance(level, str):
        return getattr(logging, level.upper(), default)

    env = os.getenv("BAKALARI_LOG_LEVEL")
    if env:
        return getattr(logging, env.upper(), default)
    return default


def configure_logging(level: int | str | None) -> logging.Logger:
    """Configure logging."""

    pkg_root = logging.getLogger("async_bakalari_api")
    pkg_root.propagate = False
    pkg_root.setLevel(_parse_level(level))

    handler = None
    for h in pkg_root.handlers:
        if isinstance(h, logging.StreamHandler):
            handler = h
            break
    if handler is None:
        handler = logging.StreamHandler()
        pkg_root.addHandler(handler)

    handler.setFormatter(CustomFormatter())
    handler.setLevel(logging.NOTSET)
    handler.setFormatter(CustomFormatter())

    return pkg_root


class api_logger:
    """API logger."""

    @classmethod
    def create(cls, name, loglevel: int = logging.ERROR):
        """Create API logger."""
        instance = cls(name, loglevel)
        return instance.logger

    def __init__(self, name, loglevel: int = logging.ERROR):
        """Create API logger."""

        if name == "async_bakalari_api":
            self.logger = configure_logging(loglevel)
            return

        self.logger = logging.getLogger(name)
        if self.logger.level == logging.NOTSET and loglevel is not None:
            self.logger.setLevel(loglevel)

    def get(self):
        """Get the logger instance."""
        return self.logger
