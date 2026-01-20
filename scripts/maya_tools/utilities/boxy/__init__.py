from __future__ import annotations


class BoxyException(Exception):
    """Exception raised for custom error scenarios."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
