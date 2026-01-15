from importlib import reload

from core import point_classes; reload(point_classes)
reload(math_funcs)
from maya_tools import display_utils; reload(display_utils)
from maya_tools import helpers; reload(helpers)
from maya_tools.geometry import geometry_utils, curve_utils

reload(geometry_utils)
from dalek_tools import dalek_builder; reload(dalek_builder)
reload(curve_utils)
from maya_tools import node_utils; reload(node_utils)
from maya_tools import scene_utils; reload(scene_utils)

from core.point_classes import Point2, Point3

#scene_utils.new_scene()


for x in ('Geometry', 'Locators', 'face_plate', 'dalek_head',
          'energy_dispenser', 'dalek_body', 'sucker_head', 'gun_arm', 'weapon', 'Curves', 'Group'):
    if cmds.objExists(f'{x}*'):
        cmds.delete(cmds.ls(f'{x}*'))


DIMENSIONS: dalek_builder.DalekDimensions = dalek_builder.DalekDimensions(
        base_height=0.15,
        base_offset=0.125,
        base_bevel=0.35,
        skirt_size=Point2(0.95, 1.25),
        skirt_height=0.8,
        core_top_diameter=0.7,
        core_height=0.35,
        num_sections=12,
        subdivisions=2,
        belt_height=0.1,
        belt_offset=0.03,
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
        neck_taper=0.125,
        strut_size=Point2(0.025, 0.04),
        head_diameter=0.61,
        head_height=0.25,
        orb_diameter=0.15,
        orb_height=0.05,
        num_orbs=4,
        face_plate_angle=8,
        eye_stalk_length=0.28,
        eye_stalk_diameter=0.035,
        eye_diameter=0.125,
        eye_depth=0.125,
        energy_dispenser_base_radius=0.05,
        energy_dispenser_base_height=0.03,
        energy_dispenser_radius=0.04,
        energy_dispenser_height=0.08,
        energy_dispenser_angle=30,
        weapon_joint_diameter=0.125,
        sucker_arm_length=0.45,
        sucker_arm_diameter=0.05,
        sucker_diameter=0.175,
        sucker_arm_angle=Point3(-15, -10, 0),
        gun_arm_angle=Point3(-15, 10, 0),
        gun_arm_length=0.45,
        rim=0.01,
        cage_bar_radius=0.005,
        num_cage_bars=7,
    )

dalek_builder.DalekBuilder(show_handles=True).build()
#dalek_builder.DalekBuilder(dimensions=DIMENSIONS, show_handles=True).build()
