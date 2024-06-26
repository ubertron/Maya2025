import pyperclip
from dataclasses import dataclass

from core.math_funcs import interpolate_linear, get_midpoint, vector_to_euler_angles, get_normal_vector, \
    get_point_normal_angle_on_ellipse, get_point_position_on_ellipse
from core.point_classes import Point3, Point2, POINT3_ORIGIN, POINT2_ORIGIN, Point3Pair, Z_AXIS, Y_AXIS
from core.environment_utils import is_using_maya_python
from core.core_enums import ComponentType, Axis

if is_using_maya_python():
    from maya import cmds
    from maya_tools.curve_utils import get_cvs, set_cv, create_ellipse, create_polygon_loft_from_curves
    from maya_tools.geometry_utils import merge_vertices, set_edge_softness, get_open_edges, create_hemispheroid, \
        create_platonic_sphere, precision_to_threshold, delete_down_facing_faces, select_faces, get_faces_by_axis, \
        get_component_list, get_component_indices, get_vertices_from_face, delete_faces, get_edges_from_face, \
        select_edges, find_faces_within_y_threshold, filter_face_list_by_face_normal, slice_faces, get_face_above, \
        group_geometry_shells, get_midpoint_from_faces
    from maya_tools.helpers import create_locator
    from maya_tools.node_utils import pivot_to_base, translate, rotate, scale, set_pivot, delete_history, \
        get_translation


