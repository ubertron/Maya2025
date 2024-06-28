from importlib import reload

from core import point_classes; reload(point_classes)
from core import math_funcs; reload(math_funcs)
from maya_tools import node_utils; reload(node_utils)
from maya_tools import geometry_utils; reload(geometry_utils)
from dalek_tools import dalek_builder; reload(dalek_builder)
from maya_tools import scene_utils; reload(scene_utils)

#scene_utils.new_scene()


for x in ('curve_group', 'geometry_group', 'locator_group', 'face_plate', 'dalek_head',
          'energy_dispenser', 'dalek_body', 'sucker_head', 'gun_arm', 'weapon'):
    if cmds.objExists(f'{x}*'):
        cmds.delete(cmds.ls(f'{x}*'))

dalek_builder.DalekBuilder().build()
cmds.select('gun_arm')
