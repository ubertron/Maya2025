# Orb Placer
# Script places orbs along the skirt section of a dalek

from importlib import reload

from core.point_classes import Point3, Point3Pair
from maya_tools import geometry_utils; reload(geometry_utils)


class OrbPlacer:
    # from the selected faces, deduce the face areas
    # iterate through faces
    # deduce the placement line
    # get the maximum height/width
    def __init__(self, node: str = ''):
        self.node = geometry_utils.get_transforms(node=node, single=True)
        self.faces = geometry_utils.get_selected_faces(transform=node)
    
    def __repr__(self) -> str:
        return f'Node: {self.node}\nFaces: {len(self.faces)}'

    def place_orbs(self, skirt_faces: list[int], diameter: float, count: int, height: float):
        pass
    
    @property
    def transform(self):
        return 'transform'
    
    @property
    def mesh(self):
        return 'mesh'
    
    @property
    def orb_lines(self) -> list[Point3Pair]:
        pass
        


orb_placer = OrbPlacer()
print(orb_placer)
point_a = Point3(0.0, 0.0, 1.0)
point_b = Point3(1.0, 0.0, 0.0)
point_pair = Point3Pair(point_a, point_b)
print(point_pair)
