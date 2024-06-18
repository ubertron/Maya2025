import math

from dataclasses import dataclass

from core.math_funcs import interpolate_linear, get_midpoint, cross_product, vector_to_euler_angles, get_vector, \
    radians_to_degrees, get_normal_vector
from core.point_classes import Point3, Point2, POINT3_ORIGIN, POINT2_ORIGIN, Point3Pair, Point2Pair
from core.environment_utils import is_using_maya_python

if is_using_maya_python():
    from maya import cmds
    from maya_tools.curve_utils import get_cvs, set_cv, create_ellipse, create_polygon_loft_from_curves
    from maya_tools.geometry_utils import merge_vertices, set_edge_softness, get_vertex_positions, \
        get_vertex_face_list, select_faces, get_open_edges, create_hemispheroid
    from maya_tools.utilities.helpers import create_locator


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
    neck_taper: float
    head_diameter: float
    head_height: float
    orb_diameter: float
    orb_height: float
    num_orbs: int

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
        neck_taper=0.125,
        head_diameter=0.61,
        head_height=0.25,
        orb_diameter=0.15,
        orb_height=0.05,
        num_orbs=4,
    )


class DalekBuilder:
    def __init__(self, dimensions: DalekDimensions = DEFAULT_DIMENSIONS):
        self.dimensions = dimensions

    def add_curve(self, name: str, size: Point2, position: Point3, lateral_offset: bool = False,
                  modify_skirt: bool = False) -> str:
        curve = create_ellipse(name=name, size=size, sections=self.dimensions.num_sections * self.dimensions.subdivisions)
        cmds.parent(curve, self.curve_group)
        cmds.setAttr(f'{curve}.translate', *position.values, type='float3')

        if lateral_offset:
            self.apply_lateral_offset(transform=curve)

        if modify_skirt:
            self.modify_skirt_curve(skirt_curve=curve)

        return curve

    def apply_lateral_offset(self, transform: str):
        """
        Shifts the transform along the y-axis according to the lateral offset value for the height
        :param transform:
        """
        lateral_offset = self.dimensions.interpolate_lateral_offset(cmds.getAttr(f'{transform}.translateY'))
        cmds.setAttr(f'{transform}.translateZ', lateral_offset)

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
        cmds.parent(self.orb_group, self.geometry_group)

        self._create_body()
        self._create_head()
        self._create_orbs()
        # cmds.hide(self.geometry_group)
        # cmds.hide(self.curve_group)

        if not cmds.listRelatives(self.locator_group, children=True):
            cmds.delete(self.locator_group)

        cmds.select(clear=True)

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
        merge_vertices(transform=self.dalek_body)
        set_edge_softness(node_selection=self.dalek_body, angle=20)
        cmds.parent(self.dalek_body, self.geometry_group)


    def _create_head(self):
        """
        Create the head geometry
        :return:
        """
        self.head = create_hemispheroid(diameter=self.dimensions.head_diameter, height=self.dimensions.head_height,
                                        primitive=2, subdivisions=3, name='dalek_head', construction_history=False)

        # position on top of dalek
        cmds.setAttr(f'{self.head}.translate', *self.dimensions.head_position.values, type='float3')

        # parent to geometry group
        cmds.parent(self.head, self.geometry_group)

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
        set_edge_softness(node_selection=orb, angle=60)
        cmds.setAttr(f'{orb}.rotate', *rotation.values, type='float3')
        cmds.setAttr(f'{orb}.translate', *position.values, type='float3')
        cmds.parent(orb, self.orb_group)

    @property
    def curves(self) -> list[str]:
        return cmds.listRelatives(self.curve_group, children=True)

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


if __name__ == '__main__':

    if is_using_maya_python():
        for node in ('dalek_curves', 'dalek_geometry'):
            if cmds.objExists(node):
                cmds.delete(node)

    dalek: DalekBuilder = DalekBuilder()

    if is_using_maya_python():
        dalek.build()

    # interpolate_linear(Point2(10, 20), Point2(110, 120), 5)
    # interpolate_linear(Point2(10, 20), Point2(110, 120),
    # interpolate_linear(Point2(10, 20), Point2(110, 120), 15)
    # interpolate_linear(Point2(10, 20), Point2(110, 120), 20)
    # interpolate_linear(Point2(10, 20), Point2(110, 120), 25)
    # print(f'skirt_top_position: {dalek_dimensions.skirt_top_position.y}')
    # print(f'skirt_top_size: {dalek_dimensions.skirt_top_size}')
    # print(f'core_bottom_position: {dalek_dimensions.core_bottom_position.y}')
    # print(f'core_bottom_size: {dalek_dimensions.core_bottom_size}')
    # print(0.15, dalek_dimensions.interpolate_size(0.15))
    # print(0.95, dalek_dimensions.interpolate_size(0.95))
    # print(1.05, dalek_dimensions.interpolate_size(1.05))
    # print('1.05', dalek_dimensions.interpolate_lateral_offset(1.05))
    # print(dalek_dimensions.num_fins)
