"""Bakalari API logger."""

import logging
import logging.handlers


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

    _format = f"%(asctime)s - %(name)s - %(levelname)s - %(threadName)s:\n   {cyan}Message: %(message)s\n{magenta}@(%(filename)s:%(lineno)d)"
    dateformat = "%d/%m/%Y %H:%M:%S"

    FORMATS = {
        logging.DEBUG: grey + _format + reset,
        logging.INFO: green + _format + reset,
        logging.WARNING: yellow + _format + reset,
        logging.ERROR: bold_red + _format + reset,
        logging.CRITICAL: bold_red + _format + reset,
    }

    def format(self, record):
        """Format string."""

        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt=self.dateformat)
        return formatter.format(record)


class api_logger:
    """API logger."""

    @classmethod
    def create(cls, name, loglevel: int = logging.ERROR):
        """Create API logger."""
        instance = cls(name, loglevel)
        return instance.logger

    def __init__(self, name, loglevel: int = logging.ERROR):
        """Create API logger."""
        self.name = name
        self.loglevel = loglevel

        self.console_formatter = CustomFormatter()
        self.logger = logging.getLogger(name)

        # Reuse existing stream handler if present; avoid duplicates
        stream_handler = None
        for h in self.logger.handlers:
            if isinstance(h, logging.StreamHandler):
                stream_handler = h
                break
        if stream_handler is None:
            stream_handler = logging.StreamHandler()
            self.logger.addHandler(stream_handler)

        # Expose handler on instance
        self.console_logger = stream_handler

        # Always use our formatter and let logger level control filtering
        stream_handler.setFormatter(self.console_formatter)
        stream_handler.setLevel(logging.NOTSET)

        # Prefer the most verbose (lowest) level across repeated initializations
        current_level = self.logger.level
        if current_level == logging.NOTSET:
            new_level = loglevel
        else:
            new_level = min(current_level, loglevel)
        self.logger.setLevel(new_level)

    def get(self):
        "Get."
        return self.logger
