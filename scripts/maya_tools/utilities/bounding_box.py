from maya import cmds

from core.point_classes import Point3Pair
from maya_tools import node_utils


class BoundingBox:
    def __init__(self, transform: str):
        self.transform = transform

        # check that transform has attached mesh node
        shape = node_utils.get_shape_from_transform(node=transform)
        if shape:
            print(cmds.objectType(shape))


    @property
    def bounds(self) -> Point3Pair:
        return True