from maya import cmds
from typing import Sequence, Optional

from core.point_classes import Point3, Point2
from core.core_enums import Axis
from maya_tools.node_utils import get_shape_from_transform, get_transform_from_shape
from maya_tools.maya_enums import ObjectType


def get_cvs(transform: Optional[str] = None, debug: bool = False, local: bool=False) -> list[Point3]:
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
    
    shape = get_shape_from_transform(curve)
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


def create_curve_from_cvs(cvs: Sequence, close: bool = False) -> str or None:
    """
    Create a curve from a list of cv locations
    :param cvs:
    :param close:
    :return:
    """
    curve = cmds.curve(degree=1, point=cvs)
    
    if close:
        closed = cmds.closeCurve(curve)
        cmds.delete(curve)
        curve = closed
    
    cmds.rename(curve, 'curve1')
    return curve


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
        transform = get_transform_from_shape(shape)
        cvs = [x.values for x in get_cvs(transform=transform)]
        reordered_cvs = cvs[idx - 1:] + cvs[:idx - 1]
        result = create_curve_from_cvs(cvs=reordered_cvs, close=True)

        if not keep_original:
            cmds.delete(transform)
            
        return result
    else:
        cmds.warning(assert_message)


def create_ellipse(name: str, size: Point2, axis: Axis = Axis.y, sections: int = 8) -> str:
    """
    Creates a single degree NURBS ellipse with a specific width and length
    :param name:
    :param size:
    :param axis:
    :param sections:
    """
    normal = {Axis.x: (1, 0, 0), Axis.y: (0, 1, 0), Axis.z: (0, 0, 1)}
    ellipse = cmds.circle(degree=1, sections=sections, radius=size.x/2, normal=normal[axis], name=name, ch=False)[0]
    scale_axis = {Axis.x: 'scaleY', Axis.y: 'scaleZ', Axis.z: 'scaleY'}
    cmds.setAttr(f'{ellipse}.{scale_axis[axis]}', size.y/size.x if size.x else 0)
    cmds.makeIdentity(ellipse, apply=True, scale=True)

    return ellipse


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