@dataclass
class DalekDimensions:
    base_height: float
    base_offset: float
    base_bevel: float
    skirt_size: Point2
    skirt_height: float
    core_top_diameter: float
    core_height: float
    num_sections: int
    subdivisions: int
    belt_height: float
    belt_offset: float
    lateral_offset: float
    neck_height: float
    neck_diameter: float
    num_fins: int
    fin_height: float
    fin_diameter: float
    fin_slant: float
    rib_height: float
    rib_inset: float
    rib_offset: float
    neck_taper: float
    head_diameter: float
    head_height: float
    orb_diameter: float
    orb_height: float
    num_orbs: int
    face_plate_angle: float
    eye_stalk_length: float
    eye_stalk_diameter: float
    eye_diameter: float
    eye_depth: float
    energy_dispenser_base_radius: float
    energy_dispenser_base_height: float
    energy_dispenser_radius: float
    energy_dispenser_height: float
    energy_dispenser_angle: float
    weapon_joint_diameter: float

    def __post_init__(self):
        # Must have at least 1 fin
        self.num_fins = max(self.num_fins, 1)

        # Can't have more fins than spacing
        self.num_fins = min(self.num_fins, int(self.neck_height / self.fin_height))

    def interpolate_torso_size(self, height: float) -> Point2:
        """
        Calculate the size of the body section at a given height
        :param height:
        :return:
        """
        width = interpolate_linear(self.torso_height_range, self.torso_width_range, height)
        length = interpolate_linear(self.torso_height_range, self.torso_length_range, height)
        return Point2(width, length)

    def interpolate_lateral_offset(self, height: float) -> float:
        """
        Calculate the lateral offset at a given height
        :param height:
        :return:
        """
        output_range = Point2(0, self.lateral_offset)
        return interpolate_linear(input_range=self.torso_height_range, output_range=output_range, value=height)

    def interpolate_neck_size(self, height: float, diameter_range: Point2) -> Point2:
        """
        Calculate the neck size at a given height
        :param height:
        :param diameter_range:
        :return:
        """
        size = interpolate_linear(self.neck_height_range, diameter_range, height)
        return Point2(size, size)

    @property
    def skirt_top_position(self) -> Point3:
        return Point3(0, self.base_height + self.skirt_height, 0)

    @property
    def skirt_top_size(self) -> Point2:
        return self.interpolate_torso_size(self.skirt_top_position.y)

    @property
    def torso_height_range(self) -> Point2:
        return Point2(self.base_height, self.core_top_position.y)

    @property
    def torso_width_range(self) -> Point2:
        return Point2(self.skirt_size.x, self.core_top_diameter)

    @property
    def torso_length_range(self) -> Point2:
        return Point2(self.skirt_size.y, self.core_top_diameter)

    @property
    def base_size(self) -> Point2:
        return Point2(self.skirt_size.x + self.base_offset * 2, self.skirt_size.y + self.base_offset * 2)

    @property
    def bevel_value(self):
        return self.base_bevel * min(self.base_height, self.base_offset)

    @property
    def base_bevel_position(self) -> Point3:
        return Point3(0, self.base_height - self.bevel_value, 0)

    @property
    def base_top_size(self) -> Point2:
        return Point2(self.base_size.x - 2 * self.bevel_value, self.base_size.y - 2 * self.bevel_value)

    @property
    def base_top_position(self) -> Point3:
        return Point3(0, self.base_height, 0)

    @property
    def belt_size(self) -> Point2:
        return Point2(self.skirt_size.x + 2 * self.belt_offset, self.skirt_size.y + 2 * self.belt_offset)

    @property
    def belt_bottom_size(self) -> Point2:
        return Point2(*[x + 2 * self.belt_offset for x in self.skirt_top_size.values])

    @property
    def belt_top_size(self) -> Point2:
        return Point2(*[x + 2 * self.belt_offset for x in self.core_bottom_size.values])

    @property
    def core_bottom_position(self) -> Point3:
        return Point3(0, self.core_bottom_height, 0)

    @property
    def core_bottom_height(self) -> float:
        return self.skirt_top_position.y + self.belt_height

    @property
    def core_bottom_size(self) -> Point2:
        return self.interpolate_torso_size(self.core_bottom_position.y)

    @property
    def core_top_position(self) -> Point3:
        return Point3(0, self.core_top_height, 0)

    @property
    def core_center(self) -> Point3:
        midpoint = get_midpoint([self.core_top_position, self.core_bottom_position])
        shifted_z = self.interpolate_lateral_offset(midpoint.y)
        midpoint.z = shifted_z

        return midpoint

    @property
    def core_top_size(self) -> Point2:
        return Point2(self.core_top_diameter, self.core_top_diameter)

    @property
    def core_top_height(self) -> float:
        return self.core_bottom_position.y + self.core_height

    @property
    def base_to_neck(self) -> float:
        return self.core_top_position.y - self.base_height

    @property
    def neck_position(self) -> Point3:
        return Point3(self.core_top_position.x, self.core_top_position.y, self.core_top_position.z + self.lateral_offset)

    @property
    def neck_spacing(self) -> float:
        return (self.neck_height / self.num_fins) - self.fin_height

    @property
    def fin_size(self) -> Point2:
        return Point2(self.fin_diameter, self.fin_diameter)

    @property
    def fin_diameter_range(self) -> Point2:
        return Point2(self.fin_diameter, self.fin_diameter * (1 - self.neck_taper))

    @property
    def neck_size(self) -> Point2:
        return Point2(self.neck_diameter, self.neck_diameter)

    @property
    def neck_diameter_range(self) -> Point2:
        return Point2(self.neck_diameter, self.neck_diameter * (1 - self.neck_taper))

    @property
    def neck_height_range(self) -> Point2:
        return Point2(self.core_top_position.y, self.core_top_position.y + self.neck_height)

    @property
    def head_position(self) -> Point3:
        return Point3(0, self.neck_position.y + self.neck_height, self.lateral_offset)

    @property
    def head_radius_pair(self) -> Point2:
        return Point2(self.head_diameter / 2, self.head_height)


DEFAULT_DIMENSIONS: DalekDimensions = DalekDimensions(
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
        neck_diameter=0.625,
        num_fins=3,
        fin_height=0.02,
        fin_diameter=0.71,
        fin_slant=0.5,
        rib_height=0.02,
        rib_inset=0.01,
        rib_offset=0.005,
        neck_taper=0.125,
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
    )


