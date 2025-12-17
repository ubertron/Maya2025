from __future__ import annotations

from abc import ABC, abstractmethod

from maya_tools.utilities.architools.arch_data import ArchData


class ArchCreator(ABC):
    """Base metaclass for architools creator class."""

    def __init__(self):
        self._data = None

    @property
    def data(self) -> ArchData | None:
        """Construction data for the asset."""
        try:
            return self._data
        except AttributeError:
            return None

    @data.setter
    def data(self, value: ArchData | None):
        self._data = value

    @abstractmethod
    def validate(self):
        """Validates selected input and generates ArchData."""
        pass

    @abstractmethod
    def create(self):
        """Creates the asset from the ArchData values."""
        pass