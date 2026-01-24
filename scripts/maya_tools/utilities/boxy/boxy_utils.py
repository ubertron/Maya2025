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

    def __repr__(self) -> str:
        return f"BoxyData(bounds={self.bounds}, pivot={self.pivot}, color={self.color}, name={self.name}"

    @property
    def dictionary(self) -> dict:
        return {
            "position": self.bounds.position.values,
            "pivot position": self.pivot_position.values,
            "rotation": self.bounds.rotation.values,
            "size": self.bounds.size.values,
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
        LOGGER.debug(f"  BoxyData.pivot_position calculation:")
        LOGGER.debug(f"    self.pivot: {self.pivot}")
        LOGGER.debug(f"    self.bounds.position: {self.bounds.position}")
        LOGGER.debug(f"    self.bounds.size: {self.bounds.size}")
        LOGGER.debug(f"    self.bounds.rotation: {self.bounds.rotation}")
        if self.pivot == Side.bottom:
            result = self.bounds.base_center
            LOGGER.debug(f"    returning base_center: {result}")
            return result
        elif self.pivot == Side.top:
            result = self.bounds.top_center
            LOGGER.debug(f"    returning top_center: {result}")
            return result
        elif self.pivot == Side.center:
            result = self.bounds.position
            LOGGER.debug(f"    returning center position: {result}")
            return result
        else:
            # Calculate pivot position for left/right/front/back
            from core.math_utils import apply_euler_xyz_rotation
            offsets = {
                Side.left: Point3(-self.bounds.size.x / 2.0, 0.0, 0.0),
                Side.right: Point3(self.bounds.size.x / 2.0, 0.0, 0.0),
                Side.front: Point3(0.0, 0.0, self.bounds.size.z / 2.0),
                Side.back: Point3(0.0, 0.0, -self.bounds.size.z / 2.0),
            }
            local_offset = offsets[self.pivot]
            LOGGER.debug(f"    local_offset (before rotation): {local_offset}")
            rotated_offset = apply_euler_xyz_rotation(local_offset, self.bounds.rotation)
            LOGGER.debug(f"    rotated_offset (after rotation): {rotated_offset}")
            result = Point3(
                self.bounds.position.x + rotated_offset.x,
                self.bounds.position.y + rotated_offset.y,
                self.bounds.position.z + rotated_offset.z
            )
            LOGGER.debug(f"    returning calculated pivot_position: {result}")
            return result


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
            # Creating from scratch - calculate center position so pivot ends up at origin
            # This ensures the transform is at (0, 0, 0) regardless of pivot setting
            if self.pivot == Side.bottom:
                center_position = Point3(0, self.size.y / 2, 0)
            elif self.pivot == Side.top:
                center_position = Point3(0, -self.size.y / 2, 0)
            elif self.pivot == Side.center:
                center_position = ZERO3
            elif self.pivot == Side.left:
                center_position = Point3(self.size.x / 2, 0, 0)
            elif self.pivot == Side.right:
                center_position = Point3(-self.size.x / 2, 0, 0)
            elif self.pivot == Side.front:
                center_position = Point3(0, 0, -self.size.z / 2)
            elif self.pivot == Side.back:
                center_position = Point3(0, 0, self.size.z / 2)
            else:
                center_position = ZERO3

            bounds = Bounds(size=self.size, position=center_position, rotation=self.rotation)
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
        valid_pivots = (Side.bottom, Side.center, Side.top, Side.left, Side.right, Side.front, Side.back)
        assert pivot in valid_pivots, f"Invalid pivot position: {pivot.name}"
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


BOXY_PIVOT_ATTR = "boxyPivotType"


def convert_boxy_to_poly_cube(node: str) -> str | BoxyException:
    """Convert a boxy node to a poly-cube.

    Maya 2022 compatible - uses manual baseline positioning.
    For rotated cubes, we must create the cube at the center position, then set rotation,
    then reposition the pivot. The baseline parameter only works for unrotated cubes.

    The original pivot type is stored as a custom attribute for reliable conversion back.
    """
    result = rebuild(node=node)
    if isinstance(result, BoxyException):
        return result
    boxy_data: BoxyData = get_boxy_data(node=result)
    LOGGER.debug(f"convert_boxy_to_poly_cube: boxy_data.pivot = {boxy_data.pivot}")
    LOGGER.debug(f"  boxy_data.bounds.position = {boxy_data.bounds.position}")
    LOGGER.debug(f"  boxy_data.pivot_position = {boxy_data.pivot_position}")

    # Always create cube at center position with baseline=0.5 (center)
    # This ensures rotation happens around the correct point
    cube = geometry_utils.create_cube(
        size=boxy_data.bounds.size,
        position=boxy_data.bounds.position,
        baseline=0.5
    )
    node_utils.set_rotation(nodes=cube, value=boxy_data.bounds.rotation)

    # Set pivot to match the original boxy pivot position
    # This ensures the transform translation stays at the pivot location
    node_utils.set_pivot(nodes=cube, value=boxy_data.pivot_position, reset=True)

    # Store the original pivot type as a custom attribute for reliable conversion back
    pivot_index = {
        Side.bottom: 0, Side.center: 1, Side.top: 2,
        Side.left: 3, Side.right: 4, Side.front: 5, Side.back: 6
    }[boxy_data.pivot]
    if not cmds.attributeQuery(BOXY_PIVOT_ATTR, node=cube, exists=True):
        cmds.addAttr(cube, longName=BOXY_PIVOT_ATTR, attributeType="short", defaultValue=pivot_index)
    cmds.setAttr(f"{cube}.{BOXY_PIVOT_ATTR}", pivot_index)
    LOGGER.debug(f"  Stored pivot type {boxy_data.pivot.name} (index {pivot_index}) on {cube}.{BOXY_PIVOT_ATTR}")

    cmds.delete(node)
    return cube


def convert_poly_cube_to_boxy(node: str, color: RGBColor = color_classes.DEEP_GREEN) -> str:
    """Convert a poly-cube to a boxy node.

    Maya 2022 compatible - doesn't rely on heightBaseline attribute.
    Uses custom boxyPivotType attribute if available, otherwise detects from geometry.
    """
    LOGGER.info(f"=== convert_poly_cube_to_boxy({node}) ===")
    shape = node_utils.get_shape_from_transform(node=node)
    LOGGER.info(f"  shape: {shape}")

    # Search through history to find polyCube node (handles intermediate nodes from set_pivot)
    poly_cube_node = find_poly_cube_in_history(node)
    LOGGER.info(f"  poly_cube_node from history search: {poly_cube_node}")
    if not poly_cube_node:
        LOGGER.info(f"  No polyCube found in history - not a polyCube")
        return node
    LOGGER.info(f"  poly_cube_node: {poly_cube_node}, type: {cmds.objectType(poly_cube_node)}")

    # Get bounds (try CuboidFinder first for rotated faces, fall back to BoundsFinder)
    bounds: Bounds = bounds_utils.get_cuboid(geometry=node)
    LOGGER.info(f"  bounds from get_cuboid: {bounds}")
    if not bounds:
        bounds = bounds_utils.get_bounds(geometry=node, inherit_rotations=True)
        LOGGER.info(f"  bounds from get_bounds: {bounds}")

    # Check for stored pivot type attribute first (most reliable)
    pivot = None
    if cmds.attributeQuery(BOXY_PIVOT_ATTR, node=node, exists=True):
        pivot_index = cmds.getAttr(f"{node}.{BOXY_PIVOT_ATTR}")
        pivot_map = {
            0: Side.bottom, 1: Side.center, 2: Side.top,
            3: Side.left, 4: Side.right, 5: Side.front, 6: Side.back
        }
        pivot = pivot_map.get(pivot_index, Side.center)
        LOGGER.info(f"  Found stored pivot attribute: index={pivot_index}, pivot={pivot.name}")
    else:
        # Detect pivot from geometry (pivot position relative to bounds center)
        pivot = _detect_pivot_from_poly_cube(node, bounds)
        LOGGER.info(f"  Detected pivot from geometry: {pivot.name}")

    LOGGER.info(f"  final pivot: {pivot}")
    boxy_data = BoxyData(
        bounds=bounds,
        pivot=pivot,
        color=color,
        name="boxy"
    )
    LOGGER.info(f"  building boxy with data: {boxy_data.dictionary}")
    boxy_node = build(boxy_data=boxy_data)
    LOGGER.info(f"  built boxy_node: {boxy_node}")
    cmds.delete(node)
    return boxy_node


def _detect_pivot_from_poly_cube(node: str, bounds: Bounds) -> Side:
    """Detect pivot type from polyCube pivot position relative to bounds center.

    Compares the pivot position to the bounds center in local space (XZ plane)
    to determine if pivot is center, left, right, front, or back.
    """
    LOGGER.info(f"  === _detect_pivot_from_poly_cube({node}) ===")
    # Get pivot position
    pivot_pos = node_utils.get_pivot_position(node)
    center = bounds.position
    LOGGER.info(f"    pivot_pos: {pivot_pos}")
    LOGGER.info(f"    center: {center}")

    # Calculate offset from center to pivot in local space
    # We need to account for rotation
    offset = Point3(
        pivot_pos.x - center.x,
        pivot_pos.y - center.y,
        pivot_pos.z - center.z
    )
    LOGGER.info(f"    offset (world): {offset}")

    # Un-rotate the offset to get local space offset
    if bounds.rotation.x != 0 or bounds.rotation.y != 0 or bounds.rotation.z != 0:
        # Apply inverse rotation
        inv_rotation = Point3(-bounds.rotation.x, -bounds.rotation.y, -bounds.rotation.z)
        offset = math_utils.apply_euler_xyz_rotation(offset, inv_rotation)
        LOGGER.info(f"    offset (local, after un-rotate): {offset}")

    # Tolerance for detecting non-center pivot (half of size)
    half_x = bounds.size.x / 2.0
    half_z = bounds.size.z / 2.0
    tolerance = 0.01  # Small tolerance for floating point comparison
    LOGGER.info(f"    half_x: {half_x}, half_z: {half_z}, tolerance: {tolerance}")

    # Check which side the pivot is on (in local XZ space)
    LOGGER.info(f"    checking left: abs({offset.x} + {half_x}) = {abs(offset.x + half_x)}")
    LOGGER.info(f"    checking right: abs({offset.x} - {half_x}) = {abs(offset.x - half_x)}")
    LOGGER.info(f"    checking front: abs({offset.z} - {half_z}) = {abs(offset.z - half_z)}")
    LOGGER.info(f"    checking back: abs({offset.z} + {half_z}) = {abs(offset.z + half_z)}")

    if abs(offset.x + half_x) < tolerance:  # pivot at min X
        LOGGER.info(f"    detected: left")
        return Side.left
    elif abs(offset.x - half_x) < tolerance:  # pivot at max X
        LOGGER.info(f"    detected: right")
        return Side.right
    elif abs(offset.z - half_z) < tolerance:  # pivot at max Z
        LOGGER.info(f"    detected: front")
        return Side.front
    elif abs(offset.z + half_z) < tolerance:  # pivot at min Z
        LOGGER.info(f"    detected: back")
        return Side.back
    else:
        LOGGER.info(f"    detected: center (no match)")
        return Side.center


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

    # Get transform values
    transform_pos = node_utils.get_translation(node)
    transform_scale = node_utils.get_scale(node)
    LOGGER.debug(f"  transform position: {transform_pos}")
    LOGGER.debug(f"  transform scale: {transform_scale}")

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
    LOGGER.debug(f"  size (from shape attributes): {size}")
    # NOTE: This size does NOT account for transform scale!
    # If transform has scale, the world-space size would be:
    scaled_size = Point3(
        size.x * transform_scale.x,
        size.y * transform_scale.y,
        size.z * transform_scale.z
    )
    LOGGER.debug(f"  scaled_size (world-space size): {scaled_size}")
    if transform_scale.x != 1.0 or transform_scale.y != 1.0 or transform_scale.z != 1.0:
        LOGGER.debug(f"  NOTE: Transform has non-identity scale. Using scaled_size for center calculation.")

    pivot = get_boxy_pivot(node=node)
    LOGGER.debug(f"  pivot: {pivot}")

    # Calculate center from transform position based on pivot
    # Offset from pivot to center in local space
    rotation = node_utils.get_rotation(node)
    LOGGER.debug(f"  transform rotation: {rotation}")

    # Use SCALED size for pivot offset calculation since we need world-space center position
    # The offset from pivot to center is in local space, but scale affects this offset in world space
    pivot_offsets = {
        Side.bottom: Point3(0.0, scaled_size.y / 2.0, 0.0),    # pivot at bottom, center is up
        Side.top: Point3(0.0, -scaled_size.y / 2.0, 0.0),      # pivot at top, center is down
        Side.left: Point3(scaled_size.x / 2.0, 0.0, 0.0),      # pivot at left (min X), center is +X
        Side.right: Point3(-scaled_size.x / 2.0, 0.0, 0.0),    # pivot at right (max X), center is -X
        Side.front: Point3(0.0, 0.0, -scaled_size.z / 2.0),    # pivot at front (max Z), center is -Z
        Side.back: Point3(0.0, 0.0, scaled_size.z / 2.0),      # pivot at back (min Z), center is +Z
        Side.center: Point3(0.0, 0.0, 0.0),
    }
    local_offset = pivot_offsets.get(pivot, Point3(0.0, 0.0, 0.0))
    LOGGER.debug(f"  local_offset (from pivot to center, using scaled size): {local_offset}")

    if local_offset.x != 0.0 or local_offset.y != 0.0 or local_offset.z != 0.0:
        rotated_offset = math_utils.apply_euler_xyz_rotation(local_offset, rotation)
        LOGGER.debug(f"  rotated_offset (after applying rotation): {rotated_offset}")
        center = Point3(
            transform_pos.x + rotated_offset.x,
            transform_pos.y + rotated_offset.y,
            transform_pos.z + rotated_offset.z
        )
        LOGGER.debug(f"  center calculated as: transform_pos + rotated_offset = {center}")
    else:
        # Transform is at center
        center = transform_pos
        LOGGER.debug(f"  center = transform_pos (pivot is center): {center}")

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
        3: Side.left,
        4: Side.right,
        5: Side.front,
        6: Side.back,
    }[pivot_index]


