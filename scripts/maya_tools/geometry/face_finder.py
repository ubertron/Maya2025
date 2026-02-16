"""This utility looks for cuboid geometry by searching a mesh for a matching face."""
from __future__ import annotations

from maya import cmds
from pathlib import Path

from core.point_classes import Point3, Point3Pair
from core.core_enums import SurfaceDirection
from core.math_utils import get_midpoint_from_point_list
from maya_tools import node_utils
from maya_tools.geometry.component_utils import FaceComponent, FacePair
from maya_tools.geometry import geometry_utils
from tests.validators import quadrilateral_validator
from tests.validators import cuboid_validator


class FaceFinder:

    def __init__(self, mode: SurfaceDirection = SurfaceDirection.concave, select: bool = False,
                 component: FaceComponent | None = None):
        """
        Initialize FaceFinder.

        Args:
            mode: SurfaceDirection enum. Default is SurfaceDirection.concave.
                  - SurfaceDirection.concave: finds face in the direction of the normal
                  - SurfaceDirection.convex: finds face in the opposite direction of the normal
            select: If True, selects the found faces. If False, restores the original selection.
            component: Optional FaceComponent specifying the face to use. If None, uses the current selection.
        """
        self.opposite_face = None
        self.valid_candidate_count = 0
        self.mode = mode
        self.select = select

        if not isinstance(mode, SurfaceDirection):
            cmds.warning(f"Invalid mode '{mode}'. Using SurfaceDirection.concave.")
            self.mode = SurfaceDirection.concave

        # Store original selection state to restore later
        state = node_utils.State()

        # Use provided component or fall back to selection
        if component is not None:
            if cmds.objExists(component.transform):
                self.transform = component.transform
                self.idx = component.idx
            else:
                cmds.warning(f"Transform '{component.transform}' does not exist.")
                state.restore()
                return
        else:
            selection = cmds.ls(sl=True, flatten=True, long=True)
            face_selection = [s for s in selection if ".f[" in s]
            if len(face_selection) == 1:
                self.transform = face_selection[0].split(".f")[0]
                self.idx = int(face_selection[0].split("[")[1].split("]")[0])
            elif len(face_selection) > 1:
                raise ValueError("More than one face found.")
            else:
                raise ValueError("No valid face is selected.")

        is_valid, message = quadrilateral_validator.validate_quadrilateral(self.transform, self.idx)
        if is_valid:
            result = self._process()
            print(f"Mode: {self.mode.name}")
            print(f"Found opposite face: {result}")
            if result:
                print(f"Opposite face index: {self.opposite_face}")
                if self.select:
                    # Select both faces and highlight the transform
                    face1 = f"{self.transform}.f[{self.idx}]"
                    face2 = f"{self.transform}.f[{self.opposite_face}]"
                    cmds.select([face1, face2], replace=True)
                    cmds.hilite(self.transform)
                else:
                    state.restore()
            else:
                print("No matching face found.")
                state.restore()
        else:
            cmds.warning(f"Not quad face: {message}")
            state.restore()

    def _process(self) -> bool:
        """
        Look for the opposite face that forms a cuboid with the selected face.

        Returns:
            True if a complementary face is found, False otherwise
        """
        # Get the mesh shape
        mesh_shape = quadrilateral_validator.get_mesh_shape(self.transform)
        if not mesh_shape:
            return False

        # Get source face data
        source_vertices = cuboid_validator.get_face_vertex_positions(mesh_shape, self.idx)
        source_center = cuboid_validator.get_face_center(source_vertices)
        source_normal = cuboid_validator.get_face_normal(source_vertices)

        # Get total face count
        face_count = cmds.polyEvaluate(mesh_shape, face=True)

        # Tolerance for position filtering (dot product should be ±1)
        position_tolerance = 0.1

        # Track all valid candidates and their distances
        valid_candidates = []

        # Search for complementary face
        for candidate_idx in range(face_count):
            # Skip the original face
            if candidate_idx == self.idx:
                continue

            # Get candidate face center
            candidate_vertices = cuboid_validator.get_face_vertex_positions(mesh_shape, candidate_idx)
            candidate_center = cuboid_validator.get_face_center(candidate_vertices)

            # Calculate center vector (from source to candidate)
            center_vector = Point3Pair(source_center, candidate_center).delta
            center_vector_norm = center_vector.normalized
            distance = center_vector.magnitude

            # Calculate dot product of source normal and center vector
            dot_product = Point3Pair(source_normal, center_vector_norm).dot_product

            print(f"\nChecking candidate face {candidate_idx}:")
            print(f"  Source center: {source_center}")
            print(f"  Source normal: {source_normal}")
            print(f"  Candidate center: {candidate_center}")
            print(f"  Center vector: {center_vector_norm}")
            print(f"  Distance: {distance:.4f}")
            print(f"  Dot product: {dot_product:.4f}")

            # Filter by search direction based on mode
            if self.mode == SurfaceDirection.concave:
                # Concave: search IN direction of normal (dot should be ≈ 1)
                if abs(dot_product - 1.0) > position_tolerance:
                    print(f"  SKIP: Not in concave search direction (need dot ≈ 1, got {dot_product:.4f})")
                    continue  # Skip this candidate
            else:  # SurfaceDirection.convex
                # Convex: search OPPOSITE to normal (dot should be ≈ -1)
                if abs(dot_product + 1.0) > position_tolerance:
                    print(f"  SKIP: Not in convex search direction (need dot ≈ -1, got {dot_product:.4f})")
                    continue  # Skip this candidate

            print(f"  PASS: Position check passed, validating cuboid...")
            print(f"  Validating with mode: {self.mode} (type: {type(self.mode).__name__})")

            # Candidate is in the correct search direction, now validate cuboid
            is_valid, message = cuboid_validator.validate_cuboid_faces(
                self.transform,
                self.idx,
                candidate_idx,
                mode=self.mode
            )

            if is_valid:
                # Found a valid complementary face, add to candidates
                valid_candidates.append((candidate_idx, distance, message))
                print(f"  VALID: {message}")
            else:
                print(f"  FAIL: {message}")

        # If we found valid candidates, select the closest one
        self.valid_candidate_count = len(valid_candidates)
        if valid_candidates:
            # Sort by distance and pick the closest
            valid_candidates.sort(key=lambda x: x[1])
            self.opposite_face, closest_distance, validation_msg = valid_candidates[0]

            print(f"\n{'=' * 80}")
            print(f"Found {len(valid_candidates)} valid candidate(s)")
            print(f"Selected closest face: {self.opposite_face} at distance {closest_distance:.4f}")
            print(f"Cuboid validation: {validation_msg}")
            print(f"{'=' * 80}")
            return True

        return False


