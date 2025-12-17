from __future__ import annotations

from tests.framework import NurbsCurveValidator


def validate_door_curve(curve_name):
    """
    Validate that a curve meets door curve requirements.

    Args:
        curve_name (str): Name of the curve to validate

    Returns:
        tuple: (bool, list) - (passed, issues)
               passed: True if all validations pass, False otherwise
               issues: List of validation error messages (empty if passed)

    Example:
        passed, issues = validate_door_curve('myCurve1')
        if not passed:
            for issue in issues:
                print(issue)
    """
    issues = []

    try:
        validator = NurbsCurveValidator(curve_name)

        # Check 1: Degree must be 1 (linear)
        degree = validator.get_degree()
        if degree != 1:
            issues.append(f"Degree is {degree}, expected 1 (linear)")

        # Check 2: No construction history
        if validator.has_construction_history():
            issues.append("Curve has construction history (delete history required)")

        # Check 3: Must have exactly 4 CVs
        cv_count = validator.get_cv_count()
        if cv_count != 4:
            issues.append(f"Curve has {cv_count} CVs, expected exactly 4")
            # Can't check rectangle if not 4 CVs
            return False, issues

        # Check 4: All CVs must be planar
        if not validator.is_planar():
            issues.append("CVs are not planar (all CVs must be on same plane)")

        # Check 5 & 6: Rectangle validation
        positions = validator.get_cv_positions()
        tolerance = 0.0001

        # Check vertical edges (bottom and top)
        bottom_y_diff = abs(positions[0][1] - positions[3][1])
        if bottom_y_diff > tolerance:
            issues.append(
                f"Bottom edge not aligned: cv[0].y ({positions[0][1]:.4f}) != cv[3].y ({positions[3][1]:.4f})")

        top_y_diff = abs(positions[1][1] - positions[2][1])
        if top_y_diff > tolerance:
            issues.append(f"Top edge not aligned: cv[1].y ({positions[1][1]:.4f}) != cv[2].y ({positions[2][1]:.4f})")

        # Check horizontal edges (left and right)
        left_x_diff = abs(positions[0][0] - positions[1][0])
        left_z_diff = abs(positions[0][2] - positions[1][2])
        if left_x_diff > tolerance:
            issues.append(
                f"Left edge X not aligned: cv[0].x ({positions[0][0]:.4f}) != cv[1].x ({positions[1][0]:.4f})")
        if left_z_diff > tolerance:
            issues.append(
                f"Left edge Z not aligned: cv[0].z ({positions[0][2]:.4f}) != cv[1].z ({positions[1][2]:.4f})")

        right_x_diff = abs(positions[2][0] - positions[3][0])
        right_z_diff = abs(positions[2][2] - positions[3][2])
        if right_x_diff > tolerance:
            issues.append(
                f"Right edge X not aligned: cv[2].x ({positions[2][0]:.4f}) != cv[3].x ({positions[3][0]:.4f})")
        if right_z_diff > tolerance:
            issues.append(
                f"Right edge Z not aligned: cv[2].z ({positions[2][2]:.4f}) != cv[3].z ({positions[3][2]:.4f})")

        # Return results
        passed = len(issues) == 0
        return passed, issues

    except ValueError as e:
        # Curve doesn't exist or isn't a NURBS curve
        issues.append(str(e))
        return False, issues
    except Exception as e:
        issues.append(f"Unexpected error: {str(e)}")
        return False, issues
