from __future__ import annotations

from maya import cmds
from typing import Sequence, Optional

from core.color_classes import RGBColor
from core.core_enums import Axis
from core.point_classes import Point3, Point2
from maya_tools import node_utils
from maya_tools.helpers import create_locator
from maya_tools.maya_enums import ObjectType


def get_cvs(transform: Optional[str] = None, debug: bool = False, local: bool = False) -> list[Point3]:
    """
    Get the location of all the cvs in a curve
    :param transform:
    :param debug:
    :param local:
    :return:
    """
    assert_message: str = "Please select a single curve"

    if transform:
        curve = transform
    else:
        selection = cmds.ls(sl=True, tr=True)
        assert len(selection) == 1, assert_message
        curve = selection[0]

    shape = node_utils.get_shape_from_transform(curve)
    degree = cmds.getAttr(f'{shape}.degree')
    spans = cmds.getAttr(f'{shape}.spans')
    form = cmds.getAttr(f'{shape}.form')
    num_cvs = spans + degree - 1

    if debug:
        print(f'Shape: {shape}')
        print(f'Degree: {degree}')
        print(f'Spans: {spans}')
        print(f'Form: {form}')

    assert cmds.nodeType(shape) == ObjectType.nurbsCurve.name, assert_message
    result = [cmds.pointPosition(f'{shape}.cv[{i}]', local=local) for i in range(num_cvs)]

    return [Point3(*x) for x in result]


def set_cv(transform: str, cv_id: int, position: Point3):
    """
    Sets the position of a cv
    :param transform:
    :param cv_id:
    :param position:
    """
    cmds.setAttr(f'{transform}.cv[{cv_id}]', *position.values, type='float3')


def create_curve_from_points(points: Sequence[Point3], close: bool = False, name: str = '',
                             color: RGBColor | None = None) -> str or None:
    """
    Create a curve from a list of cv locations
    :param name:
    :param color:
    :param points:
    :param close:
    :return:
    """
    curve = cmds.curve(degree=1, point=[x.values for x in points])

    if close:
        closed = cmds.closeCurve(curve)
        cmds.delete(curve)
        curve = closed

    new_name = cmds.rename(curve, name if name else 'curve0')
    shape = node_utils.get_shape_from_transform(node=new_name)
    if color is not None:
        cmds.setAttr(f"{shape}.overrideColorRGB", *color.normalized)
        cmds.setAttr(f"{shape}.overrideRGBColors", 1)
        cmds.setAttr(f"{shape}.overrideEnabled", True)
    else:
        cmds.setAttr(f"{shape}.overrideEnabled", False)
        cmds.setAttr(f"{shape}.overrideRGBColors", 0)
    return new_name


def rebuild_closed_curve_from_selected_cv(keep_original: bool = True) -> str or None:
    """
    Change the starting cv of a closed curve
    :param keep_original:
    :return:
    """
    assert_message = "Select a single cv"
    selection = cmds.ls(sl=True)
    assert len(selection) == 1, assert_message
    selected = selection[0]

    if '.cv' in selected:
        idx = selected.split('.cv[')[1].split(']')[0]
        assert idx.isnumeric(), assert_message
        idx = int(idx)
        shape = cmds.listRelatives(selected, parent=True)[0]
        transform = node_utils.get_transform_from_shape(shape)
        cvs = [x.values for x in get_cvs(transform=transform)]
        reordered_cvs = cvs[idx - 1:] + cvs[:idx - 1]
        point_list = [Point3(*x) for x in reordered_cvs]
        result = create_curve_from_points(points=point_list, close=True)

        if not keep_original:
            cmds.delete(transform)

        return result
    else:
        cmds.warning(assert_message)


def create_ellipse(name: str, size: Point2, axis: Axis = Axis.y, sections: int = 8, history: bool = False) -> str:
    """
    Creates a single degree NURBS ellipse with a specific width and length
    :param name:
    :param size:
    :param axis:
    :param sections:
    :param history:
    """
    normal = {Axis.x: (1, 0, 0), Axis.y: (0, 1, 0), Axis.z: (0, 0, 1)}
    ellipse = cmds.circle(degree=1, sections=sections, radius=size.x / 2, normal=normal[axis], name=name, ch=history)[0]
    scale_axis = {Axis.x: 'scaleY', Axis.y: 'scaleZ', Axis.z: 'scaleY'}
    cmds.setAttr(f'{ellipse}.{scale_axis[axis]}', size.y / size.x if size.x else 0)
    cmds.makeIdentity(ellipse, apply=True, scale=True)

    return ellipse


def create_circle(name: str, radius: float, axis: Axis = Axis.y, sections: int = 8, history: bool = False) -> str:
    """
    Creates a single degree NURBS circle with a specific width and length
    :param name:
    :param radius:
    :param axis:
    :param sections:
    :param history:
    """
    return create_ellipse(name=name, size=Point2(2 * radius, 2 * radius), axis=axis, sections=sections, history=history)


def create_polygon_loft_from_curves(name: str, curves: list[str], close_surface: bool = False) -> tuple:
    """
    Creates a lofted mesh object from a set of curves
    :param name:
    :param curves:
    :param close_surface:
    :return:
    """
    cmds.nurbsToPolygonsPref(polyType=1, format=3)
    geometry, loft_node = cmds.loft(curves, degree=1, polygon=1, close=close_surface, name=name)

    return geometry, loft_node


def create_linear_spline(name: str, points: list[Point3]):
    """
    Creates a linear NURBS spline from a set of points
    :param name:
    :param points:
    :return:
    """
    spline = cmds.curve(degree=1, point=[point.values for point in points], worldSpace=True)
    result = cmds.rename(spline, name)

    return result