def get_opposite_face(component: FaceComponent | None = None,
                      surface_direction: SurfaceDirection = SurfaceDirection.convex,
                      select: bool = False) -> FaceComponent | None:
    """
    Get the opposite face to a supplied face.

    Args:
        component: Optional FaceComponent specifying the face to use. If None, uses the current selection.
        surface_direction: SurfaceDirection enum for search direction.
        select: If True, selects the found faces. If False, restores the original selection.

    Returns:
        FaceComponent of the opposite face if found, None otherwise.

    Raises:
        ValueError: If select=True, component=None, and selection is invalid
                    (no face selected or multiple faces selected).
    """
    finder = FaceFinder(mode=surface_direction, select=select, component=component)
    if finder.opposite_face is not None:
        return FaceComponent(transform=finder.transform, idx=finder.opposite_face)
    return None


def get_opposite_face_group(
    components: list[FaceComponent] | None = None,
    surface_direction: SurfaceDirection = SurfaceDirection.convex,
    select: bool = False
) -> list[FacePair]:
    """
    Find opposite faces for multiple input faces.

    Handles three cases:
    1. Disconnected faces: Process each independently
    2. Connected faces forming valid rectangle: Treat as unified block
    3. Connected faces NOT forming rectangle: Fall back to individual processing

    Args:
        components: List of FaceComponents. If None, uses current selection.
        surface_direction: Search direction (concave/convex).
        select: If True, selects all found face pairs.

    Returns:
        List of FacePair objects for successful matches.
        Faces with no match are silently skipped.
    """
    from maya_tools.geometry.component_utils import components_from_selection

    # Get components from selection if not provided
    if components is None:
        all_components = components_from_selection()
        components = [c for c in all_components if isinstance(c, FaceComponent)]

    if not components:
        return []

    # Ensure all faces are on same transform
    transforms = set(c.transform for c in components)
    if len(transforms) > 1:
        cmds.warning("All faces must be on the same mesh")
        return []

    transform = components[0].transform
    face_indices = [c.idx for c in components]

    results: list[FacePair] = []

    # Check connectivity of all faces
    shells = geometry_utils.group_geometry_shells(transform=transform, faces=face_indices)
    print(f"[get_opposite_face_group] Faces: {face_indices}")
    print(f"[get_opposite_face_group] Shells: {shells}")

    for shell in shells:
        shell_components = [c for c in components if c.idx in shell]

        print(f"[get_opposite_face_group] Processing shell: {shell} (len={len(shell_components)})")
        if len(shell_components) == 1:
            # Single face in shell - use existing logic
            print(f"[get_opposite_face_group] Single face, using _process_single_face()")
            result = _process_single_face(shell_components[0], surface_direction)
            if result:
                results.append(result)
        else:
            # Multiple connected faces in shell
            is_valid_rect, msg = geometry_utils.validate_rectangular_face_block(transform, shell)
            print(f"[get_opposite_face_group] validate_rectangular_face_block: {is_valid_rect}, msg: {msg}")
            if is_valid_rect:
                # Connected rectangle block - process as group
                block_results = _process_rectangle_block(shell_components, surface_direction)
                results.extend(block_results)
            else:
                # Not a valid rectangle - process individually
                individual_results = _process_individual_faces(shell_components, surface_direction)
                results.extend(individual_results)

    # Handle selection
    if select and results:
        all_faces = []
        for pair in results:
            all_faces.extend(pair.names)
        cmds.select(all_faces, replace=True)
        cmds.hilite(transform)

    return results


