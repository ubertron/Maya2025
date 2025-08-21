import os
import sys
import maya.api.OpenMaya as om
import logging
import platform
import shutil

from maya import mel
from pathlib import Path

from startup import pip_utils
from maya_tools import robotools_utils


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


class RobotoolsInitializeCmd(om.MPxCommand):
    kPluginCmdName = 'RobotoolsShelfInitialize'

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RobotoolsInitializeCmd()

    def doIt(self, args):
        raise Exception('Plugin not supposed to be invoked - only loaded or unloaded.')


def initializePlugin(plugin):
    """
    Initialize the plug-in
    @param plugin:
    """
    vendor = 'Robonobo'
    version = '2.0'
    pluginFn = om.MFnPlugin(plugin, vendor, version)

    try:
        logging.info('>>> Robotools plugin initialize script')
        pip_utils.install_requirements()
        robotools_utils.setup_robotools()
        pluginFn.registerCommand(RobotoolsInitializeCmd.kPluginCmdName, RobotoolsInitializeCmd.cmdCreator)
    except RuntimeError as err:
        raise RuntimeError(f'Failed to register command: {RobotoolsInitializeCmd.kPluginCmdName}\nError: {err}')


def uninitializePlugin(plugin):
    """
    Uninitialize the plugin
    @param plugin:
    """
    pluginFn = om.MFnPlugin(plugin)

    try:
        logging.info('>>> Robotools plugin uninitialize script')
        logging.info('>>> Deleting Robotools')
        robotools_utils.delete_robotools()
        pluginFn.deregisterCommand(RobotoolsInitializeCmd.kPluginCmdName)
    except RuntimeError:
        raise RuntimeError(f'Failed to unregister command: {RobotoolsInitializeCmd.kPluginCmdName}\n')