def get_position_from_bounds(bounds: Point3Pair, pivot: Side) -> Point3:
    """Get the position of a Boxy object from the bounds."""
    valid_pivots = (Side.bottom, Side.top, Side.center, Side.left, Side.right, Side.front, Side.back)
    assert pivot in valid_pivots, f"Invalid pivot: {pivot}"

    if pivot == Side.bottom:
        return bounds.base_center
    elif pivot == Side.top:
        return bounds.top_center
    elif pivot == Side.left:
        return Point3(bounds.minimum.x, bounds.center.y, bounds.center.z)
    elif pivot == Side.right:
        return Point3(bounds.maximum.x, bounds.center.y, bounds.center.z)
    elif pivot == Side.front:
        return Point3(bounds.center.x, bounds.center.y, bounds.maximum.z)
    elif pivot == Side.back:
        return Point3(bounds.center.x, bounds.center.y, bounds.minimum.z)
    else:  # center
        return bounds.center


def get_selected_boxy_nodes() -> list[str]:
    """Get a list of all boxy nodes selected."""
    return [x for x in node_utils.get_selected_transforms(full_path=True) if node_utils.is_boxy(x)]


def find_poly_cube_in_history(node: str) -> str | None:
    """Find a polyCube node in the construction history of a mesh.

    When set_pivot is called with reset=True, intermediate nodes may be inserted
    between the shape and the polyCube node. This function searches through the
    history to find the polyCube node.

    Args:
        node: Transform or shape node name.

    Returns:
        The polyCube node name if found, None otherwise.
    """
    shape = node_utils.get_shape_from_transform(node=node)
    if not shape:
        return None

    # Get the full history of the shape
    history = cmds.listHistory(shape, pruneDagObjects=True) or []
    LOGGER.debug(f"find_poly_cube_in_history({node}): history = {history}")

    for hist_node in history:
        if cmds.objectType(hist_node) == "polyCube":
            LOGGER.debug(f"  Found polyCube: {hist_node}")
            return hist_node

    LOGGER.debug(f"  No polyCube found in history")
    return None


