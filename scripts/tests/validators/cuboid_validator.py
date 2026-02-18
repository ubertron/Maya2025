"""Validator for checking if two faces form a cuboid in Maya scenes."""

from __future__ import annotations

from maya import cmds
from core.point_classes import Point3, Point3Pair
from core.core_enums import SurfaceDirection
from tests.validators import quadrilateral_validator


def validate_cuboid_faces(transform: str, face1_idx: int, face2_idx: int,
                          mode: SurfaceDirection = SurfaceDirection.concave,
                          dimension_tolerance: float = 0.001,
                          normal_tolerance: float = 0.98,
                          parallelism_tolerance: float = 0.98) -> tuple[bool, str]:
    """
    Validate that two faces form a valid cuboid (rectangular prism).

    Args:
        transform: The transform node name
        face1_idx: Index of the first face
        face2_idx: Index of the second face
        mode: SurfaceDirection enum - determines normal direction check
        dimension_tolerance: Tolerance for matching face dimensions
        normal_tolerance: Tolerance for normal alignment (dot product close to 1 or -1)
        parallelism_tolerance: Tolerance for parallel alignment

    Returns:
        A tuple of (is_valid, message) where is_valid is True if the faces form a cuboid,
        and message contains details about the validation result
    """
    # Validate both faces are quadrilaterals with right angles
    is_valid1, msg1 = quadrilateral_validator.validate_quadrilateral(
        transform, face1_idx, check_coplanar=True, check_right_angles=True
    )
    if not is_valid1:
        return False, f"Face {face1_idx} is not a valid rectangle: {msg1}"

    is_valid2, msg2 = quadrilateral_validator.validate_quadrilateral(
        transform, face2_idx, check_coplanar=True, check_right_angles=True
    )
    if not is_valid2:
        return False, f"Face {face2_idx} is not a valid rectangle: {msg2}"

    # Get mesh shape
    mesh_shape = quadrilateral_validator.get_mesh_shape(transform)
    if not mesh_shape:
        return False, f"Object '{transform}' does not have a valid mesh node"

    # Get face data
    vertices1 = get_face_vertex_positions(mesh_shape, face1_idx)
    vertices2 = get_face_vertex_positions(mesh_shape, face2_idx)

    normal1 = get_face_normal(vertices1)
    normal2 = get_face_normal(vertices2)

    center1 = get_face_center(vertices1)
    center2 = get_face_center(vertices2)

    dimensions1 = get_face_dimensions(vertices1)
    dimensions2 = get_face_dimensions(vertices2)

    # Check normal alignment based on mode
    # Calculate the vector from face1 center to face2 center
    center_vector = Point3Pair(center1, center2).delta
    center_vector_normalized = center_vector.normalized

    # Use .name comparison to avoid enum identity issues after module reload
    if mode.name == "concave":
        # In concave mode, we search IN direction of normal
        # normal1 should point towards center2: dot(normal1, center_vector) ≈ 1
        # normal2 should point towards center1: dot(normal2, center_vector) ≈ -1
        # (normals point toward each other - opposite directions)

        dot_normal1_to_center2 = Point3Pair(normal1, center_vector_normalized).dot_product
        dot_normal2_to_center1 = Point3Pair(normal2, center_vector_normalized).dot_product

        if dot_normal1_to_center2 <= 0:
            return False, f"Face {face1_idx} normal does not point towards face {face2_idx} (concave mode, dot: {dot_normal1_to_center2:.4f})"

        if dot_normal2_to_center1 >= 0:
            return False, f"Face {face2_idx} normal does not point towards face {face1_idx} (concave mode, dot: {dot_normal2_to_center1:.4f})"

    else:  # convex mode
        # In convex mode, we search OPPOSITE to normal direction
        # normal1 should point away from center2: dot(normal1, center_vector) ≈ -1
        # normal2 should point away from center1: dot(normal2, center_vector) ≈ 1
        # BUT normals should still be opposite to each other!
        # This means normal2 points back toward face1 (in direction of center_vector)

        dot_normal1_to_center2 = Point3Pair(normal1, center_vector_normalized).dot_product
        dot_normal2_to_center1 = Point3Pair(normal2, center_vector_normalized).dot_product

        if dot_normal1_to_center2 >= 0:
            return False, f"Face {face1_idx} normal does not point away from face {face2_idx} (convex mode, dot: {dot_normal1_to_center2:.4f})"

        if dot_normal2_to_center1 <= 0:
            return False, f"Face {face2_idx} normal does not point back toward face {face1_idx} (convex mode, dot: {dot_normal2_to_center1:.4f})"

    # Check if dimensions match
    if not dimensions_match(dimensions1, dimensions2, dimension_tolerance):
        return False, f"Face dimensions don't match: {dimensions1} vs {dimensions2}"

    # Verify normals are opposite (both modes require opposite normals)
    normal_dot = Point3Pair(normal1, normal2).dot_product

    # Normals should always be opposite (dot close to -1) for a valid cuboid
    if normal_dot > -normal_tolerance:
        return False, f"Face normals not opposite (dot product: {normal_dot:.4f}, expected < {-normal_tolerance})"

    # The vector between centers should be parallel to the face normals
    dot_with_normal1 = abs(Point3Pair(center_vector_normalized, normal1).dot_product)
    if dot_with_normal1 < parallelism_tolerance:
        return False, f"Faces are not properly aligned (parallelism: {dot_with_normal1:.4f}, expected > {parallelism_tolerance})"

    # Calculate the distance between face centers
    distance = center_vector.magnitude

    return True, f"Faces form a valid {mode.name} cuboid (dimensions: {dimensions1}, distance: {distance:.4f})"


