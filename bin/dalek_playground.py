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

from dalek_tools.dalek_builder import DalekDimensions


dimensions: DalekDimensions = DalekDimensions(
        base_height=0.15,
        base_offset=0.125,
        base_bevel=0.35,
        skirt_size=Point2(.9, 1.6),
        skirt_height=0.8,
        core_top_diameter=.9,
        core_height=0.28,
        num_sections=15,
        subdivisions=2,
        belt_height=0.15,
        belt_offset=0.05,
        lateral_offset=-0.15,
        neck_height=0.275,
        neck_diameter=0.5,
        mesh_diameter=0.625,
        num_fins=3,
        fin_height=0.02,
        fin_diameter=0.71,
        fin_slant=0.5,
        rib_height=0.02,
        rib_inset=0.01,
        rib_offset=0.005,
        neck_taper=-.1,
        strut_size=Point2(0.025, 0.04),
        head_diameter=0.8,
        head_height=0.28,
        orb_diameter=0.15,
        orb_height=0.07,
        num_orbs=3,
        face_plate_angle=8,
        eye_stalk_length=0.48,
        eye_stalk_diameter=0.035,
        eye_diameter=0.185,
        eye_depth=0.125,
        energy_dispenser_base_radius=0.1,
        energy_dispenser_base_height=0.03,
        energy_dispenser_radius=0.08,
        energy_dispenser_height=0.08,
        energy_dispenser_angle=30,
        weapon_joint_diameter=0.125,
        sucker_arm_length=0.25,
        sucker_arm_diameter=0.08,
        sucker_diameter=0.235,
        sucker_arm_angle=Point3(-15, -10, 0),
        gun_arm_angle=Point3(-15, 10, 0),
        gun_arm_length=0.12,
        rim=0.01,
        cage_bar_radius=0.005,
        num_cage_bars=7,
    )


dalek_builder.DalekBuilder(show_handles=True).build()