class DalekBuilder:
    def __init__(self, dimensions: DalekDimensions = DEFAULT_DIMENSIONS):
        self.dimensions = dimensions

    @property
    def curves(self) -> list[str]:
        return cmds.listRelatives(self.curve_group, children=True)

    def add_curve(self, name: str, size: Point2, position: Point3, lateral_offset: bool = False,
                  modify_skirt: bool = False) -> str:
        curve = create_ellipse(name=name, size=size, sections=self.dimensions.num_sections * self.dimensions.subdivisions)
        cmds.parent(curve, self.curve_group)
        translate(curve, value=position)

        if lateral_offset:
            self.apply_lateral_offset(transform=curve)

        if modify_skirt:
            self.modify_skirt_curve(skirt_curve=curve)

        return curve

    def modify_skirt_curve(self, skirt_curve: str):
        """
        Sets every other cv to the midpoint of its neighbours
        :param skirt_curve:
        """
        cvs = get_cvs(skirt_curve, local=True)

        for i in range(self.dimensions.num_sections):
            a_id = i * 2
            middle_id = i * 2 + 1
            b_id = (i * 2 + 2) % (self.dimensions.num_sections * 2)
            midpoint = get_midpoint(points=(cvs[a_id], cvs[b_id]))
            set_cv(transform=skirt_curve, cv_id=middle_id, position=midpoint)

    def apply_lateral_offset(self, transform: str):
        """
        Shifts the transform along the y-axis according to the lateral offset value for the height
        :param transform:
        """
        position = get_translation(transform=transform)
        position.z = self.dimensions.interpolate_lateral_offset(get_translation(transform=transform).y)
        translate(transform, value=position)

    def build(self):
        """
        Public function to build the geometry
        """
        self._build()

    def _build(self):
        """
        Build the geometry
        """
        self.curve_group = cmds.group(name='curve_group', empty=True)
        self.geometry_group = cmds.group(name='geometry_group', empty=True)
        self.locator_group = cmds.group(name='locator_group', empty=True)
        self.orb_group = cmds.group(name='orb_group', empty=True)
        self.head_group = cmds.group(name='head_group', empty=True)
        translate(self.head_group, self.dimensions.head_position)
        cmds.parent(self.orb_group, self.geometry_group)
        cmds.parent(self.head_group, self.geometry_group)

        self._create_body()
        self._create_head()
        self._create_orbs()
        self._create_head_details()

        # cmds.hide(self.geometry_group)
        cmds.hide(self.curve_group)

        if not cmds.listRelatives(self.locator_group, children=True):
            cmds.delete(self.locator_group)

        # cmds.select(clear=True)
        # cmds.select(self.energy_dispenser_base)

    def _create_body(self):
        """
        Build the body section out of curves
        """
        self.pole = self.add_curve(name='pole', size=POINT2_ORIGIN, position=POINT3_ORIGIN)
        self.base0 = self.add_curve(name='base0', size=self.dimensions.base_size, position=POINT3_ORIGIN)
        self.base1 = self.add_curve(name='base1', size=self.dimensions.base_size, position=self.dimensions.base_bevel_position)
        self.base2 = self.add_curve(name='base2', size=self.dimensions.base_top_size, position=self.dimensions.base_top_position)
        self.skirt0 = self.add_curve(name='skirt0', size=self.dimensions.skirt_size, position=self.dimensions.base_top_position, modify_skirt=True)
        self.skirt1 = self.add_curve(name='skirt1', size=self.dimensions.skirt_top_size, position=self.dimensions.skirt_top_position, lateral_offset=True, modify_skirt=True)
        self.belt0 = self.add_curve(name='belt0', size=self.dimensions.belt_bottom_size, position=self.dimensions.skirt_top_position, lateral_offset=True)
        self.belt1 = self.add_curve(name='belt1', size=self.dimensions.belt_top_size, position=self.dimensions.core_bottom_position, lateral_offset=True)
        self.core0 = self.add_curve(name='core0', size=self.dimensions.core_bottom_size, position=self.dimensions.core_bottom_position, lateral_offset=True)
        self.core1 = self.add_curve(name='core1', size=self.dimensions.core_top_size, position=self.dimensions.core_top_position, lateral_offset=True)

        self.neck_curves = []
        ref_position: Point3 = self.dimensions.neck_position  # used for positioning the fin and neck curves

        for i in range(self.dimensions.num_fins):
            fin_base_size = self.dimensions.interpolate_neck_size(height=ref_position.y, diameter_range=self.dimensions.fin_diameter_range)
            fin_base = self.add_curve(name=f'fin_base{i}', size=fin_base_size, position=ref_position)

            ref_position.y += self.dimensions.fin_height * (1 - self.dimensions.fin_slant)
            fin_top_size = self.dimensions.interpolate_neck_size(height=ref_position.y, diameter_range=self.dimensions.fin_diameter_range)
            fin_top = self.add_curve(name=f'fin_top{i}', size=fin_top_size, position=ref_position)

            ref_position.y += self.dimensions.fin_height * self.dimensions.fin_slant
            neck_bottom_size = self.dimensions.interpolate_neck_size(height=ref_position.y, diameter_range=self.dimensions.neck_diameter_range)
            neck_bottom = self.add_curve(name=f'neck_bottom{i}', size=neck_bottom_size, position=ref_position)

            ref_position.y += self.dimensions.neck_spacing
            neck_top_size = self.dimensions.interpolate_neck_size(height=ref_position.y, diameter_range=self.dimensions.neck_diameter_range)
            neck_top = self.add_curve(name=f'neck_top{i}', size=neck_top_size, position=ref_position)

            self.neck_curves.extend([fin_base, fin_top, neck_bottom, neck_top])

        self.dalek_body, _ = create_polygon_loft_from_curves(name='dalek_body', curves=self.curves)

        # Add Core Detail
        face_list = find_faces_within_y_threshold(transform=self.dalek_body, y_value=self.dimensions.core_center.y,
                                                  threshold=0.01)
        # Discount faces that are facing forward
        front_core_faces = filter_face_list_by_face_normal(transform=self.dalek_body, faces=face_list, axis=Z_AXIS, threshold=0.25)
        side_core_faces = [x for x in face_list if x not in front_core_faces]
        select_faces(transform=self.dalek_body, faces=side_core_faces)
        cmds.polyExtrudeFacet(cmds.ls(sl=True), keepFacesTogether=False, offset=self.dimensions.rib_inset)
        cmds.polyExtrudeFacet(cmds.ls(sl=True), localTranslateZ=self.dimensions.rib_height, offset=self.dimensions.rib_offset)

        # Slice core through middle
        slice_faces(transform=self.dalek_body, position=self.dimensions.core_center, axis=Axis.y)

        # The top edges of the front_core_faces are the new faces - get the face ids
        upper_faces = [get_face_above(transform=self.dalek_body, face_id=face_id) for face_id in front_core_faces]
        upper_faces.sort()
        lower_faces = [face for face in front_core_faces if face not in upper_faces]
        lower_faces.sort()
        num_upper_faces = len(upper_faces)

        if num_upper_faces % 2 == 0:
            upper_center_faces: list[int] = [upper_faces[num_upper_faces // 2 - 1], upper_faces[num_upper_faces // 2]]
            lower_center_faces: list[int] = [lower_faces[num_upper_faces // 2 - 1], lower_faces[num_upper_faces // 2]]
        else:
            upper_center_faces: list[int] = [upper_faces[num_upper_faces // 2]]
            lower_center_faces: list[int] = [lower_faces[num_upper_faces // 2]]

        upper_outer_faces: list[int] = [face for face in upper_faces if face not in upper_center_faces]
        lower_outer_faces: list[int] = [face for face in lower_faces if face not in lower_center_faces]

        select_faces(transform=self.dalek_body, faces=upper_outer_faces)
        cmds.polyExtrudeFacet(cmds.ls(sl=True), keepFacesTogether=False, offset=self.dimensions.rib_inset)
        cmds.polyExtrudeFacet(cmds.ls(sl=True), localTranslateZ=self.dimensions.rib_height, offset=self.dimensions.rib_offset)

        select_faces(transform=self.dalek_body, faces=upper_center_faces)
        cmds.polyExtrudeFacet(cmds.ls(sl=True), keepFacesTogether=True, offset=self.dimensions.rib_inset)
        cmds.polyExtrudeFacet(cmds.ls(sl=True), localTranslateZ=self.dimensions.rib_height, offset=self.dimensions.rib_offset)
        cmds.polyExtrudeFacet(cmds.ls(sl=True), offset=self.dimensions.rib_offset)
        cmds.polyExtrudeFacet(cmds.ls(sl=True), localTranslateZ=-self.dimensions.rib_offset, offset=self.dimensions.rib_offset)

        select_faces(transform=self.dalek_body, faces=lower_outer_faces)
        cmds.polyExtrudeFacet(cmds.ls(sl=True), keepFacesTogether=True, offset=self.dimensions.rib_inset)
        cmds.polyExtrudeFacet(cmds.ls(sl=True), keepFacesTogether=True, localTranslateZ=self.dimensions.rib_height * 2, offset=self.dimensions.rib_offset)

        selected_faces = get_component_indices(component_list=cmds.ls(sl=True), component_type=ComponentType.face)
        weapon_ports = group_geometry_shells(transform=self.dalek_body, faces=selected_faces)
        mounting_points = [get_midpoint_from_faces(transform=self.dalek_body, faces=face_list) for face_list in weapon_ports]
        mounting_points.sort(key=lambda x: x.x, reverse=True)
        self.weapon_joint0 = create_platonic_sphere(name='weapon_joint0', diameter=self.dimensions.weapon_joint_diameter, subdivisions=2)
        self.weapon_joint1 = create_platonic_sphere(name='weapon_joint1', diameter=self.dimensions.weapon_joint_diameter, subdivisions=2)
        self.weapon0 = cmds.group(name='weapon0_group', empty=True)
        self.weapon1 = cmds.group(name='weapon1_group', empty=True)
        cmds.parent(self.weapon_joint0, self.weapon0)
        cmds.parent(self.weapon_joint1, self.weapon1)
        translate(self.weapon0, mounting_points[0])
        translate(self.weapon1, mounting_points[1])
        cmds.parent(self.weapon0, self.geometry_group)
        cmds.parent(self.weapon1, self.geometry_group)

        # Clean up mesh
        merge_vertices(transform=self.dalek_body, threshold=0.001)
        set_edge_softness(nodes=self.dalek_body, angle=20)
        cmds.parent(self.dalek_body, self.geometry_group)

    def _create_head(self):
        """
        Create the head geometry
        :return:
        """
        self.head = create_hemispheroid(diameter=self.dimensions.head_diameter, height=self.dimensions.head_height,
                                        primitive=2, subdivisions=3, name='dalek_head', construction_history=False)

        # energy dispensers
        self.energy_dispenser_0 = cmds.polyCylinder(radius=self.dimensions.energy_dispenser_base_radius,
                                                    height=self.dimensions.energy_dispenser_base_height,
                                                    subdivisionsAxis=12, name='energy_dispenser_0')[0]
        delete_down_facing_faces(transform=self.energy_dispenser_0)
        top_face = get_faces_by_axis(transform=self.energy_dispenser_0, axis=Y_AXIS)
        face_component_list = get_component_list(transform=self.energy_dispenser_0, indices=top_face, component_type=ComponentType.face)
        top_edges = cmds.polyListComponentConversion(face_component_list, fromFace=True, toEdge=True)
        cmds.polyBevel(top_edges, offset=0.005)
        top_face = get_faces_by_axis(transform=self.energy_dispenser_0, axis=Y_AXIS)
        select_faces(transform=self.energy_dispenser_0, faces=top_face)
        scale_factor = self.dimensions.energy_dispenser_radius / self.dimensions.energy_dispenser_base_radius
        cmds.polyExtrudeFacet(scaleX=scale_factor, scaleZ=scale_factor)
        taper = 0.75
        cmds.polyExtrudeFacet(localTranslateZ=self.dimensions.energy_dispenser_height, scaleX=taper, scaleZ=taper)
        top_edges = cmds.polyListComponentConversion(cmds.ls(sl=True), fromFace=True, toEdge=True)
        cmds.polyBevel(top_edges, offset=0.005)
        up_faces = get_faces_by_axis(transform=self.energy_dispenser_0, axis=Y_AXIS)
        top_face = next(face for face in up_faces if len(get_vertices_from_face(transform=self.energy_dispenser_0, face_id=face)) > 4)
        edge_components = get_edges_from_face(transform=self.energy_dispenser_0, face_id=top_face, as_components=True)
        delete_faces(transform=self.energy_dispenser_0, faces=top_face)
        cmds.select(edge_components)
        cmds.polyExtrudeEdge(edge_components, scaleX=0.0, scaleZ=0.0)
        open_top_vertices = cmds.polyListComponentConversion(cmds.ls(sl=True), fromEdge=True, toVertex=True)
        cmds.polyMergeVertex(open_top_vertices, distance=0.01)
        set_edge_softness(self.energy_dispenser_0, angle=40)
        self.energy_dispenser_1 = cmds.duplicate(self.energy_dispenser_0, name='energy_dispenser_1')[0]

        # energy dispenser transformations
        position: Point2 = get_point_position_on_ellipse(degrees=self.dimensions.energy_dispenser_angle, ellipse_radius_pair=self.dimensions.head_radius_pair)
        angle: float = get_point_normal_angle_on_ellipse(point=position, ellipse_radius_pair=self.dimensions.head_radius_pair)
        translate(self.energy_dispenser_0, value=position)
        rotate(self.energy_dispenser_0, value=Point3(0, 0, angle))
        translate(self.energy_dispenser_1, value=Point2(-position.x, position.y))
        rotate(self.energy_dispenser_1, value=Point3(0, 0, -angle))
        cmds.parent(self.energy_dispenser_0, self.energy_dispenser_1, self.head)

        # position head on top of dalek
        translate(nodes=self.head, value=self.dimensions.head_position)

        # parent to geometry group
        cmds.parent(self.head, self.head_group)

    def _create_head_details(self):
        depth_coefficient = 0.25
        rim = 0.01
        face_plate_width = self.dimensions.head_diameter * 0.5
        face_plate_height = self.dimensions.head_height * 0.7
        face_plate_depth = self.dimensions.head_diameter * depth_coefficient
        capacitor_z_position = 0.5 * (self.dimensions.eye_stalk_length + face_plate_depth * 0.5)
        face_plate_position = self.dimensions.head_position
        face_plate_position.z += self.dimensions.head_diameter * 0.5 - depth_coefficient * 0.5 * self.dimensions.head_diameter + rim
        eye_stalk_position = Point3(0, face_plate_position.y + face_plate_height * 0.5, face_plate_position.z)

        # face plate
        self.face_plate = cmds.polyCube(width=face_plate_width, height=face_plate_height, depth=face_plate_depth,
                                        subdivisionsX=1, subdivisionsY=1, subdivisionsZ=1, name='face_plate')[0]
        pivot_to_base(self.face_plate, reset=True)
        translate(nodes=self.face_plate, value=face_plate_position)
        set_pivot(nodes=self.face_plate, value=self.dimensions.head_position)
        cmds.delete(f'{self.face_plate}.f[2]')
        cmds.select(f'{self.face_plate}.f[0]')
        cmds.polyExtrudeFacet(localScaleX=self.dimensions.eye_stalk_diameter / face_plate_width, localScaleY=0.6)
        cmds.polyExtrudeFacet(localTranslateZ=-0.015)
        scale(nodes=f'{self.face_plate}.f[1]', value=Point3(0.6, 1, 1), absolute=False)
        cmds.parent(self.face_plate, self.head_group)

        # eyes
        self.eye_stalk_group = cmds.group(name='eye_stalk_group', empty=True)
        self.eye_stalk = cmds.polyCylinder(axis=Z_AXIS.list, radius=self.dimensions.eye_stalk_diameter * 0.5, height=self.dimensions.eye_stalk_length, subdivisionsAxis=7, name='eye_stalk')[0]
        set_edge_softness(nodes=self.eye_stalk, angle=80)
        translate(self.eye_stalk, Point3(0, 0, self.dimensions.eye_stalk_length * 0.5))
        cmds.parent(self.eye_stalk, self.eye_stalk_group)

        self.eye_capacitor = create_platonic_sphere(name='eye_capacitor', diameter=self.dimensions.eye_stalk_diameter * 3.5, subdivisions=2)
        translate(nodes=self.eye_capacitor, value=(Point3(0, 0, capacitor_z_position)))
        scale(nodes=self.eye_capacitor, value=Point3(1, 1, 1.25))
        cmds.parent(self.eye_capacitor, self.eye_stalk_group)

        self.eye = create_hemispheroid(name='eye', diameter=self.dimensions.eye_diameter, height=self.dimensions.eye_depth * 0.5, subdivisions=2, base=False)
        rotate(self.eye, Point3(270, 0, 0))
        translate(self.eye, Point3(0, 0, self.dimensions.eye_stalk_length + self.dimensions.eye_depth * 0.45))
        get_open_edges(self.eye, select=True)
        vertices = cmds.polyListComponentConversion(cmds.ls(sl=True), fromEdge=True, toVertex=True)
        cmds.polyCircularize(vertices, evenlyDistribute=True)
        get_open_edges(self.eye, select=True)
        cmds.polyExtrudeEdge(cmds.ls(sl=True), translateZ=self.dimensions.eye_depth * 0.5)
        cmds.polyExtrudeEdge(cmds.ls(sl=True), localTranslateY=rim, localTranslateZ=-rim)
        cmds.polyExtrudeEdge(cmds.ls(sl=True), scaleX=0.6, scaleY=0.6)
        cmds.polyExtrudeEdge(cmds.ls(sl=True), localTranslateY=rim, localTranslateZ=-rim)
        cmds.polyExtrudeEdge(cmds.ls(sl=True), scaleX=0.0, scaleY=0.0, localTranslateZ=rim * 0.5)
        cmds.select(cmds.polyListComponentConversion(cmds.ls(sl=True), fromEdge=True, toVertex=True))
        cmds.polyMergeVertex(cmds.ls(sl=True), distance=precision_to_threshold(0.1))
        delete_history(self.eye)
        cmds.parent(self.eye, self.eye_stalk_group)
        translate(self.eye_stalk_group, eye_stalk_position)
        cmds.parent(self.eye_stalk_group, self.face_plate)

        rotate(nodes=self.face_plate, value=Point3(-self.dimensions.face_plate_angle, 0, 0), absolute=True)

    def _create_orbs(self, locators: bool = False):
        """
        Place orbs on each skirt panel
        """
        # get the vertices from the skirt curves for each skirt face.
        skirt0_cvs = get_cvs(transform=self.skirt0)
        skirt1_cvs = get_cvs(transform=self.skirt1)
        edge_sections = self.dimensions.subdivisions
        num_cvs = len(skirt0_cvs)

        for i in range(self.dimensions.num_sections):
            cv_id = i * 2
            cv0 = skirt0_cvs[cv_id % num_cvs]
            cv1 = skirt0_cvs[(cv_id + edge_sections) % num_cvs]
            cv2 = skirt1_cvs[(cv_id + edge_sections) % num_cvs]
            cv3 = skirt1_cvs[cv_id % num_cvs]

            # get the path
            orb_path: Point3Pair = Point3Pair(get_midpoint((cv0, cv1)), get_midpoint((cv2, cv3)))
            if locators:
                cmds.parent(create_locator(position=orb_path.a, name=f'orb_path{cv_id}_a', size=0.1), self.locator_group)
                cmds.parent(create_locator(position=orb_path.b, name=f'orb_path{cv_id}_b', size=0.1), self.locator_group)

            # create orbs
            normal_vector: Point3 = get_normal_vector(a=cv0, b=cv1, c=cv3)
            rotation = vector_to_euler_angles(vector=normal_vector)

            for j in range(self.dimensions.num_orbs):
                spacing = 1.0 / self.dimensions.num_orbs
                value = spacing * (float(j) + 0.5)
                position = orb_path.interpolate(value)
                num = i * self.dimensions.num_orbs + j
                self.create_orb(name=f'orb{num}', position=position, rotation=rotation)

    def create_orb(self, name: str, position: Point3, rotation: Point3):
        """
        Create and place a single orb
        :param name:
        :param position:
        :param rotation:
        """
        orb = create_hemispheroid(name=name, diameter=self.dimensions.orb_diameter,
                                  height=self.dimensions.orb_height, subdivisions=2, base=False, select=False,
                                  construction_history=False)
        set_edge_softness(nodes=orb, angle=60)
        rotate(orb, value=rotation)
        translate(orb, value=position)
        cmds.parent(orb, self.orb_group)


if __name__ == '__main__':

    if is_using_maya_python():
        for node in ('dalek_curves', 'dalek_geometry'):
            if cmds.objExists(node):
                cmds.delete(node)

    dalek: DalekBuilder = DalekBuilder()

    if is_using_maya_python():
        dalek.build()
