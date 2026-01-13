"""This utility looks for cuboid geometry by searching a mesh for a matching face."""

from importlib import reload

from maya import cmds
from pathlib import Path

from core.point_classes import Point3Pair
from core.core_enums import SurfaceDirection
from maya_tools import node_utils
from tests.validators import quadrilateral_validator
from tests.validators import cuboid_validator


class BoundsFinder:

    def __init__(self, mode: SurfaceDirection = SurfaceDirection.concave):
        """
        Initialize BoundsFinder.

        Args:
            mode: SurfaceDirection enum. Default is SurfaceDirection.concave.
                  - SurfaceDirection.concave: finds face in the direction of the normal
                  - SurfaceDirection.convex: finds face in the opposite direction of the normal
        """
        self.opposite_face = None
        self.mode = mode

        if not isinstance(mode, SurfaceDirection):
            cmds.warning(f"Invalid mode '{mode}'. Using SurfaceDirection.concave.")
            self.mode = SurfaceDirection.concave

        # Store original selection to restore later
        original_selection = cmds.ls(sl=True, flatten=True, long=True)

        selection = cmds.ls(sl=True, flatten=True, long=True)
        if len(selection) == 1 and ".f[" in selection[0]:
            self.transform = selection[0].split(".f")[0]
            self.idx = int(selection[0].split("[")[1].split("]")[0])

            is_valid, message = quadrilateral_validator.validate_quadrilateral(self.transform, self.idx)
            if is_valid:
                result = self._process()
                print(f"Mode: {self.mode.name}")
                print(f"Found opposite face: {result}")
                if result:
                    print(f"Opposite face index: {self.opposite_face}")
                    # Select both faces and highlight the transform
                    mesh_shape = quadrilateral_validator.get_mesh_shape(self.transform)
                    face1 = f"{mesh_shape}.f[{self.idx}]"
                    face2 = f"{mesh_shape}.f[{self.opposite_face}]"
                    cmds.select([face1, face2], replace=True)
                    cmds.hilite(self.transform)
                else:
                    print("No matching face found.")
                    # Restore original selection if no match found
                    if original_selection:
                        cmds.select(original_selection, replace=True)
                    else:
                        cmds.select(clear=True)
            else:
                cmds.warning(f"Not quad face: {message}")
                # Restore original selection on validation failure
                if original_selection:
                    cmds.select(original_selection, replace=True)
                else:
                    cmds.select(clear=True)
        else:
            cmds.warning("Select a single quad face.")
            # Restore original selection on invalid selection
            if original_selection:
                cmds.select(original_selection, replace=True)
            else:
                cmds.select(clear=True)
        
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
        if valid_candidates:
            # Sort by distance and pick the closest
            valid_candidates.sort(key=lambda x: x[1])
            self.opposite_face, closest_distance, validation_msg = valid_candidates[0]

            print(f"\n{'='*80}")
            print(f"Found {len(valid_candidates)} valid candidate(s)")
            print(f"Selected closest face: {self.opposite_face} at distance {closest_distance:.4f}")
            print(f"Cuboid validation: {validation_msg}")
            print(f"{'='*80}")
            return True

        return False

        


if __name__ == "__main__":
    # Example usage - concave mode (default)
    #cmds.select("floor.f[4]")
    #cmds.hilite("floor")
    #finder = BoundsFinder()  # Uses SurfaceDirection.concave by default

    # Example usage - convex mode
    #cmds.select("polySurface1.f[1]")
    #cmds.hilite("polySurface1")
    test_scene = Path("bounds_finder_test_scene.ma")
    finder = BoundsFinder(mode=SurfaceDirection.convex)


    