"""
ROBOTOOLS STUDIO PROPRIETARY SOFTWARE LICENSE

Copyright (c) 2026 Andrew Davis / Robotools Studio. All Rights Reserved.

1. OWNERSHIP
   This software is the proprietary property of Andrew Davis / Robotools Studio.
   All intellectual property rights remain with the copyright holder.

2. RESTRICTIONS
   Without explicit written permission, you may NOT:
   - Copy, reproduce, or distribute this software
   - Modify, adapt, or create derivative works
   - Reverse engineer, decompile, or disassemble this software
   - Remove or alter any proprietary notices
   - Use this software in production environments without pre-arranged
     agreement with Andrew Davis / Robotools Studio
   - Sublicense, rent, lease, or lend this software

3. LICENSING
   Individual and commercial licenses are available.
   For licensing inquiries: andy_j_davis@yahoo.com

4. DISCLAIMER
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
   IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM,
   DAMAGES, OR OTHER LIABILITY ARISING FROM THE USE OF THIS SOFTWARE.

5. PROTECTED TECHNOLOGIES
   - Boxy Plugin and BoxyShape custom node
   - Bounds calculation utilities
   - Related tools and plugins
"""
# Boxy helper object.
from __future__ import annotations

import contextlib
import logging

from enum import Enum, auto

from core import color_classes, math_utils
from core.bounds import Bounds
from core.color_classes import ColorRGB
from core.core_enums import CreationMode, DataType, Side, Axis
from core.logging_utils import get_logger
from core.point_classes import Point3, Point3Pair, UNIT3, ZERO3
from robotools import CustomAttribute, CustomType

with contextlib.suppress(ImportError):
    from maya import cmds
    from maya_tools import attribute_utils, node_utils
    from maya_tools.geometry import geometry_utils, component_utils, bounds_utils
    from maya_tools.node_utils import get_translation
    from robotools.boxy import BoxyException
    from robotools.boxy import boxy_node
    from robotools.boxy.boxy_data import BoxyData
    from tests.validators import boxy_validator

