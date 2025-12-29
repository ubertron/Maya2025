"""Boxy helper object.

https://docs.google.com/drawings/d/1-ZBwQI7VJAlBD0MT4IYBoy0yj76_p17w2ZN1HKV80KI
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum, auto

from maya import cmds

from core import color_classes, math_utils
from core.color_classes import RGBColor
from core.core_enums import ComponentType, CustomType, DataType, Side
from core.logging_utils import get_logger
from core.point_classes import Point3, ZERO3, Point3Pair
from maya_tools import attribute_utils, geometry_utils, node_utils
from maya_tools.maya_enums import ObjectType
from maya_tools.node_utils import get_translation
from tests.validators import boxy_validator

DEBUG_MODE = False
DEFAULT_SIZE: float = 100.0
LOGGER = get_logger(__name__, level=logging.DEBUG)


@dataclass
class BoxyData:
    position: Point3
    rotation: Point3
    size: Point3
    pivot: Side
    color: RGBColor
    name: str

    @property
    def dictionary(self) -> dict:
        return {
            "position": self.position.values,
            "rotation": self.rotation.values,
            "size": self.size.values,
            "pivot": self.pivot.name,
            "color": self.color.values,
            "name": self.name,
        }


class ElementType(Enum):
    boxy = auto()
    curve = auto()
    cv = auto()
    invalid = auto()
    locator = auto()
    mesh = auto()
    vertex = auto()


class Boxy:
    """Create a boxy

    Y-sensitive bounds based box that defines a space
    Use to define base centered bounding boxes and as a placeholder for objects
    """

    def __init__(self):
        self.box = None
        self.size = Point3(*[DEFAULT_SIZE for _ in range(3)])
        self.position = ZERO3
        self.rotation_y = 0.0
        self.pivot = Side.center
        self.color = color_classes.DEEP_GREEN
        self.selected_transforms = None
        self.original_selection = cmds.ls(selection=True, flatten=True)
        self._init_selection()
        self._init_element_type_dict()
        self.selected_transforms = [x for x in node_utils.get_selected_transforms() if not node_utils.is_boxy(x)]

    def __repr__(self):
        """Preview the analysis prior to creation."""
        return (
            f"Element types: {', '.join(x.name for x in self.element_types)}\n"
            f"Transforms: {', '.join(self.selected_transforms)}\n"
            f"Selection: {', '.join(self.selection)}\n"
            f"Position: {self.position}\n"
            f"Rotation: {self.rotation_y}\n"
            f"Size: {self.size}\n"
        )

    def _build(self):
        """Build boxy box."""
        boxy_data = BoxyData(
            position=self.position,
            rotation=Point3(0.0, self.rotation_y, 0.0),
            size=self.size,
            pivot=self.pivot,
            color=color_classes.DEEP_GREEN,
            name="boxy",
        )
        return build(boxy_data=boxy_data)

    def _evaluate_for_multiple_selection(self):
        """Set up boxy attributes for multiple nodes."""
        bounds = node_utils.get_bounds_from_selection(self.selection)
        self.position = {
            Side.bottom: bounds.base_center,
            Side.center: bounds.center,
            Side.top: bounds.top_center,
        }[self.pivot]
        self.size = bounds.size

    def _evaluate_for_single_selection(self, check_rotations: bool):
        """Set up boxy attributes for a single node."""
        self.rotation_y = node_utils.get_rotation(self.selected_transforms[0]).y
        position = get_translation(self.selected_transforms[0])

        # work out the size compensating for rotation
        if self.components_only:
            # get the bounds of locators/verts/cvs
            points = node_utils.get_points_from_selection()
            y_offset = -self.rotation_y if check_rotations else 0.0
            bounds = math_utils.get_bounds_from_points(points=points, y_offset=y_offset, pivot=position)
            self.size = bounds.size
            position_pre_rotation = get_position_from_bounds(bounds=bounds, pivot=self.pivot)
            self.position = math_utils.rotate_point_about_y(
                point=position_pre_rotation, y_rotation=-y_offset, pivot=position)
        else:
            # get the bounds from the transform
            bounds = node_utils.get_bounds(node=self.selected_transforms[0], check_rotations=check_rotations)
            self.size = bounds.size
            self.position = {
                Side.bottom: bounds.base_center,
                Side.center: bounds.center,
                Side.top: bounds.top_center,
            }[self.pivot]

    def _init_selection(self):
        """Initialize the selection. Convert any edges/faces to vertices."""
        sanitized = []
        selection = cmds.ls(selection=True, flatten=True)
        for x in selection:
            if ".e" in x:
                vertices = cmds.ls(cmds.polyListComponentConversion(x, fromEdge=True, toVertex=True), flatten=True)
                sanitized.extend(vertices)
            elif ".f" in x:
                faces = cmds.ls(cmds.polyListComponentConversion(x, fromFace=True, toVertex=True), flatten=True)
                sanitized.extend(faces)
            else:
                sanitized.append(x)
        self.selection = list(set(sanitized))

    @property
    def components_only(self) -> bool:
        """Returns False if any mesh or curve objects in selection
        Returns True if vertices, cvs or locators in selected
        boxys and invalid are ignored
        """
        if ElementType.mesh in self.element_types or ElementType.curve in self.element_types:
            return False
        return next((True for x in (ElementType.vertex, ElementType.cv, ElementType.locator) if x in self.element_types), False)

    @property
    def two_locators_only(self) -> bool:
        """Returns True if there are only two locators selected."""
        return len(self.selection) == 2 and len(self.element_type_dict.get(ElementType.locator, [])) == 2

    @property
    def element_types(self):
        return list(self.element_type_dict.keys())

    def create(self, pivot: Side = Side.center, check_rotations: bool = True) -> str:
        """Evaluate selection."""
        assert pivot in (Side.center, Side.top, Side.bottom), f"Invalid pivot position: {pivot.name}"
        self.pivot = pivot
        if ElementType.boxy in self.element_type_dict:
            for boxy_item in self.element_type_dict[ElementType.boxy]:
                rebuild(node=boxy_item, pivot=pivot, color=self.color)
                self.selection.remove(boxy_item)
        if len(self.selected_transforms) > 1:
            self._evaluate_for_multiple_selection()
        elif len(self.selected_transforms) == 1:
            self._evaluate_for_single_selection(check_rotations=check_rotations)
        if len(self.selected_transforms):
            self._build()

    def _init_element_type_dict(self):
        """Initialize the selection type dict."""
        element_type_dict = {}

        def append_dict_list(_dict, key, value) -> None:
            """Add a value to a list in a dict."""
            if key in _dict:
                _dict[key].append(value)
            else:
                _dict[key]=[value]

        if self.selection:
            for x in self.selection:
                if attribute_utils.get_attribute(node=x, attr="custom_type") == ElementType.boxy.name:
                    append_dict_list(element_type_dict, ElementType.boxy, x)
                elif node_utils.is_locator(x):
                    append_dict_list(_dict=element_type_dict, key=ElementType.locator, value=x)
                elif next((True for c in [".vtx", ".e", ".f"] if c in x), False):
                    append_dict_list(_dict=element_type_dict, key=ElementType.vertex, value=x)
                elif ".cv" in x:
                    append_dict_list(_dict=element_type_dict, key=ElementType.cv, value=x)
                elif node_utils.is_geometry(x):
                    append_dict_list(_dict=element_type_dict, key=ElementType.mesh, value=x)
                elif node_utils.is_nurbs_curve(x):
                    append_dict_list(_dict=element_type_dict, key=ElementType.curve, value=x)
                elif cmds.objectType(x) == ObjectType.nurbsCurve.name:
                    append_dict_list(_dict=element_type_dict, key=ElementType.curve, value=x)
                else:
                    append_dict_list(_dict=element_type_dict, key=ElementType.invalid, value=x)
        self._element_type_dict = element_type_dict

    @property
    def component_mode(self) -> ComponentType:
        return node_utils.get_component_mode()

    @property
    def element_type_dict(self) -> dict:
        return self._element_type_dict

    @property
    def selected_transforms(self) -> list[str]:
        return self._selected_transforms

    @selected_transforms.setter
    def selected_transforms(self, value: list[str]):
        self._selected_transforms = value


def build(boxy_data: BoxyData) -> str:
    """Build boxy box."""
    height_base_line = -1 if boxy_data.pivot is Side.bottom else 1 if boxy_data.pivot is Side.top else 0
    box = cmds.polyCube(
        name=boxy_data.name,
        width=boxy_data.size.x, height=boxy_data.size.y, depth=boxy_data.size.z,
        heightBaseline=height_base_line, constructionHistory=False)[0]
    node_utils.set_translation(nodes=box, value=boxy_data.position, absolute=True)
    node_utils.set_rotation(nodes=box, value=boxy_data.rotation, absolute=True)
    geometry_utils.set_wireframe_color(node=box, color=boxy_data.color, shading=False)
    attribute_utils.add_attribute(
        node=box,
        attr="custom_type",
        data_type=DataType.string,
        read_only=True,
        default_value=CustomType.boxy.name)
    attribute_utils.add_attribute(
        node=box,
        attr="pivot",
        data_type=DataType.string,
        read_only=True,
        default_value=boxy_data.pivot.name)
    attribute_utils.add_compound_attribute(
        node=box,
        parent_attr="size",
        data_type=DataType.float3,
        attrs=["x", "y", "z"],
        default_values=boxy_data.size.values,
        read_only=True)
    return box


def get_position_from_bounds(bounds: Point3Pair, pivot: Side) -> Point3:
    """Get the position of a Boxy object from the bounds."""
    assert pivot in (Side.bottom, Side.top, Side.center), f"Invalid pivot: {pivot}"
    return {
        Side.bottom: bounds.base_center,
        Side.center: bounds.center,
        Side.top: bounds.top_center,
    }[pivot]


def rebuild(node: str, pivot: Side | None = None, color: RGBColor | None = None) -> any:
    """Rebuild a boxy node."""
    result, issues = boxy_validator.test_selected_boxy(node=node)
    if result is False:
        print("Invalid boxy object")
        print("\n".join(issues))
        return False
    pivot = pivot if pivot else Side[attribute_utils.get_attribute(node=node, attr="pivot")]
    rotation = node_utils.get_rotation(node=node)
    bounds: Point3Pair = node_utils.get_bounds(node=node, check_rotations=True)
    position = get_position_from_bounds(bounds=bounds, pivot=pivot)
    cmds.delete(node)
    boxy_data = BoxyData(
        position=position,
        rotation=rotation,
        size=bounds.size,
        pivot=pivot,
        color=color if color else color_classes.DEEP_GREEN,
        name=node
    )
    boxy_object = build(boxy_data=boxy_data)
    print(f"Boxy rebuilt: {boxy_object}")
    return boxy_object