def get_face_vertex_positions(mesh_shape: str, face_idx: int) -> list[Point3]:
    """Get the vertex positions for a face."""
    face_name = f"{mesh_shape}.f[{face_idx}]"
    vertex_indices = quadrilateral_validator.get_face_vertices(face_name)
    return quadrilateral_validator.get_vertex_positions(mesh_shape, vertex_indices)


def get_face_normal(vertices: list[Point3]) -> Point3:
    """Calculate the face normal from vertices."""
    # Use first three vertices to calculate normal
    edge1 = Point3Pair(vertices[0], vertices[1]).delta
    edge2 = Point3Pair(vertices[0], vertices[2]).delta
    normal = Point3Pair(edge1, edge2).cross_product
    return normal.normalized


def get_face_center(vertices: list[Point3]) -> Point3:
    """Calculate the center point of a face."""
    x = sum(v.x for v in vertices) / len(vertices)
    y = sum(v.y for v in vertices) / len(vertices)
    z = sum(v.z for v in vertices) / len(vertices)
    return Point3(x, y, z)


def get_face_dimensions(vertices: list[Point3]) -> tuple[float, float]:
    """
    Get the dimensions of a rectangular face.

    Returns:
        A tuple of (width, height) representing the face dimensions
    """
    # Calculate edge lengths
    edge1_length = Point3Pair(vertices[0], vertices[1]).delta.magnitude
    edge2_length = Point3Pair(vertices[1], vertices[2]).delta.magnitude

    # Sort to get consistent ordering
    return tuple(sorted([edge1_length, edge2_length]))


def dimensions_match(dim1: tuple[float, float], dim2: tuple[float, float],
                    tolerance: float = 0.001) -> bool:
    """Check if two dimension tuples match within tolerance."""
    return (abs(dim1[0] - dim2[0]) < tolerance and
            abs(dim1[1] - dim2[1]) < tolerance)


if __name__ == "__main__":
    # Example usage
    test_transform = "pCube1"
    test_face1 = 0
    test_face2 = 1

    # Test concave mode (default)
    is_valid, message = validate_cuboid_faces(test_transform, test_face1, test_face2, mode=SurfaceDirection.concave)
    print(f"Concave mode - Valid: {is_valid}")
    print(f"Message: {message}")

    # Test convex mode
    is_valid, message = validate_cuboid_faces(test_transform, test_face1, test_face2, mode=SurfaceDirection.convex)
    print(f"\nConvex mode - Valid: {is_valid}")
    print(f"Message: {message}")