DEBUG_MODE = False
DEFAULT_SIZE: float = 100.0
LOGGER = get_logger(__name__, level=logging.INFO)


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

    def __init__(self, color: ColorRGB = color_classes.DEEP_GREEN):
        self.box = None
        self.size = Point3(*[DEFAULT_SIZE for _ in range(3)])
        self.position = ZERO3
        self.rotation = ZERO3
        self.pivot_side = Side.center
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

    def _build(self, inherit_rotation: bool = True, inherit_scale: bool = True):
        """Build boxy box."""
        component_selection = self.component_selection
        LOGGER.debug(f"DEBUG Boxy._build:")
        LOGGER.debug(f"  inherit_rotations: {inherit_rotation}")
        LOGGER.debug(f"  inherit_scale: {inherit_scale}")
        LOGGER.debug(f"  component_selection: {component_selection}")
        if inherit_rotation and component_selection:
            # Look for a cuboid
            bounds = bounds_utils.get_cuboid(geometry=component_selection, inherit_scale=inherit_scale)
            LOGGER.debug(f"  get_cuboid returned: {bounds}")
            # If no cuboid, get the bounds using the rotation
            if not bounds:
                bounds = bounds_utils.get_bounds(geometry=self.component_selection, inherit_rotations=True,
                                                  inherit_scale=inherit_scale)
                LOGGER.debug(f"  get_bounds returned: {bounds}")
            # Calculate translation (pivot position) from bounds center
            translation = bounds.get_pivot(self.pivot_side)
            size = bounds.size
            rotation = bounds.rotation
            scale = bounds.scale if inherit_scale else UNIT3
        else:
            # Creating from scratch
            translation = self.position
            size = self.size
            rotation = self.rotation
            # Use inherited_scale if set during evaluation
            scale = getattr(self, 'inherited_scale', UNIT3)
        LOGGER.debug(f"  FINAL values for boxy_data:")
        LOGGER.debug(f"    size: {size}")
        LOGGER.debug(f"    translation: {translation}")
        LOGGER.debug(f"    rotation: {rotation}")
        LOGGER.debug(f"    scale: {scale}")
        boxy_data = BoxyData(
            size=size,
            translation=translation,
            rotation=rotation,
            pivot_side=self.pivot_side,
            color=self.color,
            scale=scale,
        )
        return build(boxy_data=boxy_data)

    def _evaluate_for_multiple_selection(self):
        """Set up boxy attributes for multiple nodes."""
        min_max: Point3Pair = node_utils.get_min_max_from_selection(self.selection)
        self.position = min_max.get_pivot(self.pivot_side)
        self.size = min_max.size

    def _evaluate_for_single_selection(self, inherit_rotations: bool, inherit_scale: bool = False):
        """Set up boxy attributes for a single node."""
        LOGGER.debug(f">>> {self.selected_transforms[0]}")
        self.rotation_y = node_utils.get_rotation(self.selected_transforms[0]).y
        position = get_translation(self.selected_transforms[0])

        # Store inherited scale if requested
        if inherit_scale:
            self.inherited_scale = node_utils.get_scale(self.selected_transforms[0])
        else:
            self.inherited_scale = UNIT3

        # work out the size compensating for rotation
        if self.components_only:
            # get the bounds of locators/verts/cvs
            points = node_utils.get_points_from_selection()
            y_offset = -self.rotation_y if inherit_rotations else 0.0
            min_max: Point3Pair = math_utils.get_minimum_maximum_from_points(
                points=points, y_offset=y_offset, pivot=position)
            self.size = min_max.size
            position_pre_rotation = get_position_from_bounds(bounds=min_max, pivot=self.pivot_side)
            self.position = math_utils.rotate_point_about_y(
                point=position_pre_rotation, y_rotation=-y_offset, pivot=position)
        else:
            # get the bounds from the transform
            min_max: Point3Pair = node_utils.get_min_max_points(
                node=self.selected_transforms[0], inherit_rotations=inherit_rotations)
            self.size = min_max.size
            self.position = min_max.get_pivot(self.pivot_side)

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
               inherit_scale: bool = False, default_size: float = 10.0) -> tuple[list[str], list[BoxyException]]:
        """Evaluate selection."""
        valid_pivots = (Side.bottom, Side.center, Side.top, Side.left, Side.right, Side.front, Side.back)
        assert pivot in valid_pivots, f"Invalid pivot position: {pivot.name}"
        exceptions = []
        rebuilt_boxy_nodes = []  # Track rebuilt boxy nodes with their NEW names
        self.pivot_side = pivot
        self.size = Point3(default_size, default_size, default_size)
        if ElementType.boxy in self.element_type_dict:
            for boxy_item in self.element_type_dict[ElementType.boxy]:
                result = rebuild(node=boxy_item, pivot=pivot, color=self.color)
                if isinstance(result, BoxyException):
                    exceptions.append(result)
                else:
                    rebuilt_boxy_nodes.append(result)  # Store the NEW node name
                    self.selection.remove(boxy_item)
        if len(self.selected_transforms) > 1:
            self._evaluate_for_multiple_selection()
        elif len(self.selected_transforms) == 1:
            self._evaluate_for_single_selection(inherit_rotations=inherit_rotations, inherit_scale=inherit_scale)

        # if only boxy items are selected, don't build because we've handled them already
        original_boxy_count = len(self.element_type_dict.get(ElementType.boxy, []))
        if not (original_boxy_count and original_boxy_count == len(self.all_selected_transforms)):
            rebuilt_boxy_nodes.append(self._build(inherit_rotation=inherit_rotations, inherit_scale=inherit_scale))

        return rebuilt_boxy_nodes, exceptions

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
                    self.append_dict_list(_dict=element_type_dict, key=ElementType.invalid, value=x)
        self._element_type_dict = element_type_dict


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


def boxy_cube_toggle(wireframe_color: ColorRGB) -> tuple[list[str], list[BoxyException]]:
    """Toggle between boxy and polycube."""
    selection_list = []
    exceptions = []
    boxy_nodes = get_selected_boxy_nodes()
    polycubes = get_selected_polycubes()
    for node in boxy_nodes:
        result = convert_boxy_to_polycube(node=node)
        if isinstance(result, BoxyException):
            exceptions.append(result)
        else:
            selection_list.append(result)
    for polycube in polycubes:
        result = convert_polycube_to_boxy(polycube=polycube, color=wireframe_color)
        if isinstance(result, BoxyException):
            exceptions.append(result)
        else:
            selection_list.append(result)
    return selection_list, exceptions


def build(boxy_data: BoxyData) -> str:
    """Build boxy object using custom DAG node."""
    return boxy_node.build(boxy_data=boxy_data)


