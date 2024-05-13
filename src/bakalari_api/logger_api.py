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

    format = f"%(asctime)s - %(name)s - %(levelname)s - %(threadName)s:\n   {cyan}Message: %(message)s\n{magenta}@(%(filename)s:%(lineno)d)"
    dateformat = "%d/%m/%Y %H:%M:%S"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: bold_red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        """Format string."""

        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt=self.dateformat)
        return formatter.format(record)


class api_logger:
    """API logger."""

    def __init__(self, name, loglevel: logging = logging.ERROR):
        """Create API logger."""
        self.name = name
        self.loglevel = loglevel

        self.console_formatter = CustomFormatter()
        self.console_logger = logging.StreamHandler()
        self.console_logger.setFormatter(self.console_formatter)

        self.logger = logging.getLogger(name)
        if self.logger.handlers:
            self.logger.handlers.pop()
        self.logger.addHandler(self.console_logger)
        self.logger.setLevel(self.loglevel)

    def get(self):
        "Get."
        return self.logger