def _process_single_face(
    component: FaceComponent,
    surface_direction: SurfaceDirection
) -> FacePair | None:
    """Process a single face using existing FaceFinder logic."""
    opposite = get_opposite_face(
        component=component,
        surface_direction=surface_direction,
        select=False
    )
    if opposite:
        return FacePair(source=component, opposite=opposite)
    return None


def _process_individual_faces(
    components: list[FaceComponent],
    surface_direction: SurfaceDirection
) -> list[FacePair]:
    """Process faces individually, returning all successful matches."""
    results = []
    for component in components:
        result = _process_single_face(component, surface_direction)
        if result:
            results.append(result)
    return results


def _process_rectangle_block(
    components: list[FaceComponent],
    surface_direction: SurfaceDirection
) -> list[FacePair]:
    """
    Process a connected rectangular block of faces.

    For a valid rectangle block, finds the matching opposite faces
    that together form the opposite side of the cuboid region.
    """
    if not components:
        return []

    transform = components[0].transform
    source_indices = [c.idx for c in components]
    print(f"[_process_rectangle_block] source_indices: {source_indices}")

    # Get source block data
    source_vertices = geometry_utils.get_vertices_from_faces(node=transform, faces=source_indices)
    source_positions = [geometry_utils.get_vertex_position(node=transform, vertex_id=v) for v in source_vertices]
    source_center = get_midpoint_from_point_list(source_positions)
    print(f"[_process_rectangle_block] source_center: {source_center}")

    # Calculate average normal for the block
    source_normal = _calculate_block_normal(transform, source_indices)
    print(f"[_process_rectangle_block] source_normal: {source_normal}")

    # Find candidate opposite face group
    opposite_indices = _find_opposite_face_block(
        transform=transform,
        source_indices=source_indices,
        source_center=source_center,
        source_normal=source_normal,
        surface_direction=surface_direction
    )
    print(f"[_process_rectangle_block] opposite_indices: {opposite_indices}")

    if not opposite_indices or len(opposite_indices) != len(source_indices):
        # Fallback to individual processing
        print(f"[_process_rectangle_block] FALLBACK: opposite count {len(opposite_indices) if opposite_indices else 0} != source count {len(source_indices)}")
        return _process_individual_faces(components, surface_direction)

    # Match source faces to opposite faces
    return _match_face_pairs(transform, source_indices, opposite_indices)


def _calculate_block_normal(transform: str, face_indices: list[int]) -> Point3:
    """Calculate the average normal for a group of faces."""
    normals = []
    for idx in face_indices:
        mesh_shape = quadrilateral_validator.get_mesh_shape(transform)
        if mesh_shape:
            vertices = cuboid_validator.get_face_vertex_positions(mesh_shape, idx)
            normal = cuboid_validator.get_face_normal(vertices)
            normals.append(normal)

    if not normals:
        return Point3(0, 1, 0)  # Default up

    avg_x = sum(n.x for n in normals) / len(normals)
    avg_y = sum(n.y for n in normals) / len(normals)
    avg_z = sum(n.z for n in normals) / len(normals)

    return Point3(avg_x, avg_y, avg_z).normalized


