import json
import hashlib

from maya import cmds

from maya_tools.ams.asset import Asset
from core.core_enums import AssetType
from maya_tools.ams.project_utils import load_project_definition, get_current_project_root
from maya_tools.scene_utils import get_scene_name, get_scene_path


def generate_rig_hash(asset: Asset) -> str:
    """
    Creates a JSON dictionary from the rig hierarchy
    Returns the hashed result
    :param asset:
    :return:
    """
    assert cmds.objExists(asset.rig_group_node), 'Rig not found'

    def recurse_rig_nodes(rig_dict: dict, node: str):
        if cmds.listRelatives(node, children=True):
            rig_dict[node] = {}
            for child in cmds.listRelatives(node, children=True):
                recurse_rig_nodes(rig_dict=rig_dict[node], node=child)
        else:
            rig_dict[node] = None

    rig_dictionary = {}
    recurse_rig_nodes(rig_dict=rig_dictionary, node=asset.rig_group_node)
    json_str = json.dumps(rig_dictionary, sort_keys=True, indent=2)

    return hashlib.md5(json_str.encode('utf-8')).hexdigest()


def generate_rig_hash_from_current_scene():
    """
    Looks for a valid asset in the current scene and generates the rig hash
    More of a debug function - use generate_rig_hash directly in normal circumstances
    :return:
    """
    current_project = get_current_project_root(file_path=get_scene_path())
    project = load_project_definition(project_root=current_project)
    character_asset = Asset(get_scene_name(include_extension=False), asset_type=AssetType.character, project=project)
    return generate_rig_hash(character_asset)


if __name__ == '__main__':
    result = generate_rig_hash_from_current_scene()
    print(result)
