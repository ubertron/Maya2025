"""
// Error: AttributeError: file /Users/andrewdavis/Dropbox/Technology/Python3/Projects/Maya2025/plug-ins/custom_object.py line 6: module 'maya.api.OpenMaya' has no attribute 'MPxTransform'
// Warning: file: /Applications/Autodesk/maya2026/Maya.app/Contents/scripts/others/pluginWin.mel line 316: Failed to run file: /Users/andrewdavis/Dropbox/Technology/Python3/Projects/Maya2025/plug-ins/custom_object.py
// Error: file: /Applications/Autodesk/maya2026/Maya.app/Contents/scripts/others/pluginWin.mel line 316:  (custom_object)
"""


import maya.api.OpenMaya as om
import maya.cmds as cmds


# Custom transform node class
class CustomTransform(om.MPxTransform):
    kTypeId = om.MTypeId(0x12345)
    kTypeName = "customTransform"

    def __init__(self):
        super(CustomTransform, self).__init__()

    @staticmethod
    def creator():
        return CustomTransform()

    @staticmethod
    def initialize():
        # Add attributes here if necessary
        pass


# Custom shape node class
class CustomShape(om.MPxSurfaceShape):
    kTypeId = om.MTypeId(0x12346)
    kTypeName = "customShape"

    def __init__(self):
        super(CustomShape, self).__init__()

    @staticmethod
    def creator():
        return CustomShape()

    @staticmethod
    def initialize():
        # Add attributes and the shape geometry here
        pass


def create_custom_object():
    # Create the transform node
    transform_node = cmds.createNode("customTransform")

    # Create the shape node
    shape_node = cmds.createNode("customShape", parent=transform_node)

    # Return the transform node for selection and display purposes
    return transform_node


# Create a plugin
class MyCustomPlugin(om.MPxCommand):
    kPluginCmdName = "createMyCustomObject"

    def doIt(self, args):
        cmds.createNode("customTransform", name="myCustomObject")


# Plugin initialization function
def initializePlugin(mobject):
    plugin = om.MFnPlugin(mobject, "Your Name", "1.0", "Any")
    try:
        plugin.registerCommand(MyCustomPlugin.kPluginCmdName, MyCustomPlugin.creator)
        plugin.registerNode(
            CustomTransform.kTypeName,
            CustomTransform.kTypeId,
            CustomTransform.creator,
            CustomTransform.initialize,
            om.MPxNode.kTransformNode
        )
        plugin.registerNode(
            CustomShape.kTypeName,
            CustomShape.kTypeId,
            CustomShape.creator,
            CustomShape.initialize,
            om.MPxNode.kMesh
        )
    except:
        om.MGlobal.displayError("Failed to register node")


def uninitializePlugin(mobject):
    plugin = om.MFnPlugin(mobject)
    try:
        plugin.deregisterCommand(MyCustomPlugin.kPluginCmdName)
        plugin.deregisterNode(CustomTransform.kTypeId)
        plugin.deregisterNode(CustomShape.kTypeId)
    except:
        om.MGlobal.displayError("Failed to unregister node")
