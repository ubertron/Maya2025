from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Sequence

DEFAULT_LOG_FILE = Path(__file__).parents[1] / "logs" / ".log"

class LogHandler(ABC):
    """Log handler metaclass."""

    def __init__(self, level: Enum, log_format: str):
        self.level = level
        self.log_format = log_format

    @property
    @abstractmethod
    def handler(self) -> logging.Handler:
        pass

    @property
    def formatter(self):
        return logging.Formatter(self.log_format)


class StreamHandler(LogHandler):
    """Stream handler."""

    def __init__(self, level: Enum=logging.DEBUG, log_format: str | None = None):
        if log_format is None:
            log_format = "%(levelname)s: %(funcName)s: %(message)s" if level <= logging.DEBUG else "%(levelname)s: %(message)s"
        super().__init__(level=level, log_format=log_format)

    @property
    def handler(self) -> logging.Handler:
        handler = logging.StreamHandler()
        handler.setLevel(self.level)
        handler.setFormatter(self.formatter)
        return handler


class FileHandler(LogHandler):
    """File handler."""

    def __init__(self, level: Enum=logging.DEBUG, log_format: str="%(asctime)s: %(levelname)s: %(message)s", path: Path = DEFAULT_LOG_FILE):
        super().__init__(level=level, log_format=log_format)
        self.path = path

    @property
    def handler(self) -> logging.Handler:
        handler = logging.FileHandler(self.path)
        handler.setLevel(self.level)
        handler.setFormatter(self.formatter)
        return handler


def get_logger(name: str | None = None, level=logging.INFO,
               handlers: Sequence[LogHandler] | LogHandler | None = None) -> logging.Logger:
    """Create a logger."""
    if handlers is None:
        handlers = StreamHandler(level=level)
    logger = logging.getLogger(name if name else __name__)
    logger.setLevel(level)
    logger.propagate = False
    for existing_handler in logger.handlers[:]:
        logger.removeHandler(existing_handler)
    if type(handlers) in (FileHandler, StreamHandler):
        logger.addHandler(handlers.handler)
    else:
        for log_handler in handlers:
            logger.addHandler(log_handler.handler)
    return logger


def get_logger_basic(name: str | None = None, level=logging.INFO) -> logging.Logger:
    """Create a basic logger."""
    logger = logging.getLogger(name if name else __name__)
    logger.setLevel(level)
    logger.propagate = False
    return logger


if __name__ == "__main__":
    # my_logger = get_logger(level=logging.DEBUG, handlers=[StreamHandler(level=logging.ERROR), FileHandler(logging.DEBUG)])
    # my_logger = get_logger(level=logging.DEBUG, handlers=(StreamHandler(level=logging.INFO), FileHandler(level=logging.DEBUG)))
    my_logger = get_logger(level=logging.DEBUG)
    my_logger.debug("debug test")
    my_logger.info("info test")
    my_logger.warning("warning test")
    my_logger.exception("exception test")