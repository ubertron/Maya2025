from importlib import reload

from core.point_classes import Point3
from core.core_enums import Side
from core import color_classes
from maya_tools import attribute_utils; reload(attribute_utils)
from maya_tools.geometry import geometry_utils; reload(geometry_utils)
from robotools.architools import (
    staircase_creator,
    door_creator,
    arch_utils,
    window_creator,
    arch_creator
)
reload(arch_creator)
from robotools.architools.architools_widgets import (
    door_widget,
    staircase_widget,
    window_widget,
    arch_widget, architools_help)
reload(arch_widget)
reload(door_widget)
reload(window_widget)
reload(staircase_widget)
reload(architools_help)
from robotools.boxy import boxy_utils; reload(boxy_utils)
from robotools.architools import architools; reload(architools)
reload(door_creator)
reload(window_creator)
reload(staircase_creator)
reload(arch_utils)

from core.bounds import Bounds
#from robotools.architools.architools_widgets import arch_widget; reload(arch_widget)


def create_door():
    creator: door_creator.DoorCreator = door_creator.DoorCreator(
        skirt=4,
        frame=4,
        door_depth=44,
        hinge_side=Side.left,
        opening_side=Side.front,
        auto_texture=True)



def create_boxy():
    bounds = Bounds(size=Point3(100, 100, 100), position=Point3(0,0,0), rotation=Point3(0,0,0))
    data = boxy_utils.BoxyData(bounds=bounds, pivot=Side.bottom, color=color_classes.DEEP_GREEN, name="boxy_")
    print(data)
    boxy_utils.build(boxy_data=data)
    

if __name__ == "__main__":
    architools.launch()
    #create_door()
    #result = arch_utils.get_custom_type(custom_type = CustomType.boxy)
    #result = node_utils.is_custom_type(node="boxy", custom_type=CustomType.boxy)
    #print(result)
    #create_boxy()
    #from maya import cmds
    #print(cmds.displaySurface("cube", xRay=True, query=True)[0])

   