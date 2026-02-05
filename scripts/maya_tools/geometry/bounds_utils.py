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
# Utility for finding and calculating axis-aligned bounds from cuboid geometry.
from __future__ import annotations

import logging
from itertools import combinations

import math
from maya import cmds

from core import logging_utils, math_utils
from core.core_enums import ComponentType
from core.math_utils import (
    normalize_vector, dot_product, angle_between_two_vectors,
    radians_to_degrees, are_orthogonal, points_match, normalize_angle
)
from core.point_classes import Point3, Point3Pair, X_AXIS, Y_AXIS, Z_AXIS, ZERO3
from maya_tools import node_utils
from core.bounds import Bounds
from maya_tools.geometry.component_utils import (
    Component, EdgeComponent, FaceComponent, LocatorComponent, VertexComponent,
    components_from_selection
)

LOGGER = logging_utils.get_logger(name=__name__, level=logging.INFO)


class CuboidFinder:
    """
    Finds and calculates axis-aligned bounds from cuboid geometry.

    Accepts various inputs: mesh transform, quad faces, edges, or vertices.
    Can infer a complete cuboid from partial input (e.g., 5 vertices) if the
    provided components define a valid cuboid.

    Calculates:
    - size: axis-aligned dimensions
    - center: world-space center position
    - rotation: Euler XYZ rotation to align with world axes
    """

    TOLERANCE = 0.0001  # Tolerance for vertex position matching
    DECIMAL_PLACES = 4  # Decimal places to round results to

    def __init__(self,
                 transform: str | None = None,
                 faces: list[FaceComponent] | None = None,
                 edges: list[EdgeComponent] | None = None,
                 vertices: list[VertexComponent] | None = None,
                 locators: list[LocatorComponent] | None = None,
                 inherit_scale: bool = False):
        """
        Initialize BoundsFinder.

        Args:
            transform: Mesh transform node name (must have exactly 8 vertices).
            faces: List of FaceComponents (1-6 faces).
            edges: List of EdgeComponents (3-12 edges).
            vertices: List of VertexComponents (5-8 vertices).
            locators: List of LocatorComponents (5-8 locators).
            inherit_scale: If True, calculate bounds from prescaled geometry and store scale separately.

        If no arguments provided, uses the current Maya selection.
        Partial inputs are accepted if they can uniquely define a cuboid.
        """
        self.size: Point3 | None = None
        self.center: Point3 | None = None
        self.rotation: Point3 | None = None
        self.scale: Point3 = Point3(1.0, 1.0, 1.0)
        self.is_valid: bool = False
        self.transform: str | None = None
        self.vertices: list[Point3] = []  # The 8 cuboid vertices
        self.inherit_scale = inherit_scale
        self._original_scale: Point3 | None = None

        # Store original selection state
        state = node_utils.State()

        # Determine input type and extract vertex positions
        input_positions = self._get_vertices_from_input(transform, faces, edges, vertices, locators)

        if input_positions is None or len(input_positions) < 5:
            state.restore()
            return

        # Try to infer complete cuboid from partial input
        cuboid_vertices = self._infer_cuboid_vertices(input_positions)
        if cuboid_vertices is None:
            state.restore()
            return

        self.vertices = cuboid_vertices

        # Validate cuboid and calculate bounds
        if self._validate_and_calculate(cuboid_vertices):
            self.is_valid = True

        state.restore()

    def _get_vertices_from_input(self,
                                  transform: str | None,
                                  faces: list[FaceComponent] | None,
                                  edges: list[EdgeComponent] | None,
                                  vertices: list[VertexComponent] | None,
                                  locators: list[LocatorComponent] | None) -> list[Point3] | None:
        """
        Extract 8 vertex positions from the provided input.

        Returns:
            List of 8 Point3 vertex positions, or None if invalid input.
        """
        # Priority: explicit arguments > selection
        if transform is not None:
            return self._vertices_from_transform(transform)
        elif faces is not None:
            return self._vertices_from_faces(faces)
        elif edges is not None:
            return self._vertices_from_edges(edges)
        elif vertices is not None:
            return self._vertices_from_vertices(vertices)
        elif locators is not None:
            return self._vertices_from_locators(locators)
        else:
            # Fall back to selection
            return self._vertices_from_selection()

    def _vertices_from_transform(self, transform: str) -> list[Point3] | None:
        """Get vertices from a mesh transform."""
        if not cmds.objExists(transform):
            cmds.warning(f"Transform '{transform}' does not exist.")
            return None

        self.transform = transform

        # Handle inherit_scale: store and reset scale before getting vertices
        if self.inherit_scale:
            self._original_scale = node_utils.get_scale(transform)
            self.scale = self._original_scale
            node_utils.scale(nodes=transform, value=Point3(1.0, 1.0, 1.0), absolute=True)

        vertex_count = cmds.polyEvaluate(transform, vertex=True)

        if vertex_count != 8:
            LOGGER.debug(f"Transform must have exactly 8 vertices, got {vertex_count}.")
            # Restore scale if we changed it
            if self.inherit_scale and self._original_scale:
                node_utils.scale(nodes=transform, value=self._original_scale, absolute=True)
            return None

        vertices = [Point3(*cmds.pointPosition(f'{transform}.vtx[{i}]', world=True))
                    for i in range(8)]

        # Restore scale after getting vertices
        if self.inherit_scale and self._original_scale:
            node_utils.scale(nodes=transform, value=self._original_scale, absolute=True)

        return vertices

    def _vertices_from_faces(self, faces: list[FaceComponent]) -> list[Point3] | None:
        """Get vertices from face components."""
        if len(faces) < 1 or len(faces) > 6:
            cmds.warning(f"Expected 1-6 faces, got {len(faces)}.")
            return None

        self.transform = faces[0].transform

        # Handle inherit_scale: store and reset scale before getting vertices
        if self.inherit_scale:
            self._original_scale = node_utils.get_scale(self.transform)
            self.scale = self._original_scale
            node_utils.scale(nodes=self.transform, value=Point3(1.0, 1.0, 1.0), absolute=True)

        vertex_indices = set()

        for face in faces:
            face_verts = cmds.polyListComponentConversion(
                f'{face.transform}.f[{face.idx}]', fromFace=True, toVertex=True)
            indices = cmds.ls(face_verts, flatten=True)
            for idx in indices:
                vertex_indices.add(int(idx.split('[')[1].split(']')[0]))

        result = [Point3(*cmds.pointPosition(f'{self.transform}.vtx[{i}]', world=True))
                for i in sorted(vertex_indices)]

        # Restore scale after getting vertices
        if self.inherit_scale and self._original_scale:
            node_utils.scale(nodes=self.transform, value=self._original_scale, absolute=True)

        LOGGER.debug(f"CuboidFinder._vertices_from_faces:")
        LOGGER.debug(f"  faces: {[(f.transform, f.idx) for f in faces]}")
        LOGGER.debug(f"  vertex_indices: {sorted(vertex_indices)}")
        LOGGER.debug(f"  vertex positions: {result}")
        return result

    def _vertices_from_edges(self, edges: list[EdgeComponent]) -> list[Point3] | None:
        """Get vertices from edge components."""
        if len(edges) < 3 or len(edges) > 12:
            LOGGER.debug(f"CuboidFinder._vertices_from_edges: FAILED - Expected 3-12 edges, got {len(edges)}")
            return None

        self.transform = edges[0].transform

        # Handle inherit_scale: store and reset scale before getting vertices
        if self.inherit_scale:
            self._original_scale = node_utils.get_scale(self.transform)
            self.scale = self._original_scale
            node_utils.scale(nodes=self.transform, value=Point3(1.0, 1.0, 1.0), absolute=True)

        vertex_indices = set()

        for edge in edges:
            edge_verts = cmds.polyListComponentConversion(
                f'{edge.transform}.e[{edge.idx}]', fromEdge=True, toVertex=True)
            indices = cmds.ls(edge_verts, flatten=True)
            for idx in indices:
                vertex_indices.add(int(idx.split('[')[1].split(']')[0]))

        result = [Point3(*cmds.pointPosition(f'{self.transform}.vtx[{i}]', world=True))
                for i in sorted(vertex_indices)]

        # Restore scale after getting vertices
        if self.inherit_scale and self._original_scale:
            node_utils.scale(nodes=self.transform, value=self._original_scale, absolute=True)

        LOGGER.debug(f"CuboidFinder._vertices_from_edges:")
        LOGGER.debug(f"  edges: {[(e.transform, e.idx) for e in edges]}")
        LOGGER.debug(f"  vertex_indices: {sorted(vertex_indices)}")
        LOGGER.debug(f"  vertex positions: {result}")
        return result

    def _vertices_from_vertices(self, vertices: list[VertexComponent]) -> list[Point3] | None:
        """Get vertices from vertex components."""
        if len(vertices) < 5 or len(vertices) > 8:
            LOGGER.debug(f"Expected 5-8 vertices, got {len(vertices)}.")
            return None

        self.transform = vertices[0].transform

        # Handle inherit_scale: store and reset scale before getting vertices
        if self.inherit_scale:
            self._original_scale = node_utils.get_scale(self.transform)
            self.scale = self._original_scale
            node_utils.scale(nodes=self.transform, value=Point3(1.0, 1.0, 1.0), absolute=True)

        result = [Point3(*cmds.pointPosition(f'{v.transform}.vtx[{v.idx}]', world=True))
                  for v in vertices]

        # Restore scale after getting vertices
        if self.inherit_scale and self._original_scale:
            node_utils.scale(nodes=self.transform, value=self._original_scale, absolute=True)

        return result

    def _vertices_from_locators(self, locators: list[LocatorComponent]) -> list[Point3] | None:
        """Get vertex positions from locator world positions."""
        if len(locators) < 5 or len(locators) > 8:
            LOGGER.debug(f"Expected 5-8 locators, got {len(locators)}.")
            return None

        return [Point3(*cmds.xform(loc.transform, query=True, worldSpace=True, translation=True))
                for loc in locators]

    def _vertices_from_selection(self) -> list[Point3] | None:
        """Get vertices from current Maya selection."""
        selection = cmds.ls(sl=True, flatten=True, long=True)

        if not selection:
            raise ValueError("No valid selection.")

        # Check for transform selection
        transforms = cmds.ls(selection, transforms=True)
        if transforms:
            return self._vertices_from_transform(transforms[0])

        # Check for face selection
        face_selection = [s for s in selection if '.f[' in s]
        if face_selection:
            faces = []
            for f in face_selection:
                transform = f.split('.f[')[0]
                idx = int(f.split('[')[1].split(']')[0])
                faces.append(FaceComponent(transform=transform, idx=idx))
            return self._vertices_from_faces(faces)

        # Check for edge selection
        edge_selection = [s for s in selection if '.e[' in s]
        if edge_selection:
            edges = []
            for e in edge_selection:
                transform = e.split('.e[')[0]
                idx = int(e.split('[')[1].split(']')[0])
                edges.append(EdgeComponent(transform=transform, idx=idx))
            return self._vertices_from_edges(edges)

        # Check for vertex selection
        vertex_selection = [s for s in selection if '.vtx[' in s]
        if vertex_selection:
            vertices = []
            for v in vertex_selection:
                transform = v.split('.vtx[')[0]
                idx = int(v.split('[')[1].split(']')[0])
                vertices.append(VertexComponent(transform=transform, idx=idx))
            return self._vertices_from_vertices(vertices)

        raise ValueError("No valid geometry selection found.")

    def _infer_cuboid_vertices(self, input_positions: list[Point3]) -> list[Point3] | None:
        """
        Infer the complete 8 vertices of a cuboid from partial input.

        The algorithm:
        1. Find a corner vertex with 3 orthogonal edge directions
        2. Generate all 8 cuboid vertices from the corner and edge vectors
        3. Validate that all input positions match generated vertices

        Args:
            input_positions: List of 5-8 vertex positions.

        Returns:
            List of 8 Point3 cuboid vertices, or None if invalid.
        """
        # Try each vertex as a potential corner
        for corner_idx, corner in enumerate(input_positions):
            # Find candidate vertices sorted by distance
            other_verts = [v for i, v in enumerate(input_positions) if i != corner_idx]
            distances = [(Point3Pair(corner, v).length, v) for v in other_verts]
            distances.sort(key=lambda x: x[0])

            # Need at least 3 other vertices to define edges
            if len(distances) < 3:
                continue

            # Try combinations of 3 from the closest candidates
            # Use up to 6 closest to handle cases where face diagonals are shorter than edges
            num_candidates = min(6, len(distances))
            candidate_verts = [d[1] for d in distances[:num_candidates]]

            for edge_verts in combinations(candidate_verts, 3):
                edge_vectors = [Point3Pair(corner, v).delta for v in edge_verts]

                # Check if these form orthogonal edges (dot products ≈ 0)
                if not are_orthogonal(edge_vectors):
                    continue

                # Generate all 8 cuboid vertices from corner and edges
                generated = self._generate_cuboid_vertices(corner, edge_vectors)

                # Validate all input positions match generated vertices
                if self._all_inputs_match(input_positions, generated):
                    LOGGER.debug(f"DEBUG CuboidFinder._infer_cuboid_vertices: SUCCESS")
                    LOGGER.debug(f"  input_positions: {input_positions}")
                    LOGGER.debug(f"  generated (inferred 8 vertices): {generated}")
                    return generated

        cmds.warning("Could not infer valid cuboid from input vertices.")
        LOGGER.debug(f"DEBUG CuboidFinder._infer_cuboid_vertices: FAILED to infer cuboid")
        return None

    def _generate_cuboid_vertices(self, corner: Point3, edges: list[Point3]) -> list[Point3]:
        """
        Generate all 8 vertices of a cuboid from one corner and 3 edge vectors.

        Args:
            corner: The corner vertex position.
            edges: List of 3 edge vectors from the corner.

        Returns:
            List of 8 Point3 vertex positions.
        """
        e1, e2, e3 = edges
        vertices = [
            corner,                                                      # 000
            Point3(corner.x + e1.x, corner.y + e1.y, corner.z + e1.z),  # 100
            Point3(corner.x + e2.x, corner.y + e2.y, corner.z + e2.z),  # 010
            Point3(corner.x + e3.x, corner.y + e3.y, corner.z + e3.z),  # 001
            Point3(corner.x + e1.x + e2.x, corner.y + e1.y + e2.y, corner.z + e1.z + e2.z),  # 110
            Point3(corner.x + e1.x + e3.x, corner.y + e1.y + e3.y, corner.z + e1.z + e3.z),  # 101
            Point3(corner.x + e2.x + e3.x, corner.y + e2.y + e3.y, corner.z + e2.z + e3.z),  # 011
            Point3(corner.x + e1.x + e2.x + e3.x, corner.y + e1.y + e2.y + e3.y, corner.z + e1.z + e2.z + e3.z),  # 111
        ]
        return vertices

    def _all_inputs_match(self, inputs: list[Point3], generated: list[Point3]) -> bool:
        """Check if all input positions match generated vertices with 1:1 correspondence."""
        # For 8 inputs, verify bidirectional matching (each input matches exactly one generated)
        if len(inputs) == 8:
            matched_generated = set()
            for inp in inputs:
                found_match = False
                for idx, gen in enumerate(generated):
                    if idx not in matched_generated and points_match(inp, gen):
                        matched_generated.add(idx)
                        found_match = True
                        break
                if not found_match:
                    return False
            # All 8 generated vertices should be matched
            return len(matched_generated) == 8

        # For partial inputs (5-7), just verify each input matches some generated vertex
        for inp in inputs:
            matched = False
            for gen in generated:
                if points_match(inp, gen):
                    matched = True
                    break
            if not matched:
                return False
        return True

    def _validate_cuboid_vertices(self, vertices: list[Point3]) -> bool:
        """Validate that 8 vertices form a valid cuboid."""
        if len(vertices) != 8:
            return False

        # Check that we can find orthogonal edges from any vertex
        v0 = vertices[0]
        distances = [(Point3Pair(v0, v).length, v) for v in vertices[1:]]
        distances.sort(key=lambda x: x[0])

        edge_verts = [d[1] for d in distances[:3]]
        edge_vectors = [Point3Pair(v0, v).delta for v in edge_verts]

        return are_orthogonal(edge_vectors)

    def _validate_and_calculate(self, vertex_positions: list[Point3]) -> bool:
        """
        Validate the vertices form a cuboid and calculate bounds.

        Args:
            vertex_positions: List of 8 Point3 positions.

        Returns:
            True if valid cuboid and calculations succeeded.
        """
        # Calculate center as centroid (average of all 8 vertices)
        # For rotated cuboids, this is correct - the midpoint of axis-aligned bbox is wrong!
        sum_x = sum(v.x for v in vertex_positions)
        sum_y = sum(v.y for v in vertex_positions)
        sum_z = sum(v.z for v in vertex_positions)
        num_verts = len(vertex_positions)
        self.center = Point3(
            round(sum_x / num_verts, self.DECIMAL_PLACES),
            round(sum_y / num_verts, self.DECIMAL_PLACES),
            round(sum_z / num_verts, self.DECIMAL_PLACES)
        )
        LOGGER.debug(f"DEBUG CuboidFinder._validate_and_calculate:")
        LOGGER.debug(f"  vertex_positions count: {num_verts}")
        LOGGER.debug(f"  vertex_positions: {vertex_positions}")
        LOGGER.debug(f"  center (centroid, unscaled): {self.center}")

        # Transform center from unscaled space to world space if inherit_scale is True
        if self.inherit_scale and self.transform and self._original_scale:
            pivot_position = node_utils.get_translation(node=self.transform, absolute=True)
            LOGGER.debug(f"  pivot_position: {pivot_position}")
            LOGGER.debug(f"  original_scale: {self._original_scale}")
            # Scale the offset from pivot
            offset = Point3(
                self.center.x - pivot_position.x,
                self.center.y - pivot_position.y,
                self.center.z - pivot_position.z
            )
            scaled_offset = Point3(
                offset.x * self._original_scale.x,
                offset.y * self._original_scale.y,
                offset.z * self._original_scale.z
            )
            self.center = Point3(
                round(pivot_position.x + scaled_offset.x, self.DECIMAL_PLACES),
                round(pivot_position.y + scaled_offset.y, self.DECIMAL_PLACES),
                round(pivot_position.z + scaled_offset.z, self.DECIMAL_PLACES)
            )
            LOGGER.debug(f"  center (after scale transform): {self.center}")

        # Collect all valid rotation results from corners
        valid_results = []

        for corner in vertex_positions:
            edge_data = self._get_edge_vectors_from_corner(vertex_positions, corner)
            if not edge_data:
                continue

            axis_assignment = self._assign_edges_to_axes(edge_data)
            if not axis_assignment:
                continue

            rotation = self._calculate_xyz_rotation(axis_assignment)
            valid_results.append((axis_assignment, rotation))

        if not valid_results:
            return False

        # Get the transform's rotation if available
        transform_rotation = self._get_transform_rotation() if self.transform else None

        # First, check if any calculated rotation matches the transform's rotation
        best_result = None
        calculated_rotation_for_match = None
        if transform_rotation:
            for axis_assignment, rotation in valid_results:
                if self._rotations_match(rotation, transform_rotation):
                    best_result = (axis_assignment, transform_rotation)
                    calculated_rotation_for_match = rotation
                    LOGGER.debug(f"Using transform rotation: {transform_rotation}")
                    LOGGER.debug(f"  (matched with calculated rotation: {rotation})")
                    break

        # If no match with transform rotation, pick the simplest rotation
        if not best_result:
            best_rotation_complexity = float('inf')
            for axis_assignment, rotation in valid_results:
                complexity = abs(rotation.x) + abs(rotation.y) + abs(rotation.z)
                if complexity < best_rotation_complexity:
                    best_rotation_complexity = complexity
                    best_result = (axis_assignment, rotation)

        axis_assignment, rotation = best_result

        # Calculate size from edge lengths
        size_x = axis_assignment['x']['length']
        size_y = axis_assignment['y']['length']
        size_z = axis_assignment['z']['length']

        # If using transform rotation that differs from calculated rotation by 90°,
        # swap dimensions (because the local axes are swapped)
        if calculated_rotation_for_match is not None:
            x_diff = normalize_angle(rotation.x - calculated_rotation_for_match.x)
            y_diff = normalize_angle(rotation.y - calculated_rotation_for_match.y)
            z_diff = normalize_angle(rotation.z - calculated_rotation_for_match.z)

            LOGGER.debug(f"  Rotation diffs: X={x_diff}°, Y={y_diff}°, Z={z_diff}°")
            LOGGER.debug(f"    (transform: {rotation}, calculated: {calculated_rotation_for_match})")

            # 90° Y-rotation difference: swap X and Z
            if abs(abs(y_diff) - 90) < 1.0:
                LOGGER.debug(f"  Swapping X and Z dimensions due to 90° Y rotation difference")
                size_x, size_z = size_z, size_x

            # 90° Z-rotation difference: swap X and Y
            if abs(abs(z_diff) - 90) < 1.0:
                LOGGER.debug(f"  Swapping X and Y dimensions due to 90° Z rotation difference")
                size_x, size_y = size_y, size_x

            # 90° X-rotation difference: swap Y and Z
            if abs(abs(x_diff) - 90) < 1.0:
                LOGGER.debug(f"  Swapping Y and Z dimensions due to 90° X rotation difference")
                size_y, size_z = size_z, size_y

        self.size = Point3(
            round(size_x, self.DECIMAL_PLACES),
            round(size_y, self.DECIMAL_PLACES),
            round(size_z, self.DECIMAL_PLACES)
        )

        # Store rotation (rounded)
        self.rotation = Point3(
            round(rotation.x, self.DECIMAL_PLACES),
            round(rotation.y, self.DECIMAL_PLACES),
            round(rotation.z, self.DECIMAL_PLACES)
        )

        LOGGER.debug(f"DEBUG _validate_and_calculate FINAL RESULT:")
        LOGGER.debug(f"  size: {self.size}")
        LOGGER.debug(f"  center: {self.center}")
        LOGGER.debug(f"  rotation: {self.rotation}")
        LOGGER.debug(f"  transform rotation: {self._get_transform_rotation() if self.transform else 'N/A'}")

        return True

    def _rotate_size_for_transform(self, size: Point3, rotation: Point3) -> Point3:
        """
        Adjust size dimensions to match the transform's local coordinate system.

        For 90-degree rotations, this swaps dimensions appropriately.
        """
        # Normalize rotation angles to 0, 90, 180, 270
        def normalize_90(angle: float) -> int:
            return round(angle / 90) % 4 * 90

        rx = normalize_90(rotation.x)
        ry = normalize_90(rotation.y)
        rz = normalize_90(rotation.z)

        # Start with world-aligned size
        sx, sy, sz = size.x, size.y, size.z

        # Apply Y rotation (swaps X and Z)
        if ry in (90, 270, -90, -270):
            sx, sz = sz, sx

        # Apply X rotation (swaps Y and Z)
        if rx in (90, 270, -90, -270):
            sy, sz = sz, sy

        # Apply Z rotation (swaps X and Y)
        if rz in (90, 270, -90, -270):
            sx, sy = sy, sx

        return Point3(sx, sy, sz)

    def _is_axis_aligned_rotation(self, rotation: Point3) -> bool:
        """Check if rotation is effectively zero (axis-aligned vertices)."""
        tolerance = 0.01
        return (abs(rotation.x) < tolerance and
                abs(rotation.y) < tolerance and
                abs(rotation.z) < tolerance)

    def _is_90_degree_rotation(self, rotation: Point3) -> bool:
        """Check if rotation values are multiples of 90 degrees."""
        def is_90_multiple(angle: float) -> bool:
            # Normalize to 0-360 range and check if close to 0, 90, 180, or 270
            normalized = abs(angle) % 360
            return any(abs(normalized - mult) < 0.01 for mult in [0, 90, 180, 270])

        return (is_90_multiple(rotation.x) and
                is_90_multiple(rotation.y) and
                is_90_multiple(rotation.z))

    def _rotations_match(self, rotation_a: Point3, rotation_b: Point3, tolerance: float = 1.0) -> bool:
        """Check if two rotations represent the same cuboid orientation.

        For cuboids, rotations that differ by 90° multiples on any axis are equivalent
        because a cuboid has 90° rotational symmetry.

        Args:
            rotation_a: First rotation in degrees.
            rotation_b: Second rotation in degrees.
            tolerance: Angle tolerance in degrees.

        Returns:
            True if rotations are equivalent within tolerance (accounting for 90° symmetry).
        """
        def angles_match_with_90_symmetry(a: float, b: float) -> bool:
            """Check if angles match, accounting for 90° cuboid symmetry."""
            diff = normalize_angle(a - b)
            # Check if difference is close to 0, ±90, ±180, ±270
            for offset in [0, 90, -90, 180, -180, 270, -270]:
                if abs(diff - offset) < tolerance:
                    return True
            return False

        return (angles_match_with_90_symmetry(rotation_a.x, rotation_b.x) and
                angles_match_with_90_symmetry(rotation_a.y, rotation_b.y) and
                angles_match_with_90_symmetry(rotation_a.z, rotation_b.z))

    def _get_transform_rotation(self) -> Point3 | None:
        """Get the rotation values from the transform node."""
        if not self.transform or not cmds.objExists(self.transform):
            return None

        try:
            rot = cmds.getAttr(f'{self.transform}.rotate')[0]
            return Point3(
                round(rot[0], self.DECIMAL_PLACES),
                round(rot[1], self.DECIMAL_PLACES),
                round(rot[2], self.DECIMAL_PLACES)
            )
        except (ValueError, RuntimeError):
            return None

    def _get_edge_directions(self, vertex_positions: list[Point3]) -> list[Point3] | None:
        """
        Find the 3 principal edge directions of the cuboid.

        For a cuboid, each vertex connects to exactly 3 other vertices via edges.
        We find one vertex and its 3 neighbors to determine the edge directions.

        Returns:
            List of 3 normalized edge direction vectors, or None if invalid.
        """
        # Find edges by checking distances - cuboid edges are the 3 shortest unique distances from any vertex
        v0 = vertex_positions[0]
        distances = []

        for i, v in enumerate(vertex_positions[1:], 1):
            dist = Point3Pair(v0, v).length
            distances.append((dist, i, v))

        # Sort by distance
        distances.sort(key=lambda x: x[0])

        # The 3 shortest distances should be the edges (not face diagonals or space diagonal)
        # For a valid cuboid, first 3 are edges, next 3 are face diagonals, last is space diagonal
        if len(distances) < 3:
            return None

        edge_vectors = []
        for dist, idx, v in distances[:3]:
            direction = Point3Pair(v0, v).delta
            edge_vectors.append(normalize_vector(direction))

        return edge_vectors

    def _get_edge_vectors_with_lengths(self, vertex_positions: list[Point3]) -> list[dict] | None:
        """
        Find the 3 principal edge vectors with their lengths.

        Returns:
            List of dicts with 'vector' (normalized), 'length', and 'raw' (unnormalized) keys,
            or None if invalid.
        """
        v0 = vertex_positions[0]
        distances = []

        for i, v in enumerate(vertex_positions[1:], 1):
            pair = Point3Pair(v0, v)
            distances.append((pair.length, i, v, pair.delta))

        distances.sort(key=lambda x: x[0])

        if len(distances) < 3:
            return None

        edge_data = []
        for dist, idx, v, delta in distances[:3]:
            edge_data.append({
                'vector': normalize_vector(delta),
                'length': dist,
                'raw': delta
            })

        return edge_data

    def _get_edge_vectors_from_corner(self, vertex_positions: list[Point3], corner: Point3) -> list[dict] | None:
        """
        Find the 3 principal edge vectors from a specific corner vertex.

        Args:
            vertex_positions: List of 8 Point3 vertex positions.
            corner: The corner vertex to use as reference.

        Returns:
            List of dicts with 'vector' (normalized), 'length', and 'raw' keys,
            or None if invalid.
        """
        distances = []

        for v in vertex_positions:
            # Use tolerance-based comparison for Point3
            if points_match(v, corner):
                continue
            pair = Point3Pair(corner, v)
            distances.append((pair.length, v, pair.delta))

        distances.sort(key=lambda x: x[0])

        if len(distances) < 3:
            return None

        # Try combinations to find 3 orthogonal edges (handles case where face diagonal < longest edge)
        num_candidates = min(6, len(distances))
        for combo in combinations(range(num_candidates), 3):
            edges = [distances[i] for i in combo]
            vectors = [Point3Pair(corner, e[1]).delta for e in edges]

            if are_orthogonal(vectors):
                edge_data = []
                for dist, v, delta in edges:
                    edge_data.append({
                        'vector': normalize_vector(delta),
                        'length': dist,
                        'raw': delta
                    })
                return edge_data

        return None

    def _assign_edges_to_axes(self, edge_data: list[dict]) -> dict | None:
        """
        Assign each edge to the world axis it's most aligned with.

        Args:
            edge_data: List of edge dicts from _get_edge_vectors_with_lengths.

        Returns:
            Dict with 'x', 'y', 'z' keys, each containing the assigned edge data,
            or None if assignment fails.
        """
        world_axes = [
            ('x', X_AXIS),
            ('y', Y_AXIS),
            ('z', Z_AXIS)
        ]

        assignment = {}
        used_edges = set()

        # For each world axis, find the edge most aligned with it
        for axis_name, axis_vector in world_axes:
            best_edge_idx = None
            best_alignment = -1

            for i, edge in enumerate(edge_data):
                if i in used_edges:
                    continue

                # Use absolute dot product (edge could point in either direction)
                alignment = abs(dot_product(edge['vector'], axis_vector))

                if alignment > best_alignment:
                    best_alignment = alignment
                    best_edge_idx = i

            if best_edge_idx is None:
                return None

            used_edges.add(best_edge_idx)
            edge = edge_data[best_edge_idx]

            # Ensure vector points in positive axis direction
            dp = dot_product(edge['vector'], axis_vector)
            if dp < 0:
                vector = Point3(-edge['vector'].x, -edge['vector'].y, -edge['vector'].z)
            else:
                vector = edge['vector']

            assignment[axis_name] = {
                'vector': vector,
                'length': edge['length']
            }
            LOGGER.debug(f"  Axis '{axis_name}': edge_idx={best_edge_idx}, alignment={best_alignment:.4f}, "
                         f"vector={vector}, length={edge['length']:.4f}")

        LOGGER.debug(f"DEBUG _assign_edges_to_axes result:")
        for axis_name in ['x', 'y', 'z']:
            LOGGER.debug(f"  {axis_name}: vector={assignment[axis_name]['vector']}, "
                         f"length={assignment[axis_name]['length']:.4f}")
        return assignment

    def _calculate_xyz_rotation(self, axis_assignment: dict) -> Point3:
        """
        Calculate Euler XYZ rotation from axis assignment.

        The edge vectors form the columns of the rotation matrix R.
        Maya uses XYZ rotation order meaning R = Rz * Ry * Rx.

        Args:
            axis_assignment: Dict with 'x', 'y', 'z' axis assignments.

        Returns:
            Point3 with X, Y, Z rotation in degrees.
        """
        edge_x = axis_assignment['x']['vector']
        edge_y = axis_assignment['y']['vector']
        edge_z = axis_assignment['z']['vector']

        LOGGER.debug(f"DEBUG _calculate_xyz_rotation:")
        LOGGER.debug(f"  edge_x (assigned to X axis): {edge_x}")
        LOGGER.debug(f"  edge_y (assigned to Y axis): {edge_y}")
        LOGGER.debug(f"  edge_z (assigned to Z axis): {edge_z}")

        # Euler XYZ decomposition for R = Rz * Ry * Rx
        # edge_x, edge_y, edge_z are columns of R
        # R[2][0] = -sin(y) = edge_x.z
        # R[2][1] = cos(y)*sin(x) = edge_y.z
        # R[2][2] = cos(y)*cos(x) = edge_z.z
        # R[1][0] = sin(z)*cos(y) = edge_x.y
        # R[0][0] = cos(z)*cos(y) = edge_x.x

        # Y rotation: sin(y) = -edge_x.z
        sin_y = max(-1, min(1, -edge_x.z))
        y_rotation = math.asin(sin_y)
        cos_y = math.cos(y_rotation)

        if abs(cos_y) > 0.001:
            # X rotation: atan2(edge_y.z, edge_z.z)
            x_rotation = math.atan2(edge_y.z, edge_z.z)

            # Z rotation: atan2(edge_x.y, edge_x.x)
            z_rotation = math.atan2(edge_x.y, edge_x.x)
        else:
            # Gimbal lock: Y is ±90°, X and Z are coupled
            x_rotation = math.atan2(-edge_y.x, edge_y.y)
            z_rotation = 0.0

        result = Point3(
            radians_to_degrees(x_rotation),
            radians_to_degrees(y_rotation),
            radians_to_degrees(z_rotation)
        )
        LOGGER.debug(f"  Calculated rotation: {result}")
        return result

    def _calculate_y_rotation(self, edge_directions: list[Point3]) -> float:
        """
        Calculate the Y-axis rotation needed to align the cuboid with world axes.

        We find the edge direction that is most horizontal (smallest Y component)
        and calculate the angle to align it with either X or Z axis.

        Args:
            edge_directions: List of 3 normalized edge vectors.

        Returns:
            Y rotation in degrees.
        """
        # Find the most horizontal edge (smallest absolute Y component)
        horizontal_edges = [(abs(e.y), e) for e in edge_directions]
        horizontal_edges.sort(key=lambda x: x[0])

        # Get the most horizontal edge
        _, horizontal_edge = horizontal_edges[0]

        # Project to XZ plane
        xz_edge = Point3(horizontal_edge.x, 0, horizontal_edge.z)
        if xz_edge.magnitude < 0.001:
            # Edge is vertical, no Y rotation needed
            return 0.0

        xz_edge = normalize_vector(xz_edge)

        # Calculate angle to Z axis (or X axis, depending on which is closer)
        angle_to_z = angle_between_two_vectors(xz_edge, Z_AXIS, ref_axis=Y_AXIS)
        angle_to_x = angle_between_two_vectors(xz_edge, X_AXIS, ref_axis=Y_AXIS)

        # Use the smaller rotation
        if abs(angle_to_z) < abs(angle_to_x):
            return radians_to_degrees(angle_to_z)
        else:
            return radians_to_degrees(angle_to_x)


