import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx

# Define a unique Type ID for your node
kCustomNodeTypeId = om.MTypeId(0x87001)


class MyCustomNode(ompx.MPxNode):
    kNodeName = "myCustomNode"

    # Attributes
    inputAttribute = om.MObject()
    outputAttribute = om.MObject()

    def __init__(self):
        ompx.MPxNode.__init__(self)

    @staticmethod
    def creator():
        return ompx.asMPxPtr(MyCustomNode())

    @staticmethod
    def initialize():
        nAttr = om.MFnNumericAttribute()

        # Create input attribute
        MyCustomNode.inputAttribute = nAttr.create("input", "in", om.MFnNumericData.kFloat)
        nAttr.setStorable(True)
        nAttr.setKeyable(True)

        # Create output attribute
        MyCustomNode.outputAttribute = nAttr.create("output", "out", om.MFnNumericData.kFloat)
        nAttr.setWritable(False)
        nAttr.setStorable(False)

        # Add attributes to the node
        MyCustomNode.addAttribute(MyCustomNode.inputAttribute)
        MyCustomNode.addAttribute(MyCustomNode.outputAttribute)

        # Define attribute dependencies
        MyCustomNode.attributeAffects(MyCustomNode.inputAttribute, MyCustomNode.outputAttribute)

    def compute(self, plug, dataBlock):
        if plug == MyCustomNode.outputAttribute:
            inputValue = dataBlock.inputValue(MyCustomNode.inputAttribute).asFloat()
            outputValue = inputValue * 2.0  # Example computation

            outputHandle = dataBlock.outputValue(MyCustomNode.outputAttribute)
            outputHandle.setFloat(outputValue)
            dataBlock.setClean(plug)
            return True
        return False


# Plugin initialization and uninitialization
def initializePlugin(mobject):
    mplugin = ompx.MFnPlugin(mobject)
    try:
        mplugin.registerNode(MyCustomNode.kNodeName, kCustomNodeTypeId, MyCustomNode.creator, MyCustomNode.initialize)
    except:
        om.MGlobal.displayError("Failed to register node: %s" % MyCustomNode.kNodeName)


def uninitializePlugin(mobject):
    mplugin = ompx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode(kCustomNodeTypeId)
    except:
        om.MGlobal.displayError("Failed to deregister node: %s" % MyCustomNode.kNodeName)