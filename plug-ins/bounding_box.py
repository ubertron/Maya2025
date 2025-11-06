import os
import sys
import maya.api.OpenMaya as om
import logging

from maya import mel

from core.logging_utils import get_logger_basic

LOGGER = get_logger_basic(__name__, level=logging.DEBUG)


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


# command
class BoundingBoxInitializeCmd(om.MPxCommand):
    kPluginCmdName = 'BoundingBoxInitialize'

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return BoundingBoxInitializeCmd()

    def doIt(self, args):
        raise Exception('Plugin not supposed to be invoked - only loaded or unloaded.')


def initializePlugin(plugin):
    """
    Initialize the plug-in
    @param plugin:
    """
    vendor = 'Robonobo'
    version = '0.1'
    pluginFn = om.MFnPlugin(plugin, vendor, version)

    try:
        # imports
        LOGGER.info('>>>> BoundingBox imports')

        # code
        LOGGER.info('>>>> BoundingBox set up')

        pluginFn.registerCommand(BoundingBoxInitializeCmd.kPluginCmdName, BoundingBoxInitializeCmd.cmdCreator)
    except RuntimeError:
        raise RuntimeError(f'Failed to register command: {BoundingBoxInitializeCmd.kPluginCmdName}\n')


def uninitializePlugin(plugin):
    """
    Uninitialize the plugin
    @param plugin:
    """
    pluginFn = om.MFnPlugin(plugin)

    try:
        teardown()
        pluginFn.deregisterCommand(BoundingBoxInitializeCmd.kPluginCmdName)
    except RuntimeError:
        raise RuntimeError('Failed to unregister command: %s\n' % BoundingBoxInitializeCmd.kPluginCmdName)


def teardown():
    """
    Reverse the routine to unload the plug-in
    """
    LOGGER.info('>>>> Teardown of BoundingBox')
