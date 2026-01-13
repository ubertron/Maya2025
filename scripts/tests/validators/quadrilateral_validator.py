"""Validator for quadrilateral faces in Maya scenes."""

from __future__ import annotations

import math
from maya import cmds
from core.point_classes import Point3, Point3Pair


def validate_quadrilateral(transform: str, face_index: int,
                          check_coplanar: bool = True,
                          check_right_angles: bool = True,
                          angle_tolerance: float = 1.0,
                          coplanar_tolerance: float = 0.0001) -> tuple[bool, str]:
    """
    Validate that a face in a Maya scene is a valid quadrilateral.

    Args:
        transform: The transform node name
        face_index: The face index to validate
        check_coplanar: Whether to check if vertices are co-planar
        check_right_angles: Whether to check if all corner angles are 90 degrees
        angle_tolerance: Tolerance in degrees for right angle check
        coplanar_tolerance: Tolerance for co-planarity check

    Returns:
        A tuple of (is_valid, message) where is_valid is True if the face is a valid quad,
        and message contains details about the validation result
    """
    # Store the current selection
    original_selection = cmds.ls(selection=True)

    try:
        # Check that the object exists
        if not cmds.objExists(transform):
            return False, f"Object '{transform}' does not exist"

        # Check that the object has a valid mesh node
        mesh_shape = get_mesh_shape(transform)
        if not mesh_shape:
            return False, f"Object '{transform}' does not have a valid mesh node"

        # Get the total number of faces
        face_count = cmds.polyEvaluate(mesh_shape, face=True)
        if face_index < 0 or face_index >= face_count:
            return False, f"Face index {face_index} is out of range (0-{face_count-1})"

        # Get the vertices of the specified face
        face_name = f"{mesh_shape}.f[{face_index}]"
        vertex_indices = get_face_vertices(face_name)

        # Check that the face has exactly four vertices
        if len(vertex_indices) != 4:
            return False, f"Face {face_index} has {len(vertex_indices)} vertices, expected 4"

        # Get vertex positions
        vertex_positions = get_vertex_positions(mesh_shape, vertex_indices)

        # Check co-planarity
        if check_coplanar:
            is_coplanar, coplanar_msg = check_vertices_coplanar(vertex_positions, coplanar_tolerance)
            if not is_coplanar:
                return False, f"Face {face_index} vertices are not co-planar: {coplanar_msg}"

        # Check right angles
        if check_right_angles:
            are_right_angles, angle_msg = check_all_right_angles(vertex_positions, angle_tolerance)
            if not are_right_angles:
                return False, f"Face {face_index} does not have right angles: {angle_msg}"

        # If we've made it this far, the face is a valid quadrilateral
        return True, f"Face {face_index} is a valid quadrilateral with 4 vertices"

    finally:
        # Restore the original selection
        if original_selection:
            cmds.select(original_selection, replace=True)
        else:
            cmds.select(clear=True)


def get_mesh_shape(transform: str) -> str | None:
    """
    Get the mesh shape node from a transform.

    Args:
        transform: The transform node name

    Returns:
        The mesh shape node name, or None if no mesh is found
    """
    # Check if the node is already a mesh
    if cmds.objectType(transform) == "mesh":
        return transform

    # Get the shape nodes under this transform
    shapes = cmds.listRelatives(transform, shapes=True, fullPath=True)
    if not shapes:
        return None

    # Find the first mesh shape
    for shape in shapes:
        if cmds.objectType(shape) == "mesh":
            return shape

    return None


def get_face_vertices(face_name: str) -> list[int]:
    """
    Get the vertex indices for a face in winding order.

    Args:
        face_name: The face component name (e.g., "pCube1.f[0]")

    Returns:
        A list of vertex indices in face-winding order
    """
    # Use polyInfo to get vertices in winding order
    face_info = cmds.polyInfo(face_name, faceToVertex=True)

    # Parse the output: "FACE     0:    4    5    7    6 \n"
    # The format is "FACE <index>: <vertex_indices>"
    info_str = face_info[0].strip()

    # Split by colon and get the vertex part
    vertex_part = info_str.split(':')[1].strip()

    # Extract vertex indices
    vertex_indices = [int(idx) for idx in vertex_part.split()]

    return vertex_indices


