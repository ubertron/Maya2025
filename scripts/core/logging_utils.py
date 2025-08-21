"""Functions to handle logging."""
from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path


def get_stream_handler(logger: logging.Logger) -> logging.Handler | None:
    """Get the stream handler of a logger if it exists."""
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            return handler
    return None


def get_logger(name: str | None = None, log_file: Path | None = None,  # noqa: D103
               level: Enum = logging.INFO,
               log_format: str = "%(message)s") -> logging.Logger:
    """Create an instance of the logger and return it."""
    logger = logging.getLogger(name)
    for handler in logger.handlers[:]:  # Iterate over a slice to avoid modification issues
        logger.removeHandler(handler)
    handler = get_stream_handler(logger=logger)
    if not handler:
        handler = logging.FileHandler(log_file.as_posix()) if log_file \
            else logging.StreamHandler()
        handler.setLevel(level)
    handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(handler)
    return logger