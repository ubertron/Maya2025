"""Boxy helper object."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum, auto

from maya import cmds

from core import color_classes, math_utils
from core.color_classes import RGBColor
from core.core_enums import ComponentType, CustomType, DataType, Side, Axis
from core.logging_utils import get_logger
from core.point_classes import Point3, ZERO3, Point3Pair
from maya_tools import attribute_utils, node_utils
from maya_tools.geometry.bounds import Bounds
from maya_tools.geometry import geometry_utils, component_utils, bounds_utils
from maya_tools.maya_enums import ObjectType
from maya_tools.node_utils import get_translation
from maya_tools.utilities.boxy import BoxyException
from maya_tools.utilities.boxy import boxy_node
from tests.validators import boxy_validator

DEBUG_MODE = False
DEFAULT_SIZE: float = 100.0
LOGGER = get_logger(__name__, level=logging.DEBUG)


@dataclass
class BoxyData:
    bounds: Bounds
    pivot: Side
    color: RGBColor
    name: str

    @property
    def dictionary(self) -> dict:
        return {
            "position": self.bounds.position.values,
            "pivot position": self.pivot_position.values,
            "rotation": self.rotation.values,
            "size": self.size.values,
            "pivot": self.pivot.name,
            "color": self.color.values,
            "name": self.name,
        }

    @property
    def center(self) -> Point3:
        """Center of the Boxy node."""
        return self.bounds.position

    @property
    def pivot_position(self) -> Point3:
        """Position of pivot, based on pivot side."""
        return {
            Side.bottom: self.bounds.base_center,
            Side.center: self.bounds.position,
            Side.top: self.bounds.top_center,
        }[self.pivot]


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

    Use to define base centered bounding boxes and as a placeholder for objects
    """

    def __init__(self, color: RGBColor = color_classes.DEEP_GREEN):
        self.box = None
        self.size = Point3(*[DEFAULT_SIZE for _ in range(3)])
        self.position = ZERO3
        self.rotation = ZERO3
        self.pivot = Side.center
        self.color = color
        self.original_selection = cmds.ls(selection=True, flatten=True)
        self._init_selection()
        self._init_element_type_dict()
        self.all_selected_transforms = node_utils.get_selected_transforms()
        self.selected_transforms = [x for x in self.all_selected_transforms if not node_utils.is_boxy(x)]

    def __repr__(self):
        """Preview the analysis prior to creation."""
        return (
            f"Element types: {', '.join(x.name for x in self.element_types)}\n"
            f"Transforms: {', '.join(self.selected_transforms)}\n"
            f"Selection: {', '.join(self.selection)}\n"
            f"Position: {self.position}\n"
            f"Rotation: {self.rotation}\n"
            f"Size: {self.size}\n"
        )

    def _build(self, inherit_rotations: bool = True):
        """Build boxy box."""
        component_selection = self.component_selection
        LOGGER.debug(f"DEBUG Boxy._build:")
        LOGGER.debug(f"  inherit_rotations: {inherit_rotations}")
        LOGGER.debug(f"  component_selection: {component_selection}")
        if inherit_rotations and component_selection:
            # Look for a cuboid
            bounds = bounds_utils.get_cuboid(geometry=component_selection)
            LOGGER.debug(f"  get_cuboid returned: {bounds}")
            # If no cuboid, get the bounds using the rotation
            if not bounds:
                bounds = bounds_utils.get_bounds(geometry=self.component_selection, inherit_rotations=True)
                LOGGER.debug(f"  get_bounds returned: {bounds}")
        else:
            bounds = Bounds(size=self.size, position=self.position, rotation=self.rotation)
        LOGGER.debug(f"  FINAL bounds for boxy_data:")
        LOGGER.debug(f"    size: {bounds.size}")
        LOGGER.debug(f"    position: {bounds.position}")
        LOGGER.debug(f"    rotation: {bounds.rotation}")
        boxy_data = BoxyData(
            bounds=bounds,
            pivot=self.pivot,
            color=self.color,
            name="boxy"
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

    def _evaluate_for_single_selection(self, inherit_rotations: bool):
        """Set up boxy attributes for a single node."""
        LOGGER.debug(f">>> {self.selected_transforms[0]}")
        self.rotation_y = node_utils.get_rotation(self.selected_transforms[0]).y
        position = get_translation(self.selected_transforms[0])
        # work out the size compensating for rotation
        if self.components_only:
            # get the bounds of locators/verts/cvs
            points = node_utils.get_points_from_selection()
            y_offset = -self.rotation_y if inherit_rotations else 0.0
            bounds = math_utils.get_minimum_maximum_from_points(points=points, y_offset=y_offset, pivot=position)
            self.size = bounds.size
            position_pre_rotation = get_position_from_bounds(bounds=bounds, pivot=self.pivot)
            self.position = math_utils.rotate_point_about_y(
                point=position_pre_rotation, y_rotation=-y_offset, pivot=position)
        else:
            # get the bounds from the transform
            bounds = node_utils.get_min_max_points(node=self.selected_transforms[0],
                                                   inherit_rotations=inherit_rotations)
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
        return next(
            (True for x in (ElementType.vertex, ElementType.cv, ElementType.locator) if x in self.element_types), False)

    @property
    def component_selection(self) -> list[component_utils.Component]:
        return component_utils.components_from_selection(selection=self.selection)

    @property
    def element_types(self):
        return list(self.element_type_dict.keys())

    @property
    def element_type_dict(self) -> dict:
        return self._element_type_dict

    @property
    def selected_transforms(self) -> list[str]:
        return self._selected_transforms

    @selected_transforms.setter
    def selected_transforms(self, value: list[str]):
        self._selected_transforms = value

    @property
    def two_locators_only(self) -> bool:
        """Returns True if there are only two locators selected."""
        return len(self.selection) == 2 and len(self.element_type_dict.get(ElementType.locator, [])) == 2

    def create(self, pivot: Side = Side.center, inherit_rotations: bool = True,
               default_size: float = 10.0) -> tuple[list[str], list[BoxyException]]:
        """Evaluate selection."""
        assert pivot in (Side.center, Side.top, Side.bottom), f"Invalid pivot position: {pivot.name}"
        exceptions = []
        self.pivot = pivot
        self.size = Point3(default_size, default_size, default_size)
        if ElementType.boxy in self.element_type_dict:
            for boxy_item in self.element_type_dict[ElementType.boxy]:
                result = rebuild(node=boxy_item, pivot=pivot, color=self.color)
                if isinstance(result, BoxyException):
                    exceptions.append(result)
                else:
                    self.selection.remove(boxy_item)
        if len(self.selected_transforms) > 1:
            self._evaluate_for_multiple_selection()
        elif len(self.selected_transforms) == 1:
            self._evaluate_for_single_selection(inherit_rotations=inherit_rotations)

        # if only boxy items are selected, don't build because we've handled them already
        boxy_items = self.element_type_dict.get(ElementType.boxy, [])
        num_boxy_items = len(boxy_items)
        if not (num_boxy_items and num_boxy_items == len(self.all_selected_transforms)):
            boxy_items.append(self._build(inherit_rotations=inherit_rotations))

        return boxy_items, exceptions

    @staticmethod
    def append_dict_list(_dict, key, value) -> None:
        """Add a value to a list in a dict."""
        if key in _dict:
            _dict[key].append(value)
        else:
            _dict[key] = [value]

    def _init_element_type_dict(self):
        """Initialize the selection type dict."""
        element_type_dict = {}

        if self.selection:
            for x in self.selection:
                if node_utils.is_boxy(x):
                    self.append_dict_list(element_type_dict, ElementType.boxy, x)
                elif node_utils.is_locator(x):
                    self.append_dict_list(_dict=element_type_dict, key=ElementType.locator, value=x)
                elif next((True for c in [".vtx", ".e", ".f"] if c in x), False):
                    self.append_dict_list(_dict=element_type_dict, key=ElementType.vertex, value=x)
                elif ".cv" in x:
                    self.append_dict_list(_dict=element_type_dict, key=ElementType.cv, value=x)
                elif node_utils.is_geometry(x):
                    self.append_dict_list(_dict=element_type_dict, key=ElementType.mesh, value=x)
                elif node_utils.is_nurbs_curve(x):
                    self.append_dict_list(_dict=element_type_dict, key=ElementType.curve, value=x)
                else:
                    append_dict_list(_dict=element_type_dict, key=ElementType.invalid, value=x)
        self._element_type_dict = element_type_dict


def build(boxy_data: BoxyData) -> str:
    """Build boxy object using custom DAG node."""
    return boxy_node.build(boxy_data=boxy_data)


def convert_boxy_to_poly_cube(node: str) -> str | BoxyException:
    """Convert a boxy node to a poly-cube."""
    result = rebuild(node=node)
    if isinstance(result, BoxyException):
        return result
    boxy_data: BoxyData = get_boxy_data(node=result)
    baseline = {
        Side.bottom: -1,
        Side.center: 0,
        Side.top: 1,
    }[boxy_data.pivot]
    cube = geometry_utils.create_cube(size=boxy_data.bounds.size, position=boxy_data.pivot_position, baseline=baseline)
    node_utils.set_rotation(nodes=cube, value=boxy_data.bounds.rotation)
    cmds.delete(node)
    return cube


def convert_poly_cube_to_boxy(node: str, color: RGBColor = color_classes.DEEP_GREEN) -> str:
    """Convert a poly-cube to a boxy node."""
    shape = node_utils.get_shape_from_transform(node=node)
    poly_cube_node = cmds.listConnections(f"{shape}.inMesh")[0]
    baseline = cmds.getAttr(f"{poly_cube_node}.heightBaseline")
    if baseline in (-1.0, 0.0, 1.0):
        pivot = {
            -1.0: Side.bottom,
            0.0: Side.center,
            1.0: Side.top,
        }[baseline]
        # Try CuboidFinder first (handles rotated faces), fall back to BoundsFinder
        bounds: Bounds = bounds_utils.get_cuboid(geometry=node)
        if not bounds:
            bounds = bounds_utils.get_bounds(geometry=node, inherit_rotations=True)
        boxy_data = BoxyData(
            bounds=bounds,
            pivot=pivot,
            color=color,
            name="boxy"
        )
        boxy_node = build(boxy_data=boxy_data)
        cmds.delete(node)
        return boxy_node
    return node


def edit_boxy_orientation(node: str, rotation: float, axis: Axis) -> str | False:
    """Rotate the pivot by 90° about an axis."""
    result, issues = boxy_validator.test_selected_boxy(node=node, test_poly_cube=False)
    if result is False:
        LOGGER.info(f"Invalid boxy object: {node}")
        LOGGER.info("\n".join(issues))
        return False
    if rotation % 90 != 0:
        LOGGER.info(f"Invalid rotation: {rotation}")
        return False
    result = rebuild(node=node)
    if type(result) is BoxyException:
        raise result
    else:
        node = result
    boxy_data = get_boxy_data(node=node)
    new_size = {
        Axis.x: Point3(boxy_data.size.x, boxy_data.size.z, boxy_data.size.y),
        Axis.y: Point3(boxy_data.size.z, boxy_data.size.y, boxy_data.size.x),
        Axis.z: Point3(boxy_data.size.y, boxy_data.size.x, boxy_data.size.z)
    }[axis]
    boxy_data.size = new_size
    if axis is Axis.x:
        boxy_data.rotation.x = boxy_data.rotation.x + rotation
    elif axis is Axis.y:
        boxy_data.rotation.y = boxy_data.rotation.y + rotation
    else:
        boxy_data.rotation.z = boxy_data.rotation.z + rotation
    cmds.delete(node)
    return build(boxy_data=boxy_data)


def get_boxy_data(node: str) -> BoxyData:
    """Get BoxyData from a boxy node."""
    LOGGER.debug(f"=== get_boxy_data({node}) ===")
    shape = node_utils.get_shape_from_transform(node=node)

    if not shape or cmds.objectType(shape) != "boxyShape":
        raise ValueError(f"Node '{node}' is not a valid boxy node")

    # Get transform position
    transform_pos = node_utils.get_translation(node)
    LOGGER.debug(f"  transform position: {transform_pos}")

    # Get color from shape attributes
    color = RGBColor(
        int(cmds.getAttr(f"{shape}.wireframeColorR") * 255),
        int(cmds.getAttr(f"{shape}.wireframeColorG") * 255),
        int(cmds.getAttr(f"{shape}.wireframeColorB") * 255)
    )

    # Get size from shape attributes
    size = Point3(
        cmds.getAttr(f"{shape}.sizeX"),
        cmds.getAttr(f"{shape}.sizeY"),
        cmds.getAttr(f"{shape}.sizeZ")
    )
    LOGGER.debug(f"  size: {size}")

    pivot = get_boxy_pivot(node=node)
    LOGGER.debug(f"  pivot: {pivot}")

    # Calculate center from transform position based on pivot
    rotation = node_utils.get_rotation(node)
    if pivot == Side.bottom:
        # Transform is at base, center is half height up
        local_offset = Point3(0.0, size.y / 2.0, 0.0)
        rotated_offset = math_utils.apply_euler_xyz_rotation(local_offset, rotation)
        center = Point3(
            transform_pos.x + rotated_offset.x,
            transform_pos.y + rotated_offset.y,
            transform_pos.z + rotated_offset.z
        )
    elif pivot == Side.top:
        # Transform is at top, center is half height down
        local_offset = Point3(0.0, -size.y / 2.0, 0.0)
        rotated_offset = math_utils.apply_euler_xyz_rotation(local_offset, rotation)
        center = Point3(
            transform_pos.x + rotated_offset.x,
            transform_pos.y + rotated_offset.y,
            transform_pos.z + rotated_offset.z
        )
    else:
        # Transform is at center
        center = transform_pos

    bounds = Bounds(size=size, position=center, rotation=rotation)
    LOGGER.debug(f"  center: {center}")
    LOGGER.debug(f"  bounds.size: {bounds.size}")
    LOGGER.debug(f"  bounds.rotation: {bounds.rotation}")

    boxy_data = BoxyData(
        bounds=bounds,
        pivot=pivot,
        color=color,
        name=node
    )
    LOGGER.debug(f"  boxy_data.pivot_position: {boxy_data.pivot_position}")
    LOGGER.debug(f"=== end get_boxy_data ===")
    return boxy_data


def get_boxy_pivot(node: str) -> Side:
    """Get the pivot of a boxy node."""
    shape = node_utils.get_shape_from_transform(node=node)

    if not shape or cmds.objectType(shape) != "boxyShape":
        raise ValueError(f"Node '{node}' is not a valid boxy node")

    pivot_index = cmds.getAttr(f"{shape}.pivot")
    return {
        0: Side.bottom,
        1: Side.center,
        2: Side.top,
    }[pivot_index]


def get_position_from_bounds(bounds: Point3Pair, pivot: Side) -> Point3:
    """Get the position of a Boxy object from the bounds."""
    assert pivot in (Side.bottom, Side.top, Side.center), f"Invalid pivot: {pivot}"
    return {
        Side.bottom: bounds.base_center,
        Side.center: bounds.center,
        Side.top: bounds.top_center,
    }[pivot]


def get_selected_boxy_nodes() -> list[str]:
    """Get a list of all boxy nodes selected."""
    return [x for x in node_utils.get_selected_transforms(full_path=True) if node_utils.is_boxy(x)]


def get_selected_poly_cubes() -> list[str]:
    """Get a list of all poly cube nodes selected."""
    mesh_nodes = [x for x in node_utils.get_selected_geometry() if not node_utils.is_custom_type_node(x)]
    poly_cubes = []
    for x in mesh_nodes:
        shape = node_utils.get_shape_from_transform(x)
        result = cmds.listConnections(f"{shape}.inMesh")
        if result and cmds.objectType(result[0]) == "polyCube":
            poly_cubes.append(x)
    return poly_cubes


def rebuild(node: str, pivot: Side | None = None, color: RGBColor | None = None) -> str | BoxyException:
    """Rebuild a boxy node."""
    result, issues = boxy_validator.test_selected_boxy(node=node, test_poly_cube=False)
    if result is False:
        msg = "Invalid boxy object\n" + "\n".join(issues)
        LOGGER.info(msg)
        return BoxyException(message=f"Invalid boxy object [{node}]")
    pivot: Side = pivot if pivot else get_boxy_pivot(node=node)
    bounds: Bounds = bounds_utils.get_cuboid(geometry=node)
    # Preserve scale before deleting
    scale = node_utils.get_scale(node)
    cmds.delete(node)
    boxy_data = BoxyData(
        bounds=bounds,
        pivot=pivot,
        color=color if color else color_classes.DEEP_GREEN,
        name=node
    )
    boxy_object = build(boxy_data=boxy_data)
    # Restore scale after building
    node_utils.scale(nodes=boxy_object, value=scale)
    LOGGER.debug(f"Boxy rebuilt: {boxy_object}")
    return boxy_object
