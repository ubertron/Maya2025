"""
arch_creator.py

Populate the create function:
# 1) initialize arch data
self.initialize_arch_data()

# 2) create curves from the arch data
curves = [curve_utils.create_curve_from_points(
            points=self.data.profile_points, close=False, name=f"{self.custom_type.name}_curve1", color=CURVE_COLOR)]

# 3) create the geometry
cmds.nurbsToPolygonsPref(polyType=1, format=3)
geometry, loft = cmds.loft(*curves, degree=1, polygon=1, name=self.custom_type.name)

# 4) add the attributes
attribute_utils.add_attribute(
    node=geometry, attr="custom_type", data_type=DataType.string, lock=True, default_value=self.custom_type.name)

# 5) texture/wireframe color
geometry_utils.set_wireframe_color(node=geometry, color=color_classes.DEEP_GREEN)
if auto_texture:
    material_utils.auto_texture(transform=geometry)

# 6) cleanup
cmds.polySoftEdge(geometry, angle=0)
node_utils.pivot_to_base(node=geometry)
cmds.delete(geometry, constructionHistory=True)
cmds.delete(curves, self.boxy_node)
node_utils.set_translation(geometry, value=self.data.translation)
node_utils.set_rotation(geometry, value=Point3(0, self.data.y_rotation, 0))
cmds.select(clear=True)
cmds.select(geometry)
return geometry
"""

from __future__ import annotations

import logging

from abc import ABC, abstractmethod
from maya import cmds

from core.core_enums import CustomType, Side
from core.logging_utils import get_logger
from core.point_classes import Point3
from maya_tools import node_utils
from maya_tools.utilities.architools.data.arch_data import ArchData
from maya_tools.utilities.architools import arch_utils
from maya_tools.utilities.boxy import boxy_utils

LOGGER = get_logger(name=__name__, level=logging.INFO)


class ArchCreator(ABC):
    """Base metaclass for architools creator class."""

    def __init__(self, custom_type: CustomType, auto_texture: bool = False):
        self.custom_type = custom_type
        self.auto_texture = auto_texture
        self.data = None
        self.boxy_node = None
        self._get_boxy_node()

    def _get_boxy_node(self):
        """Get the boxy data."""
        selection = arch_utils.get_custom_type(custom_type=CustomType.boxy, selected=True)
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
        """Generate ArchData.

        - Override to set up self.data with ArchData
        """
        pass

    @abstractmethod
    def create(self):
        """Creates the asset from the ArchData values.

        - Override for creation function
        """
        pass