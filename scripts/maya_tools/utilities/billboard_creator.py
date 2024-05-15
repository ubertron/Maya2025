from PIL import Image
from pathlib import Path
from maya import cmds

from core.core_enums import ObjectType
from maya_tools.node_utils import pivot_to_base, move_to_origin
from maya_tools.material_utils import apply_shader, lambert_file_texture_shader


DALEK_IMAGE: Path = Path(__file__).parents[3].joinpath('images/dalek.png')


class BillboardCreator:
    def __init__(self, image_path: Path, billboard_width: float = 1.0):
        assert image_path.exists(), 'Path not found.'
        self.image_path: Path = image_path
        self.billboard_width = billboard_width

    def __repr__(self) -> str:
        return f'Path: {self.image_path} [{self.resolution[0]}, {self.resolution[1]}]'

    @property
    def resolution(self) -> tuple[int, int]:
        return Image.open(self.image_path.as_posix()).size

    @property
    def aspect_ratio(self) -> float:
        width, height = self.resolution
        return float(width) / float(height)

    @property
    def billboard_height(self) -> float:
        return self.billboard_width / self.aspect_ratio

    def create(self):
        billboard, shape = cmds.polyPlane(
            name=self.image_path.stem,
            width=self.billboard_width, height=self.billboard_height,
            subdivisionsX=1, subdivisionsY=1,
            createUVs=1,
            axis=(0, 0, 1))
        pivot_to_base(transform=billboard)
        move_to_origin(billboard)
        lambert_shader, shading_group = lambert_file_texture_shader(texture_path=self.image_path)
        apply_shader(shading_group=shading_group, transforms=billboard)

        for panel in cmds.getPanel(type=ObjectType.modelPanel.name):
            cmds.modelEditor(panel, edit=True, displayTextures=True)

        return billboard, shape
