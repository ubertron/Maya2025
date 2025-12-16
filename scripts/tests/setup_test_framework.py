"""
Setup script to create the Maya testing framework structure.
Run this script from your tests directory:
    cd /Users/andrewdavis/Dropbox/Technology/Python3/Projects/Maya2025/scripts/tests
    python setup_test_framework.py
"""

import os
from pathlib import Path

# Define the base directory (where this script is located)
BASE_DIR = Path(__file__).parent

# Define all directories to create
DIRECTORIES = [
    'framework',
    'framework/validators',
    'framework/assertions',
    'unit',
    'integration',
    'validators',
    'fixtures',
    'fixtures/scenes',
    'utils',
]

# Define all files with their content
FILES = {
    '__init__.py': '''"""
Maya Testing Framework
"""
__version__ = "1.0.0"
''',

    'framework/__init__.py': '''"""
Core testing framework components.
"""
from .base import MayaTestCase
from .validators.curve_validator import (
    NurbsCurveValidator,
    NurbsCurveTestCase,
    ValidationRuleset
)

__all__ = [
    'MayaTestCase',
    'NurbsCurveValidator',
    'NurbsCurveTestCase',
    'ValidationRuleset'
]
''',

    'framework/base.py': '''"""
Base test case class for Maya testing.
"""
import unittest
import maya.cmds as cmds


class MayaTestCase(unittest.TestCase):
    """Base test case with Maya scene management."""

    @classmethod
    def setUpClass(cls):
        """Called once before all tests in the class."""
        pass

    @classmethod
    def tearDownClass(cls):
        """Called once after all tests in the class."""
        pass

    def setUp(self):
        """Called before each test method. Creates a fresh scene."""
        cmds.file(new=True, force=True)

    def tearDown(self):
        """Called after each test method. Cleans up the scene."""
        cmds.file(new=True, force=True)

    # Scene Management Helpers
    def create_test_scene(self):
        """Create a clean test scene."""
        cmds.file(new=True, force=True)

    def select_nodes(self, *nodes):
        """Helper to select nodes."""
        cmds.select(nodes, replace=True)

    # Node Existence Assertions
    def assertNodeExists(self, node, msg=None):
        """Assert that a node exists in the scene."""
        if not cmds.objExists(node):
            self.fail(msg or f"Node '{node}' does not exist")

    def assertNodeNotExists(self, node, msg=None):
        """Assert that a node does not exist in the scene."""
        if cmds.objExists(node):
            self.fail(msg or f"Node '{node}' exists but should not")

    # Node Type Assertions
    def assertNodeType(self, node, node_type, msg=None):
        """Assert that a node is of a specific type."""
        actual_type = cmds.nodeType(node)
        if actual_type != node_type:
            self.fail(msg or f"Node '{node}' is type '{actual_type}', expected '{node_type}'")

    # Attribute Assertions
    def assertAttributeExists(self, node, attr, msg=None):
        """Assert that an attribute exists on a node."""
        if not cmds.attributeQuery(attr, node=node, exists=True):
            self.fail(msg or f"Attribute '{attr}' does not exist on node '{node}'")

    def assertAttributeValue(self, node, attr, expected_value, msg=None, tolerance=0.0001):
        """Assert that an attribute has a specific value."""
        full_attr = f"{node}.{attr}"
        actual_value = cmds.getAttr(full_attr)

        if isinstance(expected_value, (int, float)):
            if abs(actual_value - expected_value) > tolerance:
                self.fail(msg or f"Attribute '{full_attr}' is {actual_value}, expected {expected_value}")
        else:
            if actual_value != expected_value:
                self.fail(msg or f"Attribute '{full_attr}' is {actual_value}, expected {expected_value}")

    # Connection Assertions
    def assertConnected(self, source_attr, dest_attr, msg=None):
        """Assert that two attributes are connected."""
        connections = cmds.listConnections(source_attr, 
                                          plugs=True, 
                                          connections=True,
                                          destination=True,
                                          source=False) or []

        if dest_attr not in connections:
            self.fail(msg or f"'{source_attr}' is not connected to '{dest_attr}'")

    # Hierarchy Assertions
    def assertParent(self, child, parent, msg=None):
        """Assert that a node has a specific parent."""
        actual_parent = cmds.listRelatives(child, parent=True)
        if not actual_parent or actual_parent[0] != parent:
            self.fail(msg or f"Node '{child}' does not have parent '{parent}'")

    # Transform Assertions
    def assertTranslation(self, node, expected, msg=None, tolerance=0.0001):
        """Assert that a node has a specific translation."""
        actual = cmds.xform(node, query=True, translation=True, worldSpace=True)
        for i, (a, e) in enumerate(zip(actual, expected)):
            if abs(a - e) > tolerance:
                self.fail(msg or f"Translation mismatch at index {i}: {actual} != {expected}")
''',

    'framework/validators/__init__.py': '''"""
Validators for Maya nodes.
"""
from .curve_validator import NurbsCurveValidator, NurbsCurveTestCase, ValidationRuleset

__all__ = ['NurbsCurveValidator', 'NurbsCurveTestCase', 'ValidationRuleset']
''',

    'framework/validators/curve_validator.py': '''"""
NURBS Curve Validation Framework
"""
import maya.cmds as cmds
import maya.api.OpenMaya as om
from ..base import MayaTestCase


class NurbsCurveValidator:
    """Validation rules for NURBS curves."""

    def __init__(self, curve):
        """Initialize validator with a curve name or shape node."""
        self.curve = curve

        # Get the shape node if transform was provided
        if cmds.nodeType(curve) == 'transform':
            shapes = cmds.listRelatives(curve, shapes=True, type='nurbsCurve')
            if not shapes:
                raise ValueError(f"No NURBS curve shape found under '{curve}'")
            self.shape = shapes[0]
        else:
            self.shape = curve

        if cmds.nodeType(self.shape) != 'nurbsCurve':
            raise ValueError(f"'{self.shape}' is not a NURBS curve")

    def get_degree(self):
        """Get the degree of the curve."""
        return cmds.getAttr(f'{self.shape}.degree')

    def get_spans(self):
        """Get the number of spans."""
        return cmds.getAttr(f'{self.shape}.spans')

    def get_form(self):
        """Get the form of the curve (open, closed, periodic)."""
        form_value = cmds.getAttr(f'{self.shape}.form')
        forms = {0: 'open', 1: 'closed', 2: 'periodic'}
        return forms.get(form_value, 'unknown')

    def get_cv_count(self):
        """Get the number of CVs."""
        return cmds.getAttr(f'{self.shape}.controlPoints', size=True)

    def get_cv_positions(self):
        """Get all CV positions as a list of tuples."""
        cv_count = self.get_cv_count()
        positions = []
        for i in range(cv_count):
            pos = cmds.xform(f'{self.shape}.cv[{i}]', query=True, translation=True, worldSpace=True)
            positions.append(tuple(pos))
        return positions

    def has_construction_history(self):
        """Check if curve has construction history."""
        history = cmds.listHistory(self.shape, pruneDagObjects=True) or []
        history = [h for h in history if h != self.shape]
        return len(history) > 0

    def is_frozen(self):
        """Check if transforms are frozen (at default values)."""
        transform = cmds.listRelatives(self.shape, parent=True)[0]
        translate = cmds.getAttr(f'{transform}.translate')[0]
        rotate = cmds.getAttr(f'{transform}.rotate')[0]
        scale = cmds.getAttr(f'{transform}.scale')[0]

        return (translate == (0, 0, 0) and 
                rotate == (0, 0, 0) and 
                scale == (1, 1, 1))

    def get_curve_length(self):
        """Get the length of the curve."""
        return cmds.arclen(self.shape, constructionHistory=False)

    def has_overlapping_cvs(self, tolerance=0.0001):
        """Check if any CVs are at the same position."""
        positions = self.get_cv_positions()
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions[i+1:], start=i+1):
                distance = sum((a - b) ** 2 for a, b in zip(pos1, pos2)) ** 0.5
                if distance < tolerance:
                    return True, (i, j)
        return False, None

    def is_planar(self, tolerance=0.001):
        """Check if curve is planar (all CVs on same plane)."""
        positions = self.get_cv_positions()
        if len(positions) < 4:
            return True

        p1 = om.MVector(*positions[0])
        p2 = om.MVector(*positions[1])
        p3 = om.MVector(*positions[2])

        v1 = p2 - p1
        v2 = p3 - p1
        normal = v1 ^ v2

        if normal.length() < tolerance:
            if len(positions) < 4:
                return True
            p3 = om.MVector(*positions[3])
            v2 = p3 - p1
            normal = v1 ^ v2

        normal.normalize()

        for pos in positions[3:]:
            p = om.MVector(*pos)
            v = p - p1
            distance = abs(v * normal)
            if distance > tolerance:
                return False

        return True

    def has_matching_start_end(self, tolerance=0.0001):
        """Check if first and last CV are at the same position."""
        positions = self.get_cv_positions()
        if len(positions) < 2:
            return False

        start = positions[0]
        end = positions[-1]
        distance = sum((a - b) ** 2 for a, b in zip(start, end)) ** 0.5
        return distance < tolerance


class NurbsCurveTestCase(MayaTestCase):
    """Extended test case with NURBS curve validation assertions."""

    def assertCurveDegree(self, curve, expected_degree, msg=None):
        """Assert that a curve has a specific degree."""
        validator = NurbsCurveValidator(curve)
        actual_degree = validator.get_degree()
        if actual_degree != expected_degree:
            self.fail(msg or f"Curve '{curve}' has degree {actual_degree}, expected {expected_degree}")

    def assertCurveSpans(self, curve, expected_spans, msg=None):
        """Assert that a curve has a specific number of spans."""
        validator = NurbsCurveValidator(curve)
        actual_spans = validator.get_spans()
        if actual_spans != expected_spans:
            self.fail(msg or f"Curve '{curve}' has {actual_spans} spans, expected {expected_spans}")

    def assertCurveForm(self, curve, expected_form, msg=None):
        """Assert that a curve has a specific form."""
        validator = NurbsCurveValidator(curve)
        actual_form = validator.get_form()
        if actual_form != expected_form:
            self.fail(msg or f"Curve '{curve}' has form '{actual_form}', expected '{expected_form}'")

    def assertCurveCVCount(self, curve, expected_count, msg=None):
        """Assert that a curve has a specific number of CVs."""
        validator = NurbsCurveValidator(curve)
        actual_count = validator.get_cv_count()
        if actual_count != expected_count:
            self.fail(msg or f"Curve '{curve}' has {actual_count} CVs, expected {expected_count}")

    def assertCurveNoHistory(self, curve, msg=None):
        """Assert that a curve has no construction history."""
        validator = NurbsCurveValidator(curve)
        if validator.has_construction_history():
            self.fail(msg or f"Curve '{curve}' has construction history")

    def assertCurveFrozen(self, curve, msg=None):
        """Assert that a curve's transforms are frozen."""
        validator = NurbsCurveValidator(curve)
        if not validator.is_frozen():
            self.fail(msg or f"Curve '{curve}' transforms are not frozen")

    def assertCurveLength(self, curve, expected_length, tolerance=0.001, msg=None):
        """Assert that a curve has a specific length."""
        validator = NurbsCurveValidator(curve)
        actual_length = validator.get_curve_length()
        if abs(actual_length - expected_length) > tolerance:
            self.fail(msg or f"Curve '{curve}' length is {actual_length:.4f}, expected {expected_length:.4f}")

    def assertCurveNoOverlappingCVs(self, curve, tolerance=0.0001, msg=None):
        """Assert that a curve has no overlapping CVs."""
        validator = NurbsCurveValidator(curve)
        has_overlap, indices = validator.has_overlapping_cvs(tolerance)
        if has_overlap:
            self.fail(msg or f"Curve '{curve}' has overlapping CVs at indices {indices}")

    def assertCurvePlanar(self, curve, tolerance=0.001, msg=None):
        """Assert that a curve is planar."""
        validator = NurbsCurveValidator(curve)
        if not validator.is_planar(tolerance):
            self.fail(msg or f"Curve '{curve}' is not planar")

    def assertCurveClosedLoop(self, curve, tolerance=0.0001, msg=None):
        """Assert that a curve's start and end CVs match."""
        validator = NurbsCurveValidator(curve)
        if not validator.has_matching_start_end(tolerance):
            self.fail(msg or f"Curve '{curve}' is not a closed loop")


class ValidationRuleset:
    """Reusable validation ruleset for curves."""

    def __init__(self, test_case, curve):
        self.test = test_case
        self.curve = curve
        self.validator = NurbsCurveValidator(curve)

    def validate_rig_control(self):
        """Standard validation for rig control curves."""
        self.test.assertCurveNoHistory(self.curve)
        self.test.assertCurveFrozen(self.curve)
        self.test.assertCurveNoOverlappingCVs(self.curve)

    def validate_animation_path(self):
        """Standard validation for animation path curves."""
        self.test.assertCurveDegree(self.curve, 3)
        self.test.assertCurveNoOverlappingCVs(self.curve)
        self.test.assertCurveNoHistory(self.curve)

    def validate_planar_shape(self):
        """Validation for planar shapes."""
        self.test.assertCurvePlanar(self.curve)
        self.test.assertCurveFrozen(self.curve)
        self.test.assertCurveNoHistory(self.curve)
''',

    'framework/assertions/__init__.py': '''"""
Custom assertions for Maya testing.
"""
''',

    'unit/__init__.py': '"""Unit tests."""\n',
    'integration/__init__.py': '"""Integration tests."""\n',
    'validators/__init__.py': '"""Validation test suites."""\n',
    'fixtures/__init__.py': '"""Test fixtures and helpers."""\n',
    'utils/__init__.py': '"""Test utilities."""\n',

    'validators/test_rig_controls.py': '''"""
Validation tests for rig control curves.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.framework import NurbsCurveTestCase, ValidationRuleset
import maya.cmds as cmds


class TestRigControlCurves(NurbsCurveTestCase):
    """Test validation of rig control curves."""

    def test_circle_control(self):
        """Test a circle control curve passes validation."""
        curve = cmds.circle(name='ctrl_circle', normal=[0, 1, 0], radius=1)[0]
        cmds.delete(curve, constructionHistory=True)

        ruleset = ValidationRuleset(self, curve)
        ruleset.validate_rig_control()

        self.assertCurveDegree(curve, 3)
        self.assertCurveForm(curve, 'periodic')

    def test_square_control(self):
        """Test a square control curve."""
        points = [(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1), (-1, 0, -1)]
        curve = cmds.curve(name='ctrl_square', degree=1, point=points)

        self.assertCurvePlanar(curve)
        self.assertCurveNoOverlappingCVs(curve)
        self.assertCurveCVCount(curve, 5)

    def test_invalid_control_with_history(self):
        """Test that curve with history fails validation."""
        curve = cmds.circle(name='ctrl_with_history')[0]

        with self.assertRaises(AssertionError):
            self.assertCurveNoHistory(curve)


if __name__ == '__main__':
    import unittest
    unittest.main(verbosity=2)
''',

    'run_tests.py': '''"""
Main test runner for Maya tests.
Run from Maya's script editor or mayapy.
"""
import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_all_tests(verbosity=2):
    """Discover and run all tests."""
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return result


def run_unit_tests(verbosity=2):
    """Run only unit tests."""
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / 'unit'
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)


def run_validators(verbosity=2):
    """Run only validation tests."""
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / 'validators'
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)


def run_integration_tests(verbosity=2):
    """Run only integration tests."""
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / 'integration'
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run Maya tests')
    parser.add_argument('--suite', 
                       choices=['all', 'unit', 'integration', 'validators'],
                       default='all', 
                       help='Test suite to run')
    parser.add_argument('--verbose', '-v', 
                       action='store_true',
                       help='Verbose output')

    args = parser.parse_args()
    verbosity = 2 if args.verbose else 1

    print(f"Running {args.suite} tests...\\n")

    if args.suite == 'all':
        result = run_all_tests(verbosity)
    elif args.suite == 'unit':
        result = run_unit_tests(verbosity)
    elif args.suite == 'integration':
        result = run_integration_tests(verbosity)
    elif args.suite == 'validators':
        result = run_validators(verbosity)

    print(f"\\n{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print('='*60)

    sys.exit(not result.wasSuccessful())
''',

    'fixtures/curves.py': '''"""
Fixture functions for creating test curves.
"""
import maya.cmds as cmds


def create_circle_control(name='ctrl_circle', radius=1.0, clean=True):
    """Create a standard circle control curve."""
    curve = cmds.circle(name=name, normal=[0, 1, 0], radius=radius)[0]
    if clean:
        cmds.delete(curve, constructionHistory=True)
    return curve


def create_square_control(name='ctrl_square', size=1.0):
    """Create a square control curve."""
    half = size / 2.0
    points = [
        (-half, 0, -half),
        (half, 0, -half),
        (half, 0, half),
        (-half, 0, half),
        (-half, 0, -half)
    ]
    return cmds.curve(name=name, degree=1, point=points)


def create_arrow_control(name='ctrl_arrow', size=1.0):
    """Create an arrow control curve."""
    points = [
        (0, 0, size),
        (-size*0.3, 0, size*0.5),
        (-size*0.15, 0, size*0.5),
        (-size*0.15, 0, -size),
        (size*0.15, 0, -size),
        (size*0.15, 0, size*0.5),
        (size*0.3, 0, size*0.5),
        (0, 0, size)
    ]
    return cmds.curve(name=name, degree=1, point=points)
''',

    'README.md': '''# Maya Testing Framework

A comprehensive testing framework for Maya with support for NURBS curve validation and extensible test suites.

## Structure

```
tests/
├── framework/          # Core testing framework
├── unit/              # Unit tests
├── integration/       # Integration tests
├── validators/        # Validation test suites
├── fixtures/          # Test fixtures and helpers
└── utils/            # Test utilities
```

## Running Tests

### From Maya Script Editor

```python
import sys
sys.path.insert(0, '/Users/andrewdavis/Dropbox/Technology/Python3/Projects/Maya2025/scripts')

from tests import run_tests
run_tests.run_all_tests()
```

### Run specific suites

```python
run_tests.run_validators()  # Only validation tests
run_tests.run_unit_tests()  # Only unit tests
```

## Writing Tests

Create a new test file in the appropriate directory:

```python
from tests.framework import NurbsCurveTestCase, ValidationRuleset
import maya.cmds as cmds

class TestMyControls(NurbsCurveTestCase):
    def test_my_control(self):
        curve = cmds.circle(name='my_ctrl')[0]
        cmds.delete(curve, constructionHistory=True)

        ValidationRuleset(self, curve).validate_rig_control()
```

## Available Validators

- **NurbsCurveValidator**: NURBS curve validation
- More validators coming soon!

## Available Assertions

### Curve Assertions
- `assertCurveDegree()`
- `assertCurveSpans()`
- `assertCurveForm()`
- `assertCurveCVCount()`
- `assertCurveNoHistory()`
- `assertCurveFrozen()`
- `assertCurveLength()`
- `assertCurveNoOverlappingCVs()`
- `assertCurvePlanar()`
- `assertCurveClosedLoop()`

### Node Assertions
- `assertNodeExists()`
- `assertNodeType()`
- `assertAttributeExists()`
- `assertAttributeValue()`
- `assertConnected()`
- `assertParent()`
- `assertTranslation()`
''',
}


def create_directory_structure():
    """Create all necessary directories."""
    print("Creating directory structure...")
    for directory in DIRECTORIES:
        dir_path = BASE_DIR / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created: {directory}/")


def create_files():
    """Create all files with their content."""
    print("\\nCreating files...")
    for file_path, content in FILES.items():
        full_path = BASE_DIR / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'w') as f:
            f.write(content)
        print(f"  ✓ Created: {file_path}")


def main():
    """Main setup function."""
    print("=" * 60)
    print("Maya Testing Framework Setup")
    print("=" * 60)
    print(f"\\nBase directory: {BASE_DIR}\\n")

    try:
        create_directory_structure()
        create_files()

        print("\\n" + "=" * 60)
        print("✓ Setup complete!")
        print("=" * 60)
        print("\\nNext steps:")
        print("1. Review the created structure")
        print("2. Run tests from Maya:")
        print("   >>> from tests import run_tests")
        print("   >>> run_tests.run_validators()")
        print("\\n3. Check README.md for more information")

    except Exception as e:
        print(f"\\n✗ Error during setup: {e}")
        raise


if __name__ == '__main__':
    main()