def convert_boxy_to_polycube(node: str, pivot: Side = None, inherit_scale: bool = False) -> str | BoxyException:
    """Convert a boxy node to a polycube.

    Uses create_polycube() for consistent polycube creation.

    :param node: The boxy transform node
    :param pivot: Optional pivot override. If None, uses the boxy's original pivot.
    :param inherit_scale: If True, preserve original scale on polycube. If False, bake scale into size.
    """
    # Get original transform values BEFORE any modifications
    original_scale = node_utils.get_scale(node)
    original_translation = node_utils.get_translation(node)
    original_rotation = node_utils.get_rotation(node)
    has_scale = original_scale.x != 1.0 or original_scale.y != 1.0 or original_scale.z != 1.0
    LOGGER.debug(f"convert_boxy_to_polycube: inherit_scale={inherit_scale}, has_scale={has_scale}")
    LOGGER.debug(f"  original_scale: {original_scale}")
    LOGGER.debug(f"  original_translation: {original_translation}")

    if inherit_scale and has_scale:
        # When inheriting scale, get data directly from boxy (don't use rebuild which bakes scale)
        boxy_data: BoxyData = get_boxy_data(node=node)
        target_pivot = pivot if pivot else boxy_data.pivot_side
        size = boxy_data.size  # Unscaled size from shape attributes
        rotation = original_rotation
        scale = original_scale
        LOGGER.debug(f"=== convert_boxy_to_polycube (inherit_scale=True, has_scale=True) ===")
        LOGGER.debug(f"  original_translation: {original_translation}")
        LOGGER.debug(f"  original_rotation: {original_rotation}")
        LOGGER.debug(f"  original_scale: {original_scale}")
        LOGGER.debug(f"  size (unscaled from shape): {size}")
        LOGGER.debug(f"  original pivot: {boxy_data.pivot_side.name}, target pivot: {target_pivot.name}")

        # Calculate translation accounting for pivot change
        # The visual size is size * scale
        visual_size = Point3(size.x * scale.x, size.y * scale.y, size.z * scale.z)
        LOGGER.debug(f"  visual_size (size * scale): {visual_size}")

        # Calculate visual center from original pivot position
        pivot_to_center_offsets = {
            Side.bottom.name: Point3(0.0, visual_size.y / 2.0, 0.0),
            Side.top.name: Point3(0.0, -visual_size.y / 2.0, 0.0),
            Side.left.name: Point3(visual_size.x / 2.0, 0.0, 0.0),
            Side.right.name: Point3(-visual_size.x / 2.0, 0.0, 0.0),
            Side.front.name: Point3(0.0, 0.0, -visual_size.z / 2.0),
            Side.back.name: Point3(0.0, 0.0, visual_size.z / 2.0),
            Side.center.name: Point3(0.0, 0.0, 0.0),
        }
        local_offset_to_center = pivot_to_center_offsets[boxy_data.pivot_side.name]
        LOGGER.debug(f"  local_offset_to_center (before rotation): {local_offset_to_center}")
        rotated_offset_to_center = math_utils.apply_euler_xyz_rotation(local_offset_to_center, rotation)
        LOGGER.debug(f"  rotated_offset_to_center: {rotated_offset_to_center}")
        visual_center = Point3(
            original_translation.x + rotated_offset_to_center.x,
            original_translation.y + rotated_offset_to_center.y,
            original_translation.z + rotated_offset_to_center.z
        )
        LOGGER.debug(f"  visual_center: {visual_center}")

        # Calculate new translation from visual center to target pivot
        center_to_pivot_offsets = {
            Side.bottom.name: Point3(0.0, -visual_size.y / 2.0, 0.0),
            Side.top.name: Point3(0.0, visual_size.y / 2.0, 0.0),
            Side.left.name: Point3(-visual_size.x / 2.0, 0.0, 0.0),
            Side.right.name: Point3(visual_size.x / 2.0, 0.0, 0.0),
            Side.front.name: Point3(0.0, 0.0, visual_size.z / 2.0),
            Side.back.name: Point3(0.0, 0.0, -visual_size.z / 2.0),
            Side.center.name: Point3(0.0, 0.0, 0.0),
        }
        local_offset_to_pivot = center_to_pivot_offsets[target_pivot.name]
        LOGGER.debug(f"  local_offset_to_pivot (before rotation): {local_offset_to_pivot}")
        rotated_offset_to_pivot = math_utils.apply_euler_xyz_rotation(local_offset_to_pivot, rotation)
        LOGGER.debug(f"  rotated_offset_to_pivot: {rotated_offset_to_pivot}")
        translation = Point3(
            visual_center.x + rotated_offset_to_pivot.x,
            visual_center.y + rotated_offset_to_pivot.y,
            visual_center.z + rotated_offset_to_pivot.z
        )
        LOGGER.debug(f"  FINAL translation (new pivot position): {translation}")

        # Delete the original boxy
        short_name = node.split('|')[-1]
        if cmds.objExists(short_name):
            cmds.delete(short_name)
    else:
        # When not inheriting scale, use rebuild which bakes scale into size
        result = rebuild(node=node, pivot=pivot)
        if isinstance(result, BoxyException):
            return result
        boxy_data = get_boxy_data(node=result)
        target_pivot = boxy_data.pivot_side
        size = boxy_data.size  # Baked size (includes scale)
        translation = boxy_data.translation
        rotation = boxy_data.rotation
        scale = None  # No scale to apply
        LOGGER.debug(f"  Using rebuilt boxy data (inherit_scale=False)")
        LOGGER.debug(f"    size: {size}, pivot: {target_pivot}")

        # Delete the rebuilt boxy
        short_name = result.split('|')[-1]
        if cmds.objExists(short_name):
            cmds.delete(short_name)

    # Create polycube with pivot at origin, then position it
    polycube = create_polycube(
        pivot_side=target_pivot,
        size=size,
        creation_mode=CreationMode.pivot_origin,
        construction_history=False,
    )

    # Apply rotation, then translation
    node_utils.set_rotation(nodes=polycube, value=rotation)
    node_utils.set_translation(nodes=polycube, value=translation, absolute=True)

    # Apply scale if inheriting
    if scale is not None:
        node_utils.scale(nodes=polycube, value=scale)
        LOGGER.debug(f"  applied scale: {scale}")

    return polycube


