from importlib import reload

from core import point_classes; reload(point_classes)
from core import math_funcs; reload(math_funcs)
from maya_tools import display_utils; reload(display_utils)
from maya_tools import helpers; reload(helpers)
from dalek_tools import dalek_builder; reload(dalek_builder)
from maya_tools import curve_utils; reload(curve_utils)
from maya_tools import node_utils; reload(node_utils)
from maya_tools import geometry_utils; reload(geometry_utils)
from maya_tools import scene_utils; reload(scene_utils)

#scene_utils.new_scene()


for x in ('Geometry', 'Locators', 'face_plate', 'dalek_head',
          'energy_dispenser', 'dalek_body', 'sucker_head', 'gun_arm', 'weapon', 'Curves', 'Group'):
    if cmds.objExists(f'{x}*'):
        cmds.delete(cmds.ls(f'{x}*'))


dalek_builder.DalekBuilder(show_handles=True).build()