def _find_opposite_face_block(
    transform: str,
    source_indices: list[int],
    source_center: Point3,
    source_normal: Point3,
    surface_direction: SurfaceDirection
) -> list[int]:
    """
    Find the group of faces that form the opposite side of a cuboid region.

    Returns list of face indices forming the opposite block, or empty list if none found.
    """
    mesh_shape = quadrilateral_validator.get_mesh_shape(transform)
    if not mesh_shape:
        return []

    face_count = cmds.polyEvaluate(mesh_shape, face=True)
    # More lenient tolerance for block search - individual opposite faces
    # may be at different positions relative to block center
    position_tolerance = 0.25

    # Search for faces in the correct direction with opposing normals
    candidates = []

    for candidate_idx in range(face_count):
        if candidate_idx in source_indices:
            continue

        # Get candidate data
        candidate_vertices = cuboid_validator.get_face_vertex_positions(mesh_shape, candidate_idx)
        candidate_center = cuboid_validator.get_face_center(candidate_vertices)
        candidate_normal = cuboid_validator.get_face_normal(candidate_vertices)

        # Check direction alignment
        center_vector = Point3Pair(source_center, candidate_center).delta
        if center_vector.magnitude < 1e-10:
            continue
        center_vector_norm = center_vector.normalized
        distance = center_vector.magnitude

        dot_product = Point3Pair(source_normal, center_vector_norm).dot_product

        # Filter by search direction
        if surface_direction == SurfaceDirection.concave:
            if abs(dot_product - 1.0) > position_tolerance:
                continue
        else:
            if abs(dot_product + 1.0) > position_tolerance:
                continue

        # Check opposing normal
        normal_dot = Point3Pair(source_normal, candidate_normal).dot_product
        if normal_dot > -0.9:  # Normals should be roughly opposite
            continue

        candidates.append((candidate_idx, distance))

    print(f"[_find_opposite_face_block] Total candidates found: {len(candidates)}")
    if not candidates:
        return []

    # Group candidates by distance (faces at same distance are likely the opposite block)
    candidates.sort(key=lambda x: x[1])
    target_distance = candidates[0][1]
    # Use percentage-based tolerance (10% of distance) with minimum of 5 units
    distance_tolerance = max(5.0, target_distance * 0.1)
    print(f"[_find_opposite_face_block] target_distance: {target_distance}, tolerance: {distance_tolerance}")

    opposite_candidates = [
        idx for idx, dist in candidates
        if abs(dist - target_distance) < distance_tolerance
    ]
    print(f"[_find_opposite_face_block] opposite_candidates at target distance: {opposite_candidates}")

    # Verify these form a connected group matching source topology
    if len(opposite_candidates) == len(source_indices):
        shells = geometry_utils.group_geometry_shells(transform, opposite_candidates)
        print(f"[_find_opposite_face_block] shells: {shells}")
        if len(shells) == 1:  # All connected
            return opposite_candidates

    # If count doesn't match, try to find best matching subset
    print(f"[_find_opposite_face_block] Count mismatch or not connected, returning subset")
    return opposite_candidates[:len(source_indices)] if len(opposite_candidates) >= len(source_indices) else []


def _match_face_pairs(
    transform: str,
    source_indices: list[int],
    opposite_indices: list[int]
) -> list[FacePair]:
    """
    Match source faces to their corresponding opposite faces by position.

    Uses face center proximity after projecting along normal direction.
    """
    results = []
    used_opposites = set()

    for source_idx in source_indices:
        source_center = geometry_utils.get_face_position(transform=transform, face_id=source_idx)
        best_match = None
        best_distance = float('inf')

        for opp_idx in opposite_indices:
            if opp_idx in used_opposites:
                continue

            opp_center = geometry_utils.get_face_position(transform=transform, face_id=opp_idx)

            # Use XZ distance (projecting out depth) for matching
            # This works for typical wall/floor scenarios
            import math
            xz_dist = math.sqrt(
                (source_center.x - opp_center.x) ** 2 +
                (source_center.z - opp_center.z) ** 2
            )

            if xz_dist < best_distance:
                best_distance = xz_dist
                best_match = opp_idx

        if best_match is not None:
            used_opposites.add(best_match)
            results.append(FacePair(
                source=FaceComponent(transform=transform, idx=source_idx),
                opposite=FaceComponent(transform=transform, idx=best_match)
            ))

    return results


if __name__ == "__main__":
    # Example usage - concave mode (default)
    # cmds.select("floor.f[4]")
    # cmds.hilite("floor")
    # finder = FaceFinder()  # Uses SurfaceDirection.concave by default

    # Example usage - convex mode
    # cmds.select("polySurface1.f[1]")
    # cmds.hilite("polySurface1")
    test_scene = Path("bounds_finder_test_scene.ma")
    _finder = FaceFinder(mode=SurfaceDirection.convex)