def convert_polycube_to_boxy(polycube: str, color: ColorRGB = color_classes.DEEP_GREEN,
                             pivot: Side = None, inherit_scale: bool = False) -> str:
    """Convert a polycube to a boxy node.

    Detects Robotools polycubes by checking for custom_type attribute.
    Uses stored pivot_side attribute if available, otherwise detects from geometry.

    :param polycube: The polycube transform node
    :param color: Wireframe color for the boxy
    :param pivot: Optional pivot override. If None, uses stored/detected pivot.
    :param inherit_scale: If True, preserve original scale on boxy. If False, bake scale into size.
    """
    LOGGER.info(f"=== convert_polycube_to_boxy({polycube}) ===")
    shape = node_utils.get_shape_from_transform(node=polycube)
    LOGGER.info(f"  shape: {shape}")

    # Check for custom_type attribute to verify it's a Robotools polycube
    if not is_polycube(polycube):
        LOGGER.info(f"  Not a Robotools polycube (missing custom_type attribute)")
        return polycube

    # Get original scale before any operations
    original_scale = node_utils.get_scale(polycube)
    has_scale = original_scale.x != 1.0 or original_scale.y != 1.0 or original_scale.z != 1.0
    LOGGER.info(f"  original_scale: {original_scale}, inherit_scale: {inherit_scale}")

    # Get bounds (try CuboidFinder first for rotated faces, fall back to BoundsFinder)
    bounds: Bounds = bounds_utils.get_cuboid(geometry=polycube)
    LOGGER.info(f"  bounds from get_cuboid: {bounds}")
    if not bounds:
        bounds = bounds_utils.get_bounds(geometry=polycube, inherit_rotations=True)
        LOGGER.info(f"  bounds from get_bounds: {bounds}")

    # Use pivot override if provided, otherwise detect from attribute/geometry
    if pivot is not None:
        LOGGER.info(f"  Using pivot override: {pivot.name}")
    elif cmds.attributeQuery(CustomAttribute.pivot_side.name, node=shape, exists=True):
        # New polycubes store pivot_side as string on shape
        pivot_name = cmds.getAttr(f"{shape}.{CustomAttribute.pivot_side.name}")
        pivot = Side[pivot_name]
        LOGGER.info(f"  Found stored pivot_side attribute: {pivot.name}")
    elif cmds.attributeQuery(CustomAttribute.pivot_side.name, node=polycube, exists=True):
        # Legacy polycubes store pivot_side as index on transform
        pivot_index = cmds.getAttr(f"{polycube}.{CustomAttribute.pivot_side.name}")
        pivot_map = {
            0: Side.bottom, 1: Side.center, 2: Side.top,
            3: Side.left, 4: Side.right, 5: Side.front, 6: Side.back
        }
        pivot = pivot_map.get(pivot_index, Side.center)
        LOGGER.info(f"  Found legacy pivot attribute: index={pivot_index}, pivot={pivot.name}")
    else:
        # Detect pivot from geometry (pivot position relative to bounds center)
        pivot = _detect_pivot_from_poly_cube(polycube, bounds)
        LOGGER.info(f"  Detected pivot from geometry: {pivot.name}")

    LOGGER.info(f"  final pivot: {pivot}")

    # Calculate size - unbake if inheriting scale
    if inherit_scale and has_scale:
        size = Point3(
            bounds.size.x / original_scale.x,
            bounds.size.y / original_scale.y,
            bounds.size.z / original_scale.z,
        )
        LOGGER.info(f"  unbaked size: {size}")
    else:
        size = bounds.size

    # Calculate translation (pivot position) from bounds center
    translation = bounds.get_pivot(pivot)
    boxy_data = BoxyData(
        size=size,
        translation=translation,
        rotation=bounds.rotation,
        pivot_side=pivot,
        color=color,
    )
    LOGGER.info(f"  building boxy with data: {boxy_data.dictionary}")
    _boxy_node = build(boxy_data=boxy_data)
    LOGGER.info(f"  built boxy_node: {_boxy_node}")

    # Apply scale if inheriting
    if inherit_scale and has_scale:
        node_utils.scale(nodes=_boxy_node, value=original_scale)
        LOGGER.info(f"  applied scale: {original_scale}")

    cmds.delete(polycube)
    return _boxy_node


