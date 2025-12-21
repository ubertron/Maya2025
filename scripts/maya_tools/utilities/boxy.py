"""Boxy helper object.

https://docs.google.com/drawings/d/1-ZBwQI7VJAlBD0MT4IYBoy0yj76_p17w2ZN1HKV80KI
"""
from enum import Enum, auto
import logging

from maya import cmds

from core import color_classes, math_utils
from core.core_enums import ComponentType, DataType, Side
from core.point_classes import Point3, ZERO3, Point3Pair
from core.logging_utils import get_logger
from maya_tools import attribute_utils, geometry_utils, node_utils
from maya_tools.node_utils import get_object_component_dict
from maya_tools.maya_enums import ObjectType

DEBUG_MODE = False
DEFAULT_SIZE: float = 100.0
LOGGER = get_logger(__name__, level=logging.DEBUG)


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

    Y-sensitive bounds based box that defines a space
    Use to define base centered bounding boxes and as a placeholder for objects
    """

    def __init__(self):
        self.box = None
        self.size = Point3(*[DEFAULT_SIZE for _ in range(3)])
        self.position = ZERO3
        self.rotation_y = 0.0
        self.pivot = Side.bottom
        self.selected_transforms = None
        self.original_selection = cmds.ls(selection=True, flatten=True)
        self.selection = cmds.ls(selection=True, flatten=True)
        self._init_element_type_dict()
        self.selected_transforms = node_utils.get_selected_transforms()

    def __repr__(self):
        """Preview the analysis prior to creation."""
        return (
            f"Element types: {', '.join(x.name for x in self.element_types)}\n"
            f"Transforms: {', '.join(self.selected_transforms)}\n"
            f"Position: {self.position}\n"
            f"Rotation: {self.rotation_y}\n"
            f"Size: {self.size}\n"
        )

    @property
    def components_only(self) -> bool:
        """Returns False if any mesh or curve objects in selection
        Returns True if vertices, cvs or locators in selected
        boxys and invalid are ignored
        """
        if ElementType.mesh in self.element_types or ElementType.curve in self.element_types:
            return False
        return next((True for x in (ElementType.vertex, ElementType.cv, ElementType.locator) if x in self.element_types), False)

    @property
    def two_locators_only(self) -> bool:
        """Returns True if there are only two locators selected."""
        return len(self.selection) == 2 and len(self.element_type_dict.get(ElementType.locator, [])) == 2

    @property
    def element_types(self):
        return list(self.element_type_dict.keys())

    def create(self, pivot: Side = Side.bottom, check_rotations: bool = True) -> str:
        """Evaluate selection."""
        if ElementType.boxy in self.element_type_dict:
            for boxy_item in self.element_type_dict[ElementType.boxy]:
                rebuild_boxy(node=boxy_item)
                self.selection.remove(boxy_item)
        if len(self.selected_transforms) > 1:
            # get bounds of all selected objects
            bounding_box = cmds.exactWorldBoundingBox(self.selection)  # doesn't work properly with locators
            # the bounds from that function get the bounding box of the locator representation, not what we want
            # bounding_box = node_utils.get_bounds_from_selected(self.selection)
            bounds = Point3Pair(Point3(*bounding_box[:3]), Point3(*bounding_box[3:]))
            self.position = bounds.base_center if pivot is Side.bottom else bounds.midpoint
            self.size = bounds.size
        elif len(self.selected_transforms) == 1:
            self.position = node_utils.get_translation(self.selected_transforms[0])
            self.rotation_y = node_utils.get_rotation(self.selected_transforms[0]).y

            # work out the size compensating for rotation
            if self.components_only:
                # get the bounds of locators/verts/cvs
                points = node_utils.get_points_from_selection()
                y_offset = -self.rotation_y if check_rotations else 0.0
                bounds = math_utils.get_bounds_from_points(points=points, y_offset=y_offset)
                self.size = bounds.size
                # if self.two_locators_only:
                #     self.position = bounds.base_center if pivot is Side.bottom else bounds.midpoint
            else:
                # get the bounds from the transform
                self.size = node_utils.get_size(self.selected_transforms[0], check_rotations=check_rotations)
        self._build()


    def _init_element_type_dict(self):
        """Initialize the selection type dict."""
        element_type_dict = {}

        def append_dict_list(_dict, key, value) -> None:
            """Add a value to a list in a dict."""
            if key in _dict:
                _dict[key].append(value)
            else:
                _dict[key]=[value]

        if self.selection:
            for x in self.selection:
                if attribute_utils.get_attribute(node=x, attr="custom_type") == ElementType.boxy.name:
                    append_dict_list(element_type_dict, ElementType.boxy, x)
                elif node_utils.is_locator(x):
                    append_dict_list(_dict=element_type_dict, key=ElementType.locator, value=x)
                elif node_utils.is_geometry(x):
                    append_dict_list(_dict=element_type_dict, key=ElementType.mesh, value=x)
                elif node_utils.is_nurbs_curve(x):
                    append_dict_list(_dict=element_type_dict, key=ElementType.curve, value=x)
                elif cmds.objectType(x) == ObjectType.mesh.name:
                    append_dict_list(_dict=element_type_dict, key=ElementType.mesh, value=x)
                elif cmds.objectType(x) == ObjectType.nurbsCurve.name:
                    append_dict_list(_dict=element_type_dict, key=ElementType.curve, value=x)
                else:
                    append_dict_list(_dict=element_type_dict, key=ElementType.invalid, value=x)
        self._element_type_dict = element_type_dict

    def _build(self):
        """Build boxy box."""
        box = cmds.polyCube(name="boxy", width=self.size.x, height=self.size.y, depth=self.size.z, heightBaseline=-1,
                            constructionHistory=False)[0]
        node_utils.set_translation(nodes=box, value=self.position, absolute=True)
        node_utils.set_rotation(nodes=box, value=Point3(0.0, self.rotation_y, 0.0), absolute=True)
        geometry_utils.set_wireframe_color(node=box, color=color_classes.DEEP_GREEN, shading=False)
        self.box = box
        attribute_utils.add_attribute(
            node=box, attr="custom_type", data_type=DataType.string, read_only=True, default_value="boxy")
        attribute_utils.add_compound_attribute(node=box, parent_attr="size", data_type=DataType.float3,
                                               attrs=["x", "y", "z"], default_values=self.size.values, read_only=True)
        return box

    @property
    def component_mode(self) -> ComponentType:
        return node_utils.get_component_mode()

    @property
    def element_type_dict(self) -> dict:
        return self._element_type_dict

    @property
    def selected_transforms(self) -> list[str]:
        return self._selected_transforms

    @selected_transforms.setter
    def selected_transforms(self, value: list[str]):
        self._selected_transforms = value


def rebuild_boxy(node: str):
    print(f"Recalculating {node}")
