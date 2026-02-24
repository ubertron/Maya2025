"""Sandbox for Architools Studio"""

from maya import cmds
from pathlib import Path
from importlib import reload

from widgets import radio_button_widget; reload(radio_button_widget)
from widgets import float_array_widget; reload(float_array_widget)
from robotools.boxy import boxy_utils; reload(boxy_utils)
from robotools.architools_studio.nodes import base_node; reload(base_node)
from robotools.architools_studio.nodes import size_value; reload(size_value)
from robotools.architools_studio.nodes import meshbox_node; reload(meshbox_node)
from robotools.architools_studio.nodes import architype_template; reload(architype_template)
from robotools.architools_studio import nodes; reload(nodes)
from robotools.architools_studio import template_io; reload(template_io)
from robotools.architools_studio import size_widget; reload(size_widget)
from robotools.architools_studio import editors; reload(editors)
from robotools import architools_studio; reload(architools_studio)
from robotools.architools_studio import architools_studio; reload(architools_studio)

ICONS_DIR = Path.home() / "Dropbox/Technology/Python3/Projects/Maya2025/images/icons"


def copy_icon(filename: str):
    """Copy a default icon."""
    if filename in cmds.resourceManager(nameFilter="*"):
        cmds.resourceManager(saveAs=(filename, ICONS_DIR.joinpath(filename).as_posix()))
        print(f"Icon copied: {filename}")
    else:
        cmds.warning(f"Icon not found: {filename}")


if __name__ == "__main__":
    from maya import cmds
    cmds.file(new=True, force=True)
    architools_studio.launch()
    #result = BoxyComponents(boxy="boxy")
    #print(result)
    #for x in cmds.resourceManager(nameFilter="save*"):
        #print(x)
        
    #copy_icon("saveasdf.png")