def get_cuboid(
        geometry: str | list[Component] | list[str] | None = None,
        inherit_scale: bool = False
) -> Bounds | None:
    """Get the bounds of the input geometry.

    Args:
        geometry: A transform name, list of Component objects, list of strings
                  (locator names or component ranges like 'mesh.vtx[0:5]'), or None to use selection.
        inherit_scale: If True, bounds are calculated from the prescaled geometry and the
                      transform's scale is returned separately. If False (default), scale is baked.

    Returns:
        Bounds | None if invalid.
    """
    # If nothing passed, get components from current selection
    if geometry is None:
        geometry = components_from_selection()
        if not geometry:
            return None

    transform = None
    faces = None
    edges = None
    vertices = None
    locators = None

    if isinstance(geometry, str):
        if node_utils.is_boxy(node=geometry):
            # For boxy nodes, get center from BoxyData
            from maya_tools.utilities.boxy.boxy_utils import get_boxy_data
            boxy_data = get_boxy_data(node=geometry)
            scale = node_utils.get_scale(geometry) if inherit_scale else Point3(1.0, 1.0, 1.0)
            return Bounds(size=boxy_data.size, position=boxy_data.center, rotation=boxy_data.rotation, scale=scale)
        transform = geometry
    elif isinstance(geometry, list) and geometry:
        # Check if list contains strings - convert via components_from_selection
        if isinstance(geometry[0], str):
            geometry = components_from_selection(geometry)
            if not geometry:
                return None

        # Use component_type property to determine type
        component_type = geometry[0].component_type
        if component_type == ComponentType.face:
            faces = geometry
        elif component_type == ComponentType.edge:
            edges = geometry
        elif component_type == ComponentType.vertex:
            vertices = geometry
        elif component_type == ComponentType.object:
            # For object components, use the transform name
            transform = geometry[0].transform
        elif component_type == ComponentType.locator:
            locators = geometry

    finder = CuboidFinder(transform=transform, faces=faces, edges=edges, vertices=vertices, locators=locators,
                          inherit_scale=inherit_scale)

    if not finder.is_valid:
        LOGGER.debug(f"DEBUG get_cuboid: CuboidFinder is_valid=False, returning None")
        return None

    LOGGER.debug(f"DEBUG get_cuboid: returning Bounds")
    LOGGER.debug(f"  size: {finder.size}")
    LOGGER.debug(f"  center: {finder.center}")
    LOGGER.debug(f"  rotation: {finder.rotation}")
    LOGGER.debug(f"  scale: {finder.scale}")
    return Bounds(size=finder.size, position=finder.center, rotation=finder.rotation, scale=finder.scale)


