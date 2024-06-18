from importlib import reload
from maya import cmds


from core import point_classes; reload(point_classes)
from core import math_funcs; reload(math_funcs)
from core.point_classes import *
from core.math_funcs import *

def test_func(auto_delete: bool = False):
    label_a = 'locator_a'
    label_b = 'locator_b'
    position_a = (-2.0, 0.0, 0.0)
    position_b = (0.0, 2.0, 0.0)
    size=0.25

    if auto_delete and cmds.ls('locator*'):
        cmds.delete(cmds.ls('locator*'))
    
    
    if cmds.objExists(label_a):
        locator_a = cmds.ls(label_a)[0]
    else:
        locator_a = cmds.polyCube(name=label_a, width=size, depth=size, height=size)[0]
        cmds.setAttr(f'{locator_a}.translate', *position_a, type='float3')
    
    
    if cmds.objExists(label_b):
        locator_b = cmds.ls(label_b)[0]
    else:
        locator_b = cmds.polyCube(name='locator_b', width=size, depth=size, height=size)[0]
        cmds.setAttr(f'{locator_b}.translate', *position_b, type='float3')
    
    
    locator_a_point = Point3(*cmds.getAttr(f'{locator_a}.translate')[0])
    locator_b_point = Point3(*cmds.getAttr(f'{locator_b}.translate')[0])
    point_pair = Point3Pair(a=locator_a_point, b=locator_b_point)
    
    
    print(point_pair)
    print(point_pair.interpolate_position(0))
    print(point_pair.interpolate_position(0.5))
    print(point_pair.interpolate_position(1.0))
    
    if cmds.ls('test_sphere*'):
        cmds.delete(cmds.ls('test_sphere*'))
    
    test_sphere = cmds.polySphere(radius=0.2, axis=(0, 1, 0), subdivisionsX=8, subdivisionsY=6, name='test_sphere')[0]
    #cmds.setAttr(f'{test_sphere}.rotate', 90, 0, 0, type='float3')
    #print(cmds.getAttr(test_sphere + ".worldMatrix"))
    #matrix0 = rotate_x(IDENTITY_MATRIX, point_pair.x_angle)
    #matrix1 = rotate_y(matrix0, point_pair.y_angle)
    #cmds.xform(test_sphere, matrix=flatten_matrix(matrix0))
    x_rotation = radians_to_degrees(point_pair.x_angle)
    y_rotation = radians_to_degrees(point_pair.y_angle)
    cmds.setAttr(f'{test_sphere}.rotate', x_rotation, y_rotation, 0, type='float3')
    cmds.setAttr(f'{test_sphere}.translate', *point_pair.midpoint.values)


if __name__ == '__main__':
    test_func(auto_delete=False)
    