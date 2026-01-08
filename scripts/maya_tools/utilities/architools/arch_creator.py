"""
arch_creator.py

Populate the create function:
# 1) initialize arch data
self.initialize_arch_data()

# 2) create curves from the arch data
curves = [curve_utils.create_curve_from_points(points=self.data.profile_points, close=False, name="curve0", color=CURVE_COLOR)]

# 3) create the geometry
cmds.nurbsToPolygonsPref(polyType=1, format=3)
geometry, loft = cmds.loft(*curves, degree=1, polygon=1, name="arch_node")

# 4) add the attributes

# 5) texture
if auto_texture:
    material_utils.auto_texture(transform=geometry)

# 6) cleanup
"""

from __future__ import annotations

import logging

from abc import ABC, abstractmethod
from maya import cmds

from core.core_enums import Side
from core.logging_utils import get_logger
from core.point_classes import Point3
from maya_tools import node_utils
from maya_tools.utilities.architools.arch_data import ArchData
from maya_tools.utilities.boxy import boxy

LOGGER = get_logger(name=__name__, level=logging.INFO)


class ArchCreator(ABC):
    """Base metaclass for architools creator class."""

    def __init__(self, auto_texture: bool = False):
        self.auto_texture = auto_texture
        self.data = None
        self.boxy_node = None
        self._get_boxy_data()

    def _get_boxy_data(self):
        """Get the boxy data."""
        selection = [x for x in node_utils.get_selected_transforms(full_path=True) if node_utils.is_boxy(x)]
        assert len(selection) == 1, "Select a boxy item"
        self.boxy_node = boxy.Boxy().create(pivot=Side.bottom, inherit_rotations=True)[0]
        LOGGER.debug(f"Size: {self.size}")
        LOGGER.debug(f"Rotation: {self.rotation}")

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

    @property
    def rotation(self) -> Point3:
        return node_utils.get_rotation(self.boxy_node)

    @property
    def size(self) -> Point3 | None:
        return node_utils.get_size(node=self.boxy_node, inherit_rotations=True)

    @property
    def translation(self) -> Point3:
        return node_utils.get_translation(self.boxy_node)

    @abstractmethod
    def initialize_arch_data(self):
        """Generate ArchData."""
        pass

    @abstractmethod
    def create(self):
        """Creates the asset from the ArchData values."""
        pass