def get_bounds(
        geometry: str | list[Component] | list[str] | None = None,
        inherit_rotations: bool = False,
        inherit_scale: bool = False
) -> Bounds | None:
    """Get the axis-aligned bounding box of the input geometry.

    Args:
        geometry: A transform name, list of transform names, list of Component objects,
                  list of strings (component ranges like 'mesh.vtx[0:5]'), or None to use selection.
        inherit_rotations: If True and all geometry originates from a single transform,
                          bounds are calculated in object-space and the transform's rotation
                          is inherited. If False (default) or multiple transforms, bounds are
                          calculated in world-space with zero rotation.
        inherit_scale: If True and all geometry originates from a single transform,
                      bounds are calculated from the prescaled geometry and the transform's
                      scale is returned separately. If False (default), scale is baked into size.

    Returns:
        Bounds with size, center position, rotation, and scale. None if invalid.
    """
    if geometry is None:
        geometry = components_from_selection()
        if not geometry:
            return None

    positions: list[Point3] = []
    node: str | None = None
    rotation = Point3(0.0, 0.0, 0.0)

    # Case 1: Single transform string
    if isinstance(geometry, str):
        node = geometry
        scale = Point3(1.0, 1.0, 1.0)
        original_scale = None

        if inherit_rotations or inherit_scale:
            # Get the original center position before any modifications
            orig_bbox = cmds.exactWorldBoundingBox(geometry)
            position = Point3(
                (orig_bbox[0] + orig_bbox[3]) / 2,
                (orig_bbox[1] + orig_bbox[4]) / 2,
                (orig_bbox[2] + orig_bbox[5]) / 2
            )

            # Store original values
            pivot_position = node_utils.get_translation(node=node, absolute=True)
            rotation = node_utils.get_rotation(node=node) if inherit_rotations else Point3(0.0, 0.0, 0.0)
            original_rotation = node_utils.get_rotation(node=node)

            if inherit_scale:
                original_scale = node_utils.get_scale(node=node)
                scale = original_scale

            # Reset rotation first (order: rotation then scale)
            if inherit_rotations:
                node_utils.set_pivot(nodes=node, value=position, reset=False)
                node_utils.set_rotation(nodes=node, value=ZERO3)

            # Reset scale after rotation
            if inherit_scale:
                node_utils.scale(nodes=node, value=Point3(1.0, 1.0, 1.0), absolute=True)

            # Get object-space size
            min_x, min_y, min_z, max_x, max_y, max_z = cmds.exactWorldBoundingBox(geometry)
            size = Point3(max_x - min_x, max_y - min_y, max_z - min_z)

            # Restore (reverse order: scale then rotation)
            if inherit_scale:
                node_utils.scale(nodes=node, value=original_scale, absolute=True)
            if inherit_rotations:
                node_utils.set_rotation(nodes=node, value=original_rotation)
                node_utils.set_pivot(nodes=node, value=pivot_position, reset=False)

            return Bounds(size=size, position=position, rotation=rotation, scale=scale)
        else:
            min_x, min_y, min_z, max_x, max_y, max_z = cmds.exactWorldBoundingBox(geometry)
            size = Point3(max_x - min_x, max_y - min_y, max_z - min_z)
            position = Point3((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2)
            return Bounds(size=size, position=position, rotation=rotation)

    # Case 2: List input
    if isinstance(geometry, list) and geometry:
        # Check if list contains strings
        if isinstance(geometry[0], str):
            # Could be transform names or component strings
            # Try as transforms first
            if cmds.objExists(geometry[0]) and cmds.ls(geometry[0], transforms=True):
                if len(geometry) == 1:
                    # Single transform - pass through inherit_rotations and inherit_scale
                    return get_bounds(geometry[0], inherit_rotations=inherit_rotations, inherit_scale=inherit_scale)
                else:
                    # Multiple transforms - always world-space
                    return get_bounds_from_bounding_box(geometry=geometry)
            # Otherwise convert to components
            geometry = components_from_selection(geometry)
            if not geometry:
                return None

        # Now we have Component objects - check if all from single transform
        transforms = set(c.transform for c in geometry)
        single_transform = len(transforms) == 1
        component_type = geometry[0].component_type

        if component_type == ComponentType.object:
            transforms_list = [c.transform for c in geometry]
            if len(transforms_list) == 1:
                return get_bounds(transforms_list[0], inherit_rotations=inherit_rotations, inherit_scale=inherit_scale)
            return get_bounds_from_bounding_box(geometry=transforms_list)

        elif component_type == ComponentType.locator:
            # Locators don't have mesh rotation to inherit
            for loc in geometry:
                pos = cmds.xform(loc.transform, query=True, worldSpace=True, translation=True)
                positions.append(Point3(*pos))
        else:
            # vertex, edge, face components
            if single_transform:
                node = transforms.pop()

            # Helper to collect positions based on component type
            def collect_positions():
                collected = []
                if component_type == ComponentType.vertex:
                    for v in geometry:
                        pos = cmds.pointPosition(f'{v.transform}.vtx[{v.idx}]', world=True)
                        collected.append(Point3(*pos))
                elif component_type == ComponentType.edge:
                    for edge in geometry:
                        edge_verts = cmds.polyListComponentConversion(
                            f'{edge.transform}.e[{edge.idx}]', fromEdge=True, toVertex=True)
                        for vtx in cmds.ls(edge_verts, flatten=True):
                            pos = cmds.pointPosition(vtx, world=True)
                            collected.append(Point3(*pos))
                elif component_type == ComponentType.face:
                    for face in geometry:
                        face_verts = cmds.polyListComponentConversion(
                            f'{face.transform}.f[{face.idx}]', fromFace=True, toVertex=True)
                        for vtx in cmds.ls(face_verts, flatten=True):
                            pos = cmds.pointPosition(vtx, world=True)
                            collected.append(Point3(*pos))
                return collected

            if (inherit_rotations or inherit_scale) and single_transform:
                # Store transform's pivot position and rotation
                pivot_position = node_utils.get_translation(node=node, absolute=True)
                original_rotation = node_utils.get_rotation(node=node)
                rotation = original_rotation if inherit_rotations else Point3(0.0, 0.0, 0.0)
                scale = Point3(1.0, 1.0, 1.0)
                original_scale = None

                LOGGER.debug(f"get_bounds (component): node={node}")
                LOGGER.debug(f"  pivot_position={pivot_position}")
                LOGGER.debug(f"  original_rotation={original_rotation}")
                LOGGER.debug(f"  inherit_rotations={inherit_rotations}, inherit_scale={inherit_scale}")

                if inherit_scale:
                    original_scale = node_utils.get_scale(node=node)
                    scale = original_scale
                    LOGGER.debug(f"  original_scale={original_scale}")

                # Zero rotation first (order: rotation then scale)
                if inherit_rotations:
                    node_utils.set_rotation(nodes=node, value=ZERO3)

                # Zero scale after rotation
                if inherit_scale:
                    node_utils.scale(nodes=node, value=Point3(1.0, 1.0, 1.0), absolute=True)

                # Collect positions with zeroed rotation/scale
                positions = collect_positions()
                LOGGER.debug(f"  collected positions (unscaled): {positions}")

                # Calculate bounds center in zeroed-rotation space
                min_x = min(p.x for p in positions)
                min_y = min(p.y for p in positions)
                min_z = min(p.z for p in positions)
                max_x = max(p.x for p in positions)
                max_y = max(p.y for p in positions)
                max_z = max(p.z for p in positions)

                size = Point3(max_x - min_x, max_y - min_y, max_z - min_z)
                bounds_position = Point3(
                    (min_x + max_x) / 2,
                    (min_y + max_y) / 2,
                    (min_z + max_z) / 2
                )
                LOGGER.debug(f"  size={size}")
                LOGGER.debug(f"  bounds_position (unscaled)={bounds_position}")

                # Restore (reverse order: scale then rotation)
                if inherit_scale:
                    node_utils.scale(nodes=node, value=original_scale, absolute=True)
                if inherit_rotations:
                    node_utils.set_rotation(nodes=node, value=original_rotation)

                # Transform bounds_position back to world space
                # First apply scale (relative to pivot), then rotation
                if inherit_scale:
                    # Scale the offset from pivot
                    offset = Point3(
                        bounds_position.x - pivot_position.x,
                        bounds_position.y - pivot_position.y,
                        bounds_position.z - pivot_position.z
                    )
                    scaled_offset = Point3(
                        offset.x * scale.x,
                        offset.y * scale.y,
                        offset.z * scale.z
                    )
                    bounds_position = Point3(
                        pivot_position.x + scaled_offset.x,
                        pivot_position.y + scaled_offset.y,
                        pivot_position.z + scaled_offset.z
                    )
                    LOGGER.debug(f"  bounds_position (after scale)={bounds_position}")

                # Then apply rotation
                position = math_utils.apply_euler_xyz_rotation(
                    point=bounds_position,
                    rotation=rotation,
                    pivot=pivot_position
                )
                LOGGER.debug(f"  final position={position}")

                return Bounds(size=size, position=position, rotation=rotation, scale=scale)
            else:
                # World-space calculation
                positions = collect_positions()

    if not positions:
        return None

    # Calculate min/max from positions (world-space case)
    min_x = min(p.x for p in positions)
    min_y = min(p.y for p in positions)
    min_z = min(p.z for p in positions)
    max_x = max(p.x for p in positions)
    max_y = max(p.y for p in positions)
    max_z = max(p.z for p in positions)

    size = Point3(max_x - min_x, max_y - min_y, max_z - min_z)
    position = Point3((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2)

    return Bounds(size=size, position=position, rotation=rotation)


def get_bounds_from_bounding_box(geometry: str | list[str]) -> Bounds:
    """Get axis-aligned Bounds from geometry using Maya's exactWorldBoundingBox.

    Args:
        geometry: A transform name or list of transform names.

    Returns:
        Bounds with axis-aligned size, center position, and zero rotation.
    """
    min_x, min_y, min_z, max_x, max_y, max_z = cmds.exactWorldBoundingBox(geometry)
    size = Point3(max_x - min_x, max_y - min_y, max_z - min_z)
    position = Point3((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2)
    return Bounds(size=size, position=position, rotation=Point3(0.0, 0.0, 0.0))