def get_vertex_positions(mesh_shape: str, vertex_indices: list[int]) -> list[Point3]:
    """
    Get the world space positions of vertices.

    Args:
        mesh_shape: The mesh shape node name
        vertex_indices: List of vertex indices

    Returns:
        A list of Point3 objects representing vertex positions
    """
    positions = []
    for index in vertex_indices:
        vertex_name = f"{mesh_shape}.vtx[{index}]"
        pos = cmds.xform(vertex_name, query=True, worldSpace=True, translation=True)
        positions.append(Point3(*pos))
    return positions


def check_vertices_coplanar(vertices: list[Point3], tolerance: float = 0.0001) -> tuple[bool, str]:
    """
    Check if four vertices are co-planar.

    Args:
        vertices: List of 4 Point3 objects
        tolerance: Maximum distance from plane to be considered co-planar

    Returns:
        A tuple of (is_coplanar, message)
    """
    if len(vertices) != 4:
        return False, f"Expected 4 vertices, got {len(vertices)}"

    # Use first three vertices to define a plane
    v0, v1, v2, v3 = vertices

    # Create two edge vectors from the first three vertices
    edge1 = Point3Pair(v0, v1).delta
    edge2 = Point3Pair(v0, v2).delta

    # Calculate the plane normal using cross product
    normal = Point3Pair(edge1, edge2).cross_product
    normal_mag = normal.magnitude

    if normal_mag < 1e-10:
        return False, "First three vertices are collinear, cannot define a plane"

    normal = normal.normalized

    # Calculate distance from fourth vertex to the plane
    # Distance = |dot(normal, (v3 - v0))|
    v3_to_plane = Point3Pair(v0, v3).delta
    distance = abs(Point3Pair(normal, v3_to_plane).dot_product)

    if distance > tolerance:
        return False, f"Fourth vertex is {distance:.6f} units from plane (tolerance: {tolerance})"

    return True, "All vertices are co-planar"


def check_all_right_angles(vertices: list[Point3], angle_tolerance: float = 1.0) -> tuple[bool, str]:
    """
    Check if all four corner angles are right angles (90 degrees).

    Args:
        vertices: List of 4 Point3 objects in order around the face
        angle_tolerance: Tolerance in degrees

    Returns:
        A tuple of (are_right_angles, message)
    """
    if len(vertices) != 4:
        return False, f"Expected 4 vertices, got {len(vertices)}"

    angles = []

    # Check each corner angle
    for i in range(4):
        # Get the three vertices that form this corner
        prev_vertex = vertices[(i - 1) % 4]
        current_vertex = vertices[i]
        next_vertex = vertices[(i + 1) % 4]

        # Create edge vectors
        edge1 = Point3Pair(current_vertex, prev_vertex).delta
        edge2 = Point3Pair(current_vertex, next_vertex).delta

        # Normalize the edge vectors
        edge1_norm = edge1.normalized
        edge2_norm = edge2.normalized

        # Calculate the angle using dot product
        # cos(angle) = dot(edge1, edge2) / (|edge1| * |edge2|)
        # Since vectors are normalized, we can just use the dot product
        dot = Point3Pair(edge1_norm, edge2_norm).dot_product

        # Clamp to avoid numerical errors with acos
        dot = max(-1.0, min(1.0, dot))

        angle_rad = math.acos(dot)
        angle_deg = math.degrees(angle_rad)
        angles.append(angle_deg)

        # Check if this angle is a right angle
        if abs(angle_deg - 90.0) > angle_tolerance:
            return False, f"Corner {i} has angle {angle_deg:.2f}°, expected 90° ± {angle_tolerance}°"

    return True, f"All corners have right angles: {[f'{a:.2f}°' for a in angles]}"


if __name__ == "__main__":
    # Example usage
    test_transform = "pCube1"
    test_face_index = 0

    # Test with all validations enabled
    is_valid, message = validate_quadrilateral(
        test_transform,
        test_face_index,
        check_coplanar=True,
        check_right_angles=True,
        angle_tolerance=1.0,
        coplanar_tolerance=0.0001
    )
    print(f"Valid: {is_valid}")
    print(f"Message: {message}")

    # Test with only basic validation
    is_valid, message = validate_quadrilateral(
        test_transform,
        test_face_index,
        check_coplanar=False,
        check_right_angles=False
    )
    print(f"\nBasic validation only:")
    print(f"Valid: {is_valid}")
    print(f"Message: {message}")
