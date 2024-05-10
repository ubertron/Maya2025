from maya import cmds

from typing import List


def list_plug_ins(format_info: bool = False) -> List[str]:
    """
    Gets a list of all the plug-ins
    :param format_info:
    :return:
    """
    plugins = cmds.pluginInfo(query=True, listPlugins=True)
    plugins.sort(key=lambda x: x.lower())

    if format_info:
        print('\n'.join(plugins))

    return plugins