def get_selected_poly_cubes() -> list[str]:
    """Get a list of all poly cube nodes selected."""
    mesh_nodes = [x for x in node_utils.get_selected_geometry() if not node_utils.is_custom_type_node(x)]
    poly_cubes = []
    for x in mesh_nodes:
        if find_poly_cube_in_history(x):
            poly_cubes.append(x)
    return poly_cubes


def rebuild(node: str, pivot: Side | None = None, color: RGBColor | None = None) -> str | BoxyException:
    """Rebuild a boxy node."""
    LOGGER.debug(f"=== rebuild({node}) ===")
    result, issues = boxy_validator.test_selected_boxy(node=node, test_poly_cube=False)
    if result is False:
        msg = "Invalid boxy object\n" + "\n".join(issues)
        LOGGER.info(msg)
        return BoxyException(message=f"Invalid boxy object [{node}]")

    # Get original transform values BEFORE anything else
    original_translation = node_utils.get_translation(node)
    original_rotation = node_utils.get_rotation(node)
    original_scale = node_utils.get_scale(node)
    original_pivot = get_boxy_pivot(node=node)
    LOGGER.debug(f"  Original transform translation: {original_translation}")
    LOGGER.debug(f"  Original transform rotation: {original_rotation}")
    LOGGER.debug(f"  Original transform scale: {original_scale}")
    LOGGER.debug(f"  Original boxy pivot: {original_pivot}")

    pivot: Side = pivot if pivot else original_pivot
    LOGGER.debug(f"  Target pivot: {pivot}")

    bounds: Bounds = bounds_utils.get_cuboid(geometry=node)
    LOGGER.debug(f"  Bounds from get_cuboid:")
    LOGGER.debug(f"    position (center): {bounds.position}")
    LOGGER.debug(f"    size (unscaled): {bounds.size}")
    LOGGER.debug(f"    rotation: {bounds.rotation}")

    # Preserve scale before deleting
    scale = node_utils.get_scale(node)
    LOGGER.debug(f"  Preserved scale: {scale}")

    # Check if scale is non-identity - if so, bake it into the size
    # This prevents position jumping when changing pivot on scaled transforms
    has_scale = scale.x != 1.0 or scale.y != 1.0 or scale.z != 1.0
    if has_scale:
        LOGGER.debug(f"  Non-identity scale detected, baking scale into size")
        scaled_size = Point3(
            bounds.size.x * scale.x,
            bounds.size.y * scale.y,
            bounds.size.z * scale.z
        )
        bounds = Bounds(size=scaled_size, position=bounds.position, rotation=bounds.rotation)
        LOGGER.debug(f"  Bounds after baking scale:")
        LOGGER.debug(f"    size (scaled): {bounds.size}")
        # Scale will not be restored since it's now baked into size
        scale = Point3(1.0, 1.0, 1.0)

    cmds.delete(node)
    boxy_data = BoxyData(
        bounds=bounds,
        pivot=pivot,
        color=color if color else color_classes.DEEP_GREEN,
        name=node
    )
    LOGGER.debug(f"  BoxyData created:")
    LOGGER.debug(f"    bounds.position: {boxy_data.bounds.position}")
    LOGGER.debug(f"    pivot: {boxy_data.pivot}")
    LOGGER.debug(f"    pivot_position (where transform will be placed): {boxy_data.pivot_position}")

    boxy_object = build(boxy_data=boxy_data)
    # Restore scale after building (will be identity if scale was baked)
    if scale.x != 1.0 or scale.y != 1.0 or scale.z != 1.0:
        node_utils.scale(nodes=boxy_object, value=scale)

    # Log final transform values
    final_translation = node_utils.get_translation(boxy_object)
    final_rotation = node_utils.get_rotation(boxy_object)
    final_scale = node_utils.get_scale(boxy_object)
    LOGGER.debug(f"  Final transform translation: {final_translation}")
    LOGGER.debug(f"  Final transform rotation: {final_rotation}")
    LOGGER.debug(f"  Final transform scale: {final_scale}")
    LOGGER.debug(f"=== end rebuild ===")
    LOGGER.debug(f"Boxy rebuilt: {boxy_object}")
    return boxy_object