def create_polycube(pivot_side: Side, size: Point3, creation_mode: CreationMode = CreationMode.pivot_origin,
                    construction_history: bool = False) -> str:
    """Create a custom polycube node.

    Doesn't need to be a custom DAG node at this stage as it's a regular mesh transform
    It does feature some custom attributes though
    """
    result = geometry_utils.create_cube(
        size=size,
        position=ZERO3,
        baseline=0.5,
        construction_history=construction_history,
        name="polycube",
    )
    if construction_history:
        polycube, shape = result
    else:
        polycube = result
    pivot_position = {
        Side.top: Point3(0.0, size.y / 2.0, 0.0),
        Side.center: ZERO3,
        Side.bottom: Point3(0.0, -size.y / 2.0, 0.0),
        Side.left: Point3(-size.x / 2, 0.0, 0.0),
        Side.right: Point3(size.x / 2, 0.0, 0.0),
        Side.front: Point3(0.0, 0.0, size.z / 2),
        Side.back: Point3(0.0, 0.0, -size.z / 2),
    }[pivot_side]
    node_utils.set_pivot(nodes=polycube, value=pivot_position, reset=True)
    if creation_mode is CreationMode.pivot_origin:
        node_utils.set_translation(nodes=polycube, value=ZERO3, absolute=True)

    # Add custom attributes
    shape = node_utils.get_shape_from_transform(node=polycube, full_path=True)
    attribute_utils.add_attribute(
        node=shape, attr=CustomAttribute.custom_type.name, data_type=DataType.string,
        lock=True, default_value=CustomType.polycube.name, channel_box=True)
    attribute_utils.add_attribute(
        node=shape, attr=CustomAttribute.pivot_side.name, data_type=DataType.string,
        lock=True, default_value=pivot_side.name, channel_box=True)
    attribute_utils.add_compound_attribute(
        node=shape,
        parent_attr=CustomAttribute.size.name,
        data_type=DataType.float3,
        attrs=("x", "y", "z"),
        default_values=(size.x, size.y, size.z),
        lock=True,
        channel_box=True,
    )

    return polycube


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
        boxy_data.rotation = Point3(boxy_data.rotation.x + rotation, boxy_data.rotation.y, boxy_data.rotation.z)
    elif axis is Axis.y:
        boxy_data.rotation = Point3(boxy_data.rotation.x, boxy_data.rotation.y + rotation, boxy_data.rotation.z)
    else:
        boxy_data.rotation = Point3(boxy_data.rotation.x, boxy_data.rotation.y, boxy_data.rotation.z + rotation)
    cmds.delete(node)
    return build(boxy_data=boxy_data)


