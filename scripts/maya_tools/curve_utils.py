from maya import cmds
from typing import Sequence, Optional

from maya_tools.node_utils import get_shape_from_transform, get_transform_from_shape
from maya_tools.maya_enums import ObjectType


def get_cvs(transform: Optional[str] = None, debug: bool = False) -> list[float]:
    """
    Get the location of all the cvs in a curve
    :param transform:
    :param debug:
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
    return [cmds.pointPosition(f'{shape}.cv[{i}]') for i in range(num_cvs)]


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
        cvs = get_cvs(transform=transform)
        reordered_cvs = cvs[idx - 1:] + cvs[:idx - 1]
        result = create_curve_from_cvs(cvs=reordered_cvs, close=True)

        if not keep_original:
            cmds.delete(transform)
            
        return result
    else:
        cmds.warning(assert_message)
