"""
// Error: ModuleNotFoundError: file /Users/andrewdavis/Dropbox/Technology/Python3/Projects/Maya2025/plug-ins/my_custom_shape.py line 2: No module named 'maya.api.OpenMayaMPx'
// Warning: file: /Applications/Autodesk/maya2026/Maya.app/Contents/scripts/others/pluginWin.mel line 316: Failed to run file: /Users/andrewdavis/Dropbox/Technology/Python3/Projects/Maya2025/plug-ins/my_custom_shape.py
// Error: file: /Applications/Autodesk/maya2026/Maya.app/Contents/scripts/others/pluginWin.mel line 316:  (my_custom_shape)
"""

import maya.api.OpenMaya as om
import maya.api.OpenMayaMPx as ompx

# Unique ID for your node. Obtain one from Autodesk.
# Use a value within the reserved range for testing.
kPluginNodeId = om.MTypeId(0x00001)
kPluginNodeName = "myCustomShape"

class MyCustomShape(ompx.MPxSurfaceShape):
    def __init__(self):
        super(MyCustomShape, self).__init__()

    @staticmethod
    def creator():
        # Maya calls this method to create an instance of your node.
        return MyCustomShape()

    @staticmethod
    def initializePlugin():
        # This is where you define the node's attributes.
        nAttr = om.MFnNumericAttribute()
        MyCustomShape.radius = nAttr.create("radius", "r", om.MFnNumericData.kFloat)
        nAttr.keyable = True
        nAttr.storable = True
        nAttr.writable = True
        nAttr.readable = True
        nAttr.defaultValue = 1.0

        ompx.MPxNode.addAttribute(MyCustomShape.radius)

    def postConstructor(self):
        # A good place to set up things like object color.
        pass

    def compute(self, plug, dataBlock):
        # This method is called when an output attribute needs to be computed.
        if plug == self.outputMesh:
            # Code to generate geometry and set it on the output plug.
            # In a real-world example, you would build the mesh here.
            pass
        else:
            return om.kUnknownParameter
