"""robotools plug-in

Version 1.0 - Initial
Version 2.0 - Next version
Version 2.1 - Bug fixes for Novomac
Version 2.2 - Change of shelf tech
"""

import maya.api.OpenMaya as om
import logging

from maya import mel

from core import DEVELOPER
from maya_tools import shelf_utils

LOGGER = logging.getLogger(__name__)
PLUGIN_NAME = "Novotools"


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


class NovotoolsInitializeCmd(om.MPxCommand):
    kPluginCmdName = 'NovotoolsInitialize'

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return NovotoolsInitializeCmd()

    def doIt(self, args):
        raise Exception('Plugin not supposed to be invoked - only loaded or unloaded.')


def initializePlugin(plugin):
    """
    Initialize the plug-in
    @param plugin:
    """
    vendor = DEVELOPER
    version = '2.2'
    pluginFn = om.MFnPlugin(plugin, vendor, version)

    try:
        LOGGER.info(f'>>> {PLUGIN_NAME} plugin initialize script')
        shelf_utils.ShelfManager().build()
        shelf_utils.set_current_shelf("Novotools")
        pluginFn.registerCommand(NovotoolsInitializeCmd.kPluginCmdName, NovotoolsInitializeCmd.cmdCreator)
    except RuntimeError as err:
        raise RuntimeError(f'Failed to register command: {NovotoolsInitializeCmd.kPluginCmdName}\nError: {err}')


def uninitializePlugin(plugin):
    """
    Uninitialize the plugin
    @param plugin:
    """
    pluginFn = om.MFnPlugin(plugin)

    try:
        LOGGER.info(f'>>> {PLUGIN_NAME} plugin uninitialize script')
        shelf_utils.ShelfManager().delete()
        pluginFn.deregisterCommand(NovotoolsInitializeCmd.kPluginCmdName)
    except RuntimeError:
        raise RuntimeError(f'Failed to unregister command: {NovotoolsInitializeCmd.kPluginCmdName}\n')
