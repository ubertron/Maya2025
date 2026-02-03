# boxy_sandbox.py
import logging
from importlib import reload
from maya import cmds
from pathlib import Path

from core import logging_utils;
from core.point_classes import Point3

reload(logging_utils)
from core.core_enums import ComponentType, Side
from core import core_paths; reload(core_paths)
from core import color_classes, core_enums
from core import point_classes; reload(point_classes)
from core.logging_utils import get_logger
from maya_tools import display_utils, node_utils, scene_utils
from maya_tools.geometry import bounds_utils; reload(bounds_utils)
from maya_tools.utilities.boxy import boxy_tool; reload(boxy_tool)
from maya_tools.utilities.boxy import boxy_utils; reload(boxy_utils)
from maya_tools.utilities.boxy.boxy_data import BoxyData

LOGGER = get_logger(name=__name__, level=logging.DEBUG)
TEST_SCENE = Path("/Users/andrewdavis/Dropbox/Technology/Python3/Projects/Maya2025/scenes/boxy_test_scene.ma")


def run_test_case(*nodes):
    """Run a single test case."""
    if nodes == (None, ):
        node_utils.set_component_mode(ComponentType.object)
        cmds.select(clear=True)
        return
    cmds.select(nodes)
    creator = boxy_utils.Boxy(color=color_classes.RED)
    boxy_nodes, exceptions = creator.create(
        pivot=core_enums.Side.center,
        inherit_rotations=True,
        inherit_scale=True,
        default_size=100)
    LOGGER.debug(f"Boxy nodes: {', '.join(boxy_nodes)}")
    LOGGER.debug(f"Exceptions: {exceptions}")


def run_test_cases(load: bool = False):
    """Run the test scene with test cases."""
    if load:
        scene_utils.load_scene(file_path=TEST_SCENE)
    
    # case 0: single mesh
    run_test_case("staircase1")

    # case 1: single curve1
    run_test_case("curve1")

    # case 2: rotated mesh
    run_test_case("staircase")

    # case 3: two locators
    run_test_case("door_locator0", "door_locator1")

    # case 4: multiple transforms
    run_test_case("door_frame4", "door_frame3")

    # case 5: vertex selection
    run_test_case("door_frame5.vtx[2]", "door_frame5.vtx[10]")

    # case 6: face selection
    run_test_case("door_frame6.f[1:3]")

    # case 7: edge selection
    run_test_case("door_frame7.e[5]", "door_frame7.e[11]")

    # case 8: multiple locators
    run_test_case("door_locator5", "door_locator6", "door_locator4", "door_locator3")

    # case 9: vertex selection rotated transform
    run_test_case("door_frame8.vtx[2]", "door_frame8.vtx[10]")

    # case 10: face selection
    run_test_case("door_frame9.f[1]", "door_frame9.f[3]")

    # case 11: edge selection
    run_test_case("door_frame10.e[5]", "door_frame10.e[11]")
    
    # case 12: verts on transforms
    run_test_case("pCube1.vtx[1]", "pCube1.vtx[3]", "pCube2.vtx[4]", "pCube2.vtx[6]")

    # case 13: grouped mesh
    run_test_case("pCube3")
    
    # case 14: scaled doorway
    run_test_case("doorway.f[2]", "doorway.f[10]")
    
    # case 15: angled doorway
    run_test_case("doorway1.f[2]", "doorway1.f[10]")
    
    # case 16: basic boxy
    run_test_case("boxy")

    # case 17: edited boxy
    run_test_case("boxy1")

    # case 18: rotated + scaled
    run_test_case("scaled_sphere")

    # case 19: boxy and mesh
    run_test_case("boxy3", "pCube4")
    
    # case 20: moved components and rotated
    run_test_case("pCube5")
    
    # case 21: verts on object with child
    run_test_case("external_walls0Shape.vtx[5:6]")
    
    # case 22: nothing
    #run_test_case("sphere_scaled")
    
    # case 23: multiple boxys
    run_test_case("boxy4", "boxy5", "boxy6")
    
    # case 24: flat vertices
    run_test_case("external_walls1ShapeShape.f[0]", "external_walls1ShapeShape.f[12]", "external_walls1ShapeShape.f[13]")
    

def test_boxy_build():
    """Test the functionality of boxy_utils.build()."""
    data = BoxyData(
        size=Point3(10, 10, 10),
        translation=Point3(0, 0, 0),
        rotation=Point3(0, 0, 0),
        pivot_side=Side.bottom,
        color=color_classes.RED,
    )
    result = boxy_utils.build(boxy_data=data)
    print(node_utils.get_translation(result))


if __name__ == "__main__":
    # run_test_cases(load=True)
    boxy_tool.launch()
    # test_boxy_build()
