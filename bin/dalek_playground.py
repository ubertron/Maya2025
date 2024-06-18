from importlib import reload
from maya import cmds


from core import point_classes; reload(point_classes)
from core import math_funcs; reload(math_funcs)
from core.core_enums import Axis
from core.point_classes import *
from core.math_funcs import *


def test_func(auto_delete: bool = False):
    locator_a = 'locator_a'
    locator_b = 'locator_b'
    locator_c = 'locator_c'
    locator_d = 'locator_d'
    
    locators = {
        locator_a: (-2.0, 0.0, 0.0),
        locator_b: (2.0, 0.0, 0.0),
        locator_c: (2.0, 3.0, 0.0),
        locator_d: (-2.0, 3.0, 0.0),
    }
    size=0.25

    if auto_delete and cmds.ls('locator*'):
        cmds.delete(cmds.ls('locator*'))

    if cmds.ls('test_sphere*'):
        cmds.delete(cmds.ls('test_sphere*'))
    
    for name, position in locators.items():
        if not cmds.objExists(name):
            cube = cmds.polyCube(name=name, width=size, depth=size, height=size)[0]
            cmds.setAttr(f'{cube}.translate', *position, type='float3')
    
    position_a: Point3 = Point3(*cmds.getAttr(f'{locator_a}.translate')[0])
    position_b: Point3 = Point3(*cmds.getAttr(f'{locator_b}.translate')[0])
    position_c: Point3 = Point3(*cmds.getAttr(f'{locator_c}.translate')[0])
    position_d: Point3 = Point3(*cmds.getAttr(f'{locator_d}.translate')[0])
    midpoint: Point3 = get_midpoint([position_a, position_b, position_c, position_d])
    normal: Point3 = get_normal_vector(position_a, position_b, position_c)
    rotation: Point3 = vector_to_euler_angles(vector=normal)
    test_sphere = cmds.polySphere(name='test_sphere', radius=0.5, subdivisionsX=8, subdivisionsY=6, axis=[0, 1, 0])[0]
    cmds.setAttr(f'{test_sphere}.rotate', *rotation.values)
    cmds.setAttr(f'{test_sphere}.translate', *midpoint.values)
    cmds.select(test_sphere)


    
if __name__ == '__main__':
    test_func()
    