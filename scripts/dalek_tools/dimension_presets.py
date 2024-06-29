from dalek_tools.dalek_builder import DalekDimensions
from core.point_classes import Point3, Point2


CUTE_DALEK: DalekDimensions = DalekDimensions(
        base_height=0.2,
        base_offset=0.125,
        base_bevel=0.35,
        skirt_size=Point2(0.95, 1.25),
        skirt_height=0.7,
        core_top_diameter=0.7,
        core_height=0.3,
        num_sections=8,
        belt_height=0.1,
        belt_offset=0.03,
        lateral_offset=-0.25,
        neck_height=0.275,
        neck_diameter=0.5,
        mesh_diameter=0.625,
        num_fins=5,
        fin_height=0.03,
        fin_diameter=0.75,
        fin_slant=0.7,
        rib_height=0.02,
        rib_inset=0.01,
        rib_offset=0.005,
        neck_taper=-0.2,
        strut_size=Point2(0.025, 0.04),
        head_diameter=0.85,
        head_height=0.35,
        orb_diameter=0.25,
        orb_height=0.1,
        num_orbs=3,
        face_plate_angle=8,
        eye_stalk_length=0.28,
        eye_stalk_diameter=0.035,
        eye_diameter=0.25,
        eye_depth=0.225,
        energy_dispenser_base_radius=0.1,
        energy_dispenser_base_height=0.08,
        energy_dispenser_radius=0.07,
        energy_dispenser_height=0.15,
        energy_dispenser_angle=30,
        weapon_joint_diameter=0.125,
        sucker_arm_length=0.45,
        sucker_arm_diameter=0.05,
        sucker_diameter=0.275,
        sucker_arm_angle=Point3(-15, -10, 0),
        gun_arm_angle=Point3(-15, 10, 0),
        gun_arm_length=0.45,
        rim=0.01,
        cage_bar_radius=0.005,
        num_cage_bars=7,
    )


SKINNY_DALEK: DalekDimensions = DalekDimensions(
        base_height=0.12,
        base_offset=0.08,
        base_bevel=0.35,
        skirt_size=Point2(0.75, 1.0),
        skirt_height=0.8,
        core_top_diameter=0.5,
        core_height=0.35,
        num_sections=18,
        belt_height=0.1,
        belt_offset=0.03,
        lateral_offset=-0.15,
        neck_height=0.275,
        neck_diameter=0.4,
        mesh_diameter=0.5,
        num_fins=5,
        fin_height=0.02,
        fin_diameter=0.61,
        fin_slant=0.5,
        rib_height=0.02,
        rib_inset=0.01,
        rib_offset=0.005,
        neck_taper=0.125,
        strut_size=Point2(0.025, 0.04),
        head_diameter=0.5,
        head_height=0.2,
        orb_diameter=0.09,
        orb_height=0.03,
        num_orbs=7,
        face_plate_angle=8,
        eye_stalk_length=0.38,
        eye_stalk_diameter=0.035,
        eye_diameter=0.22,
        eye_depth=0.16,
        energy_dispenser_base_radius=0.05,
        energy_dispenser_base_height=0.03,
        energy_dispenser_radius=0.04,
        energy_dispenser_height=0.12,
        energy_dispenser_angle=40,
        weapon_joint_diameter=0.125,
        sucker_arm_length=0.65,
        sucker_arm_diameter=0.1,
        sucker_diameter=0.25,
        sucker_arm_angle=Point3(-15, -10, 0),
        gun_arm_angle=Point3(-15, 10, 0),
        gun_arm_length=0.45,
        rim=0.01,
        cage_bar_radius=0.005,
        num_cage_bars=3,
    )

WEIRD_DALEK: DalekDimensions = DalekDimensions(
        base_height=0.15,
        base_offset=0.125,
        base_bevel=0.35,
        skirt_size=Point2(.9, 1.6),
        skirt_height=0.8,
        core_top_diameter=.9,
        core_height=0.28,
        num_sections=15,
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