"""
Boxy Geometry Validator

Validates that a polygon object is a proper cuboid (box shape).

Place this file at:
tests/validators/validator_boxy.py

Usage:
    from tests.validators.validator_boxy import validator_boxy
    
    result, issues = validator_boxy(node="pCube1")
    if result:
        print("Valid boxy object")
    else:
        print("Invalid boxy object")
        print("\\n".join(issues))
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om


def validator_boxy(node):
    """
    Validate that a polygon object is a proper cuboid.

    Requirements:
    1. Must be a polygon mesh
    2. Must have a "custom_type" attribute set to "boxy"
    3. Must have a "pivot" attribute that returns a string value
    4. Must have a "size" attribute that returns three float values
    5. Must have exactly 6 faces
    6. All vertices must be welded (no overlapping vertices)
    7. Must be cuboid-shaped (rectangular box)
    8. Opposite faces must be coplanar (dot product of normals = -1)
    9. All face corners must be right angles (90 degrees)
    10. Face normals must align with object's pivot axes

    Args:
        node (str): Name of the polygon object to validate

    Returns:
        tuple: (bool, list)
            - bool: True if all validations pass, False otherwise
            - list: List of validation error messages (empty if passed)

    Example:
        result, issues = validator_boxy(node="pCube1")
        if not result:
            for issue in issues:
                print(f"  - {issue}")
    """
    issues = []

    # Check if node exists
    if not cmds.objExists(node):
        return False, [f"Node '{node}' does not exist"]

    # Test 1: Check for "custom_type" attribute (must be "boxy")
    if not cmds.attributeQuery('custom_type', node=node, exists=True):
        issues.append(f"Node '{node}' does not have required 'custom_type' attribute")
        return False, issues  # Early return - not a valid boxy type
    else:
        try:
            custom_type_value = cmds.getAttr(f'{node}.custom_type')
            if custom_type_value != "boxy":
                issues.append(f"Attribute 'custom_type' must be set to 'boxy', found '{custom_type_value}'")
                return False, issues  # Early return - not a valid boxy type
        except Exception as e:
            issues.append(f"Failed to read 'custom_type' attribute: {str(e)}")
            return False, issues  # Early return - error checking boxy type

    # Test 2: Check for "pivot" attribute (must be string)
    if not cmds.attributeQuery('pivot', node=node, exists=True):
        issues.append(f"Node '{node}' does not have required 'pivot' attribute")
    else:
        try:
            pivot_value = cmds.getAttr(f'{node}.pivot')
            if not isinstance(pivot_value, str):
                issues.append(f"Attribute 'pivot' must be a string, found {type(pivot_value).__name__}")
        except Exception as e:
            issues.append(f"Failed to read 'pivot' attribute: {str(e)}")

    # Test 3: Check for "size" attribute (must be list containing one tuple of three floats)
    if not cmds.attributeQuery('size', node=node, exists=True):
        issues.append(f"Node '{node}' does not have required 'size' attribute")
    else:
        try:
            size_value = cmds.getAttr(f'{node}.size')
            if type(size_value) != list:
                issues.append(f"Attribute 'size' must return a list, found {type(size_value).__name__}")
            elif len(size_value) != 1:
                issues.append(f"Attribute 'size' must return a list with exactly 1 element, found {len(size_value)}")
            elif type(size_value[0]) != tuple:
                issues.append(f"Attribute 'size' must contain a tuple, found {type(size_value[0]).__name__}")
            elif len(size_value[0]) != 3:
                issues.append(f"Attribute 'size' tuple must contain exactly 3 values, found {len(size_value[0])}")
            elif next((True for x in size_value[0] if type(x) != float), False):
                issues.append(f"Attribute 'size' tuple must contain only float values")
        except Exception as e:
            issues.append(f"Failed to read 'size' attribute: {str(e)}")

    # Get shape node
    shapes = cmds.listRelatives(node, shapes=True, type='mesh')
    if not shapes:
        return False, [f"Node '{node}' is not a polygon mesh"]

    shape = shapes[0]

    try:
        # Get MFnMesh for the shape
        sel_list = om.MSelectionList()
        sel_list.add(shape)
        dag_path = sel_list.getDagPath(0)
        mesh_fn = om.MFnMesh(dag_path)

        # Test 1: Must have exactly 6 faces
        num_faces = mesh_fn.numPolygons
        if num_faces != 6:
            issues.append(f"Must have exactly 6 faces, found {num_faces}")

        # Test 2: Check for welded vertices (no overlapping)
        if not _check_vertices_welded(mesh_fn):
            issues.append("Vertices are not welded (overlapping vertices detected)")

        # Test 3: Check face count is exactly 6 (continue with detailed checks)
        if num_faces == 6:
            # Get face normals in OBJECT SPACE (not world space)
            # This ensures we're comparing to the object's local axes, not world axes
            face_data = []
            for face_id in range(num_faces):
                # Get normal in object space - relative to object's pivot/local axes
                normal = mesh_fn.getPolygonNormal(face_id, om.MSpace.kObject)

                # Calculate center from vertices
                vertices = mesh_fn.getPolygonVertices(face_id)
                points = mesh_fn.getPoints(om.MSpace.kObject)
                center = om.MPoint(0, 0, 0)
                for v_id in vertices:
                    center += om.MVector(points[v_id])
                center = center / len(vertices)

                face_data.append({
                    'id': face_id,
                    'normal': normal,
                    'center': center,
                    'vertices': vertices
                })

            # Test 4: Opposite faces must be coplanar (normals dot product = -1)
            opposite_pairs = _find_opposite_faces(face_data)
            if len(opposite_pairs) != 3:
                issues.append(f"Could not identify 3 pairs of opposite faces, found {len(opposite_pairs)}")
            else:
                for face1, face2 in opposite_pairs:
                    n1 = face1['normal']
                    n2 = face2['normal']
                    dot = n1 * n2  # Dot product

                    # Should be -1 for opposite faces (tolerance for floating point)
                    if not _is_close(dot, -1.0, tolerance=0.01):
                        issues.append(
                            f"Faces {face1['id']} and {face2['id']} are not properly opposite "
                            f"(normal dot product = {dot:.4f}, expected -1.0)"
                        )

            # Test 5: All corners must be right angles (90 degrees)
            for face in face_data:
                if not _check_face_right_angles(mesh_fn, face['id']):
                    issues.append(f"Face {face['id']} does not have all right-angle corners")

            # Test 6: Normals must align with object's pivot axes
            # Get object's rotation
            rotation = cmds.xform(node, query=True, rotation=True, objectSpace=True)

            # Check if normals align with world axes when object is at zero rotation
            if not _check_normals_axis_aligned(face_data, node):
                issues.append(
                    "Face normals do not align with object's pivot axes. "
                    "When object rotation is (0,0,0), faces should be axis-aligned"
                )

        # Return results
        passed = len(issues) == 0
        return passed, issues

    except Exception as e:
        return False, [f"Validation error: {str(e)}"]


def _check_vertices_welded(mesh_fn):
    """
    Check if all vertices are welded (no overlapping vertices).

    Args:
        mesh_fn (MFnMesh): Maya mesh function set

    Returns:
        bool: True if all vertices are welded
    """
    num_vertices = mesh_fn.numVertices
    positions = mesh_fn.getPoints(om.MSpace.kObject)

    tolerance = 0.0001

    # Check for duplicate positions
    for i in range(num_vertices):
        for j in range(i + 1, num_vertices):
            if positions[i].isEquivalent(positions[j], tolerance):
                return False

    return True


def _find_opposite_faces(face_data):
    """
    Find pairs of opposite faces based on normal directions.

    Args:
        face_data (list): List of face data dictionaries

    Returns:
        list: List of tuples of opposite face pairs
    """
    opposite_pairs = []
    used_faces = set()

    for i, face1 in enumerate(face_data):
        if i in used_faces:
            continue

        for j, face2 in enumerate(face_data):
            if j <= i or j in used_faces:
                continue

            # Check if normals are opposite (dot product ~ -1)
            dot = face1['normal'] * face2['normal']
            if _is_close(dot, -1.0, tolerance=0.01):
                opposite_pairs.append((face1, face2))
                used_faces.add(i)
                used_faces.add(j)
                break

    return opposite_pairs


def _check_face_right_angles(mesh_fn, face_id):
    """
    Check if all corners of a face are right angles (90 degrees).

    Args:
        mesh_fn (MFnMesh): Maya mesh function set
        face_id (int): Face ID to check

    Returns:
        bool: True if all corners are right angles
    """
    vertices = mesh_fn.getPolygonVertices(face_id)
    num_verts = len(vertices)

    if num_verts != 4:
        # Not a quad, can't be a proper box face
        return False

    points = mesh_fn.getPoints(om.MSpace.kObject)
    tolerance = 0.1  # ~5.7 degrees tolerance

    for i in range(num_verts):
        # Get three consecutive vertices
        v_prev = vertices[(i - 1) % num_verts]
        v_curr = vertices[i]
        v_next = vertices[(i + 1) % num_verts]

        # Get positions
        p_prev = points[v_prev]
        p_curr = points[v_curr]
        p_next = points[v_next]

        # Create edge vectors
        edge1 = p_prev - p_curr
        edge2 = p_next - p_curr

        edge1.normalize()
        edge2.normalize()

        # Calculate angle (dot product of normalized vectors)
        dot = edge1 * edge2

        # For right angle, dot product should be 0
        if not _is_close(dot, 0.0, tolerance=tolerance):
            return False

    return True


def _check_normals_axis_aligned(face_data, node):
    """
    Check if face normals align with object's LOCAL pivot axes.

    The normals in face_data are already in object space (kObject),
    which means they're relative to the object's local transform/pivot.
    This allows the test to work regardless of how the object is rotated
    in world space.

    For a proper box aligned with its pivot:
    - One face should have normal = +X in object space (dot product = 1)
    - One face should have normal = -X in object space (dot product = 1)
    - One face should have normal = +Y in object space (dot product = 1)
    - One face should have normal = -Y in object space (dot product = 1)
    - One face should have normal = +Z in object space (dot product = 1)
    - One face should have normal = -Z in object space (dot product = 1)

    Args:
        face_data (list): List of face data dictionaries (normals in object space)
        node (str): Name of the object (not used, kept for compatibility)

    Returns:
        bool: True if normals are axis-aligned with object's local pivot
    """
    # Define the six required axis directions in object space
    required_directions = [
        om.MVector(1, 0, 0),   # +X local
        om.MVector(-1, 0, 0),  # -X local
        om.MVector(0, 1, 0),   # +Y local
        om.MVector(0, -1, 0),  # -Y local
        om.MVector(0, 0, 1),   # +Z local
        om.MVector(0, 0, -1),  # -Z local
    ]

    tolerance = 0.01
    matched_directions = []

    # Check each face normal (already in object space) against required directions
    for face in face_data:
        normal = face['normal']
        normal.normalize()

        # Find which local axis this face aligns with
        matched = False
        for i, axis in enumerate(required_directions):
            if i in matched_directions:
                continue  # This direction already matched

            dot = normal * axis
            if _is_close(dot, 1.0, tolerance=tolerance):
                matched_directions.append(i)
                matched = True
                break

        if not matched:
            # This face doesn't align with any unused axis direction
            return False

    # Check that we matched all 6 required directions
    if len(matched_directions) != 6:
        return False

    return True


def _is_close(a, b, tolerance=0.0001):
    """
    Check if two values are close within tolerance.

    Args:
        a (float): First value
        b (float): Second value
        tolerance (float): Tolerance for comparison

    Returns:
        bool: True if values are within tolerance
    """
    return abs(a - b) <= tolerance


# Convenience function for testing
def test_selected_boxy(node=None):
    """
    Test a boxy geometry object.

    Args:
        node (str, optional): Name of the object to test. If None, uses current selection.
                             Must be a single node name (string), not a list.

    Returns:
        tuple: (bool, list) - (passed, issues)

    For quick testing in Maya script editor.
    """
    # Validate input
    if node is not None:
        # Check that a string was passed, not a list or other type
        if not isinstance(node, str):
            print("❌ ERROR: node argument must be a single string, not a list or other type")
            print(f"   Received: {type(node).__name__}")
            return False, ["node argument must be a single string"]
    else:
        # Use selection if no node specified
        selected = cmds.ls(selection=True)

        if not selected:
            print("❌ Please select an object first or provide a node name!")
            return False, ["No object selected or specified"]

        if len(selected) > 1:
            print(f"❌ ERROR: Multiple objects selected ({len(selected)}). Please select only one object.")
            print(f"   Selected: {', '.join(selected)}")
            return False, [f"Multiple objects selected: {', '.join(selected)}. Only one allowed."]

        node = selected[0]

    print(f"\n{'='*60}")
    print(f"Validating Boxy Geometry: {node}")
    print('='*60)

    result, issues = validator_boxy(node)

    if result:
        print("✅ PASSED: Object is a valid boxy geometry!")
    else:
        print("❌ FAILED: Object is not a valid boxy geometry")
        print("\nIssues found:")
        for issue in issues:
            print(f"  • {issue}")

    print('='*60 + '\n')

    return result, issues


if __name__ == '__main__':
    # When run directly in Maya, test selected object
    test_selected_boxy()