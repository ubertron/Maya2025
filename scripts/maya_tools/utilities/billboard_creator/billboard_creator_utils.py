"""Billboard Creator."""
from __future__ import annotations  # noqa: I001

from maya import cmds
from pathlib import Path
from maya_tools import material_utils
from core import image_utils
from core.core_enums import Axis



def create_billboard(path: Path, width: float | None = None,
    height: float | None = None, axis: Axis = Axis.y) -> str:
    """Create a plane with a texture applied."""
    image_x, image_y = image_utils.get_image_size(path=path)
    lambert_shader, lambert_sg = material_utils.create_lambert_material(path=path)

    if not width and not height:
        width = 1.0
    if width and not height:
        height = width * image_y / image_x
    elif height and not width:
        width = height * image_x / image_y

    axis_value = {
        Axis.x: [1, 0, 0],
        Axis.y: [0, 1, 0],
        Axis.z: [0, 0, 1],
    }[axis]
    billboard, _ = cmds.polyPlane(name=f"{path.stem}_billboard", width=width, height=height,
        axis=axis_value, subdivisionsWidth=1, subdivisionsHeight=1)
    material_utils.apply_shader(transform=billboard, shader=lambert_shader)

    return billboard



if __name__ == "__main__":
    my_path = Path(r"C:\Users\raptor\Projects\Sandbox\images\at-at_walker.jpg")
    result = create_billboard(path=my_path, width = 10.0)
    print(result)