def get_boxy_data(node: str) -> BoxyData:
    """Get BoxyData from a boxy node."""
    LOGGER.debug(f"=== get_boxy_data({node}) ===")
    shape = node_utils.get_shape_from_transform(node=node)

    if not shape or cmds.objectType(shape) != "boxyShape":
        raise ValueError(f"Node '{node}' is not a valid boxy node")

    # Get transform position (this is where the pivot is)
    transform_pos = node_utils.get_translation(node)
    LOGGER.debug(f"  transform position: {transform_pos}")

    # Get color from shape attributes
    color = ColorRGB(
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

    pivot = get_boxy_pivot(node=node)
    LOGGER.debug(f"  pivot: {pivot}")

    rotation = node_utils.get_rotation(node)
    LOGGER.debug(f"  transform rotation: {rotation}")

    boxy_data = BoxyData(
        size=size,
        translation=transform_pos,
        rotation=rotation,
        pivot_side=pivot,
        color=color,
    )
    LOGGER.debug(f"  boxy_data.translation: {boxy_data.translation}")
    LOGGER.debug(f"  boxy_data.center: {boxy_data.center}")
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
        return bounds.bottom
    elif pivot == Side.top:
        return bounds.top
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


def get_selected_boxy_positions() -> list[Point3]:
    return [node_utils.get_translation(x, absolute=True) for x in get_selected_boxy_nodes()]


def is_polycube(node: str) -> bool:
    """Check if node is a Robotools polycube by checking custom_type attribute.

    Args:
        node: Transform or shape node name.

    Returns:
        True if the node is a Robotools polycube, False otherwise.
    """
    shape = node_utils.get_shape_from_transform(node=node)
    if not shape:
        return False
    if not cmds.attributeQuery(CustomAttribute.custom_type.name, node=shape, exists=True):
        return False
    return cmds.getAttr(f"{shape}.{CustomAttribute.custom_type.name}") == CustomType.polycube.name


def is_simple_cuboid(node: str) -> bool:
    """Check if mesh is a simple cuboid (6 faces, 8 vertices, no subdivision).

    Used to identify cubes that may have lost their polyCube construction history
    (e.g., duplicated cubes, imported geometry).
    """
    shape = node_utils.get_shape_from_transform(node=node)
    if not shape:
        return False
    # Must be a mesh
    if cmds.objectType(shape) != "mesh":
        return False
    face_count = cmds.polyEvaluate(shape, face=True)
    vertex_count = cmds.polyEvaluate(shape, vertex=True)
    return face_count == 6 and vertex_count == 8


def get_selected_polycubes() -> list[str]:
    """Get a list of all Robotools polycube nodes selected."""
    mesh_nodes = [x for x in node_utils.get_selected_geometry() if not node_utils.is_custom_type_node(x)]
    return [x for x in mesh_nodes if is_polycube(x)]


def rebuild(node: str, pivot: Side | None = None, color: ColorRGB | None = None) -> str | BoxyException:
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
    size = bounds.size
    if has_scale:
        LOGGER.debug(f"  Non-identity scale detected, baking scale into size")
        size = Point3(
            bounds.size.x * scale.x,
            bounds.size.y * scale.y,
            bounds.size.z * scale.z
        )
        # Recreate bounds with scaled size for pivot calculation
        bounds = Bounds(size=size, position=bounds.position, rotation=bounds.rotation)
        LOGGER.debug(f"  Size after baking scale: {size}")
        # Scale will not be restored since it's now baked into size
        scale = Point3(1.0, 1.0, 1.0)

    # Calculate translation (pivot position) from bounds center
    translation = bounds.get_pivot(pivot)
    LOGGER.debug(f"  Translation (pivot position): {translation}")

    cmds.delete(node)
    boxy_data = BoxyData(
        size=size,
        translation=translation,
        rotation=bounds.rotation,
        pivot_side=pivot,
        color=color if color else color_classes.DEEP_GREEN,
    )
    LOGGER.debug(f"  BoxyData created:")
    LOGGER.debug(f"    size: {boxy_data.size}")
    LOGGER.debug(f"    translation: {boxy_data.translation}")
    LOGGER.debug(f"    pivot: {boxy_data.pivot_side}")

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
