"""
Boxy Node - Custom Maya DAG node rendering as a wireframe cube.

This plugin provides:
- BoxyShape: MPxLocatorNode subclass for the wireframe cube shape
- BoxyDrawOverride: Viewport 2.0 draw override for rendering
- create_boxy(): Python function for creating boxy nodes

Usage:
    import maya.cmds as cmds
    cmds.loadPlugin('boxy_node.py')

    # Option 1: Use cmds.createNode directly
    cmds.createNode('boxyShape')

    # Option 2: Use the helper function (after importing)
    from maya_tools.utilities.boxy import boxy_node
    boxy_node.create_boxy()
    boxy_node.create_boxy(size=(10, 20, 10), pivot='bottom', color=(0, 1, 0))
"""

import math

import maya.api.OpenMaya as om
import maya.api.OpenMayaRender as omr
import maya.api.OpenMayaUI as omui


def maya_useNewAPI():
    """Required for Maya API 2.0."""
    pass


# Plugin constants
BOXY_SHAPE_NAME = "boxyShape"
BOXY_SHAPE_ID = om.MTypeId(0x00128001)
BOXY_SHAPE_CLASSIFICATION = "drawdb/geometry/boxy"
BOXY_DRAW_OVERRIDE_NAME = "boxyDrawOverride"
BOXY_COMMAND_NAME = "boxy"

# Default values
DEFAULT_SIZE = 100.0
DEFAULT_COLOR = (0.0, 0.627, 0.0)  # Deep green


class BoxyShape(omui.MPxLocatorNode):
    """
    Custom locator node that represents a wireframe cube.

    Attributes:
        customType (string): "boxy" - locked identifier
        pivot (enum): 0=bottom, 1=center, 2=top
        preservePivotPosition (bool): Pivot change behavior flag
        size (float3): Width, height, depth (compound: sizeX, sizeY, sizeZ)
        magnitude (float): Computed diagonal length
        wireframeColor (color/float3): RGB color for wireframe
    """

    # Static attribute MObjects
    customType = None
    pivot = None
    previousPivot = None  # Hidden attribute to track previous pivot value
    preservePivotPosition = None
    sizeX = None
    sizeY = None
    sizeZ = None
    size = None
    magnitude = None
    wireframeColorR = None
    wireframeColorG = None
    wireframeColorB = None
    wireframeColor = None

    # Class-level storage for callbacks (node MObject -> callback ID)
    _callbacks = {}

    def __init__(self):
        omui.MPxLocatorNode.__init__(self)

    def postConstructor(self):
        """Called after the node is created. Register attribute changed callback."""
        thisNode = self.thisMObject()
        callback_id = om.MNodeMessage.addAttributeChangedCallback(
            thisNode, BoxyShape._onAttributeChanged
        )
        # Store callback ID for cleanup
        BoxyShape._callbacks[om.MObjectHandle(thisNode).hashCode()] = callback_id

    @staticmethod
    def _onAttributeChanged(msg, plug, otherPlug, clientData):
        """Callback when an attribute changes."""
        # Only care about attribute set events
        if not (msg & om.MNodeMessage.kAttributeSet):
            return

        # Check if it's the pivot attribute
        if plug.attribute() != BoxyShape.pivot:
            return

        node = plug.node()
        fn = om.MFnDependencyNode(node)

        # Get current (new) pivot value
        newPivot = plug.asInt()

        # Get previous pivot value
        prevPivotPlug = fn.findPlug("previousPivot", False)
        oldPivot = prevPivotPlug.asInt()

        # If pivot hasn't actually changed, skip
        if newPivot == oldPivot:
            return

        # Get preservePivotPosition flag
        preservePlug = fn.findPlug("preservePivotPosition", False)
        preserve = preservePlug.asBool()

        # Get height for offset calculation
        heightPlug = fn.findPlug("sizeY", False)
        height = heightPlug.asFloat()

        # Calculate pivot Y positions relative to cube center
        # bottom (0): pivot at -height/2 from center
        # center (1): pivot at 0 from center
        # top (2): pivot at +height/2 from center
        def pivot_offset(piv, h):
            if piv == 0:  # bottom
                return -h / 2.0
            elif piv == 2:  # top
                return h / 2.0
            return 0.0  # center

        oldOffset = pivot_offset(oldPivot, height)
        newOffset = pivot_offset(newPivot, height)

        # Update previousPivot attribute
        prevPivotPlug.setInt(newPivot)

        # If NOT preserving pivot position, adjust transform to keep cube in place
        if not preserve:
            try:
                # Get the DAG path to the shape node
                dagPath = om.MDagPath.getAPathTo(node)

                # Get the parent transform
                transformPath = om.MDagPath(dagPath)
                transformPath.pop()  # Go up to transform

                transformFn = om.MFnTransform(transformPath)

                # Get current translation
                translation = transformFn.translation(om.MSpace.kTransform)

                # Adjust Y translation: move by (newOffset - oldOffset)
                # This keeps the cube visually in the same world position
                yAdjust = newOffset - oldOffset
                translation.y += yAdjust

                transformFn.setTranslation(translation, om.MSpace.kTransform)
            except Exception as e:
                om.MGlobal.displayWarning(f"Pivot adjust failed: {e}")

    @staticmethod
    def creator():
        return BoxyShape()

    @staticmethod
    def initialize():
        """Define all attributes for the node."""
        nAttr = om.MFnNumericAttribute()
        eAttr = om.MFnEnumAttribute()
        tAttr = om.MFnTypedAttribute()
        cAttr = om.MFnCompoundAttribute()

        # ========== customType (string, locked) ==========
        stringData = om.MFnStringData()
        defaultString = stringData.create("boxy")
        BoxyShape.customType = tAttr.create("customType", "ct", om.MFnData.kString, defaultString)
        tAttr.writable = False
        tAttr.storable = True
        tAttr.hidden = False
        tAttr.channelBox = True

        # ========== pivot (enum: bottom=0, center=1, top=2) ==========
        BoxyShape.pivot = eAttr.create("pivot", "piv", 1)  # default: center
        eAttr.addField("bottom", 0)
        eAttr.addField("center", 1)
        eAttr.addField("top", 2)
        eAttr.keyable = True
        eAttr.storable = True
        eAttr.channelBox = True

        # ========== previousPivot (hidden, for tracking pivot changes) ==========
        BoxyShape.previousPivot = nAttr.create(
            "previousPivot", "ppiv",
            om.MFnNumericData.kInt, 1  # default: center
        )
        nAttr.hidden = True
        nAttr.storable = True

        # ========== preservePivotPosition (bool) ==========
        BoxyShape.preservePivotPosition = nAttr.create(
            "preservePivotPosition", "ppp",
            om.MFnNumericData.kBoolean, False
        )
        nAttr.keyable = True
        nAttr.storable = True
        nAttr.channelBox = True

        # ========== size (float3 compound) ==========
        BoxyShape.sizeX = nAttr.create("sizeX", "sx", om.MFnNumericData.kFloat, DEFAULT_SIZE)
        nAttr.keyable = True
        nAttr.storable = True
        nAttr.setMin(0.001)

        BoxyShape.sizeY = nAttr.create("sizeY", "sy", om.MFnNumericData.kFloat, DEFAULT_SIZE)
        nAttr.keyable = True
        nAttr.storable = True
        nAttr.setMin(0.001)

        BoxyShape.sizeZ = nAttr.create("sizeZ", "sz", om.MFnNumericData.kFloat, DEFAULT_SIZE)
        nAttr.keyable = True
        nAttr.storable = True
        nAttr.setMin(0.001)

        BoxyShape.size = cAttr.create("size", "s")
        cAttr.addChild(BoxyShape.sizeX)
        cAttr.addChild(BoxyShape.sizeY)
        cAttr.addChild(BoxyShape.sizeZ)

        # ========== magnitude (float, computed) ==========
        BoxyShape.magnitude = nAttr.create("magnitude", "mag", om.MFnNumericData.kFloat, 0.0)
        nAttr.writable = False
        nAttr.storable = False
        nAttr.channelBox = True

        # ========== wireframeColor (float3, usedAsColor) ==========
        BoxyShape.wireframeColorR = nAttr.create(
            "wireframeColorR", "wcr",
            om.MFnNumericData.kFloat, DEFAULT_COLOR[0]
        )
        BoxyShape.wireframeColorG = nAttr.create(
            "wireframeColorG", "wcg",
            om.MFnNumericData.kFloat, DEFAULT_COLOR[1]
        )
        BoxyShape.wireframeColorB = nAttr.create(
            "wireframeColorB", "wcb",
            om.MFnNumericData.kFloat, DEFAULT_COLOR[2]
        )
        BoxyShape.wireframeColor = nAttr.create(
            "wireframeColor", "wc",
            BoxyShape.wireframeColorR,
            BoxyShape.wireframeColorG,
            BoxyShape.wireframeColorB
        )
        nAttr.usedAsColor = True
        nAttr.keyable = True
        nAttr.storable = True

        # Add all attributes
        BoxyShape.addAttribute(BoxyShape.customType)
        BoxyShape.addAttribute(BoxyShape.pivot)
        BoxyShape.addAttribute(BoxyShape.previousPivot)
        BoxyShape.addAttribute(BoxyShape.preservePivotPosition)
        BoxyShape.addAttribute(BoxyShape.size)
        BoxyShape.addAttribute(BoxyShape.magnitude)
        BoxyShape.addAttribute(BoxyShape.wireframeColor)

        # Attribute dependencies - size affects magnitude
        BoxyShape.attributeAffects(BoxyShape.sizeX, BoxyShape.magnitude)
        BoxyShape.attributeAffects(BoxyShape.sizeY, BoxyShape.magnitude)
        BoxyShape.attributeAffects(BoxyShape.sizeZ, BoxyShape.magnitude)

    def compute(self, plug, dataBlock):
        """Compute output attributes."""
        if plug == BoxyShape.magnitude:
            sx = dataBlock.inputValue(BoxyShape.sizeX).asFloat()
            sy = dataBlock.inputValue(BoxyShape.sizeY).asFloat()
            sz = dataBlock.inputValue(BoxyShape.sizeZ).asFloat()

            mag = math.sqrt(sx * sx + sy * sy + sz * sz)

            outHandle = dataBlock.outputValue(BoxyShape.magnitude)
            outHandle.setFloat(mag)
            dataBlock.setClean(plug)
            return

        return None

    def boundingBox(self):
        """Return the bounding box for selection and culling."""
        thisNode = self.thisMObject()

        sx = om.MPlug(thisNode, BoxyShape.sizeX).asFloat()
        sy = om.MPlug(thisNode, BoxyShape.sizeY).asFloat()
        sz = om.MPlug(thisNode, BoxyShape.sizeZ).asFloat()
        pivot = om.MPlug(thisNode, BoxyShape.pivot).asInt()

        halfX, halfZ = sx / 2.0, sz / 2.0

        if pivot == 0:  # bottom
            yMin, yMax = 0.0, sy
        elif pivot == 2:  # top
            yMin, yMax = -sy, 0.0
        else:  # center
            halfY = sy / 2.0
            yMin, yMax = -halfY, halfY

        return om.MBoundingBox(om.MPoint(-halfX, yMin, -halfZ), om.MPoint(halfX, yMax, halfZ))


class BoxyUserData(om.MUserData):
    """Cache drawing data for thread-safe rendering."""

    def __init__(self):
        om.MUserData.__init__(self, False)
        self.vertices = []
        self.edges = []
        self.color = om.MColor([DEFAULT_COLOR[0], DEFAULT_COLOR[1], DEFAULT_COLOR[2], 1.0])


class BoxyDrawOverride(omr.MPxDrawOverride):
    """Viewport 2.0 draw override for BoxyShape."""

    @staticmethod
    def creator(obj):
        return BoxyDrawOverride(obj)

    def __init__(self, obj):
        omr.MPxDrawOverride.__init__(self, obj, None, True)

    def supportedDrawAPIs(self):
        return omr.MRenderer.kAllDevices

    def isBounded(self, objPath, cameraPath):
        return True

    def boundingBox(self, objPath, cameraPath):
        node = objPath.node()
        fn = om.MFnDependencyNode(node)

        sx = fn.findPlug("sizeX", False).asFloat()
        sy = fn.findPlug("sizeY", False).asFloat()
        sz = fn.findPlug("sizeZ", False).asFloat()
        pivot = fn.findPlug("pivot", False).asInt()

        halfX, halfZ = sx / 2.0, sz / 2.0

        if pivot == 0:
            yMin, yMax = 0.0, sy
        elif pivot == 2:
            yMin, yMax = -sy, 0.0
        else:
            halfY = sy / 2.0
            yMin, yMax = -halfY, halfY

        return om.MBoundingBox(om.MPoint(-halfX, yMin, -halfZ), om.MPoint(halfX, yMax, halfZ))

    def prepareForDraw(self, objPath, cameraPath, frameContext, oldData):
        data = oldData if isinstance(oldData, BoxyUserData) else BoxyUserData()

        node = objPath.node()
        fn = om.MFnDependencyNode(node)

        sx = fn.findPlug("sizeX", False).asFloat()
        sy = fn.findPlug("sizeY", False).asFloat()
        sz = fn.findPlug("sizeZ", False).asFloat()
        pivot = fn.findPlug("pivot", False).asInt()

        colorR = fn.findPlug("wireframeColorR", False).asFloat()
        colorG = fn.findPlug("wireframeColorG", False).asFloat()
        colorB = fn.findPlug("wireframeColorB", False).asFloat()
        data.color = om.MColor([colorR, colorG, colorB, 1.0])

        halfX, halfZ = sx / 2.0, sz / 2.0

        if pivot == 0:  # bottom
            yMin, yMax = 0.0, sy
        elif pivot == 2:  # top
            yMin, yMax = -sy, 0.0
        else:  # center
            halfY = sy / 2.0
            yMin, yMax = -halfY, halfY

        data.vertices = [
            om.MPoint(-halfX, yMin, -halfZ),
            om.MPoint(halfX, yMin, -halfZ),
            om.MPoint(halfX, yMin, halfZ),
            om.MPoint(-halfX, yMin, halfZ),
            om.MPoint(-halfX, yMax, -halfZ),
            om.MPoint(halfX, yMax, -halfZ),
            om.MPoint(halfX, yMax, halfZ),
            om.MPoint(-halfX, yMax, halfZ),
        ]

        data.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7),
        ]

        return data

    def hasUIDrawables(self):
        return True

    def addUIDrawables(self, objPath, drawManager, frameContext, data):
        if not isinstance(data, BoxyUserData):
            return

        drawManager.beginDrawable()
        drawManager.setColor(data.color)
        drawManager.setLineWidth(1.5)

        for startIdx, endIdx in data.edges:
            drawManager.line(data.vertices[startIdx], data.vertices[endIdx])

        drawManager.endDrawable()


def initializePlugin(mobject):
    """Register all plugin components."""
    mplugin = om.MFnPlugin(mobject, "Robonobo", "1.0", "Any")

    try:
        mplugin.registerNode(
            BOXY_SHAPE_NAME,
            BOXY_SHAPE_ID,
            BoxyShape.creator,
            BoxyShape.initialize,
            om.MPxNode.kLocatorNode,
            BOXY_SHAPE_CLASSIFICATION
        )
    except Exception as e:
        om.MGlobal.displayError(f"Failed to register node: {e}")
        raise

    try:
        omr.MDrawRegistry.registerDrawOverrideCreator(
            BOXY_SHAPE_CLASSIFICATION,
            BOXY_DRAW_OVERRIDE_NAME,
            BoxyDrawOverride.creator
        )
    except Exception as e:
        om.MGlobal.displayError(f"Failed to register draw override: {e}")
        raise

    om.MGlobal.displayInfo("Boxy plugin loaded. Use: cmds.createNode('boxyShape')")


def uninitializePlugin(mobject):
    """Unregister all plugin components."""
    mplugin = om.MFnPlugin(mobject)

    try:
        omr.MDrawRegistry.deregisterDrawOverrideCreator(
            BOXY_SHAPE_CLASSIFICATION,
            BOXY_DRAW_OVERRIDE_NAME
        )
    except:
        pass

    try:
        mplugin.deregisterNode(BOXY_SHAPE_ID)
    except:
        pass

    om.MGlobal.displayInfo("Boxy plugin unloaded.")


# ============================================================================
# Python Helper Functions (alternative to MPxCommand)
# ============================================================================

def _ensure_plugin_loaded():
    """Ensure the boxy plugin is loaded."""
    import maya.cmds as cmds
    plugin_path = __file__
    if not cmds.pluginInfo(plugin_path, query=True, loaded=True):
        cmds.loadPlugin(plugin_path)


def build(boxy_data) -> str:
    """
    Build a custom boxy node from BoxyData.

    This function mirrors the signature of boxy_utils.build() but creates
    a custom MPxLocatorNode instead of a polyCube-based boxy.

    Args:
        boxy_data: BoxyData instance with bounds, pivot, color, and name

    Returns:
        str: The name of the created transform node
    """
    import maya.cmds as cmds
    from core.core_enums import Side

    _ensure_plugin_loaded()

    # Create the shape node
    name = boxy_data.name or "boxy"
    shape = cmds.createNode('boxyShape', name=f'{name}Shape')
    transform = cmds.listRelatives(shape, parent=True)[0]
    transform = cmds.rename(transform, name)

    # Set size from bounds
    size = boxy_data.bounds.size
    cmds.setAttr(f'{shape}.sizeX', size.x)
    cmds.setAttr(f'{shape}.sizeY', size.y)
    cmds.setAttr(f'{shape}.sizeZ', size.z)

    # Set pivot
    pivot_map = {Side.bottom: 0, Side.center: 1, Side.top: 2}
    pivot_value = pivot_map.get(boxy_data.pivot, 1)
    cmds.setAttr(f'{shape}.previousPivot', pivot_value)
    cmds.setAttr(f'{shape}.pivot', pivot_value)

    # Set wireframe color
    color = boxy_data.color
    cmds.setAttr(f'{shape}.wireframeColorR', color.r)
    cmds.setAttr(f'{shape}.wireframeColorG', color.g)
    cmds.setAttr(f'{shape}.wireframeColorB', color.b)

    # Set position from pivot_position
    pos = boxy_data.pivot_position
    cmds.setAttr(f'{transform}.translateX', pos.x)
    cmds.setAttr(f'{transform}.translateY', pos.y)
    cmds.setAttr(f'{transform}.translateZ', pos.z)

    # Set rotation from bounds
    rot = boxy_data.bounds.rotation
    cmds.setAttr(f'{transform}.rotateX', rot.x)
    cmds.setAttr(f'{transform}.rotateY', rot.y)
    cmds.setAttr(f'{transform}.rotateZ', rot.z)

    # Enable selection handle
    cmds.toggle(transform, selectHandle=True)

    # Select the transform
    cmds.select(transform)

    return transform


def create_boxy(size=None, pivot=None, color=None, position=None, name=None):
    """
    Create a boxy node with the specified attributes.

    For integration with the Boxy ecosystem, use build() with BoxyData instead.

    Args:
        size: tuple of (width, height, depth) or None for defaults
        pivot: 'bottom', 'center', or 'top' (default: 'center')
        color: tuple of (r, g, b) values 0-1 or None for default green
        position: tuple of (x, y, z) world position or None
        name: base name for the node or None for auto-naming

    Returns:
        str: The name of the created transform node

    Example:
        create_boxy()
        create_boxy(size=(50, 100, 50), pivot='bottom', color=(1, 0.5, 0), name='myBoxy')
    """
    import maya.cmds as cmds

    _ensure_plugin_loaded()

    # Create the shape node (transform is created automatically)
    if name:
        shape = cmds.createNode('boxyShape', name=f'{name}Shape')
    else:
        shape = cmds.createNode('boxyShape')

    # Get the transform parent
    transform = cmds.listRelatives(shape, parent=True)[0]

    # Rename transform if name provided
    if name:
        transform = cmds.rename(transform, name)

    # Set size attributes
    if size is not None:
        sx, sy, sz = size
        cmds.setAttr(f'{shape}.sizeX', sx)
        cmds.setAttr(f'{shape}.sizeY', sy)
        cmds.setAttr(f'{shape}.sizeZ', sz)

    # Set pivot (set previousPivot first to avoid unwanted translation adjustment)
    if pivot is not None:
        pivot_map = {'bottom': 0, 'center': 1, 'top': 2}
        pivot_value = pivot_map.get(pivot.lower(), 1)
        cmds.setAttr(f'{shape}.previousPivot', pivot_value)
        cmds.setAttr(f'{shape}.pivot', pivot_value)

    # Set wireframe color
    if color is not None:
        r, g, b = color
        cmds.setAttr(f'{shape}.wireframeColorR', r)
        cmds.setAttr(f'{shape}.wireframeColorG', g)
        cmds.setAttr(f'{shape}.wireframeColorB', b)

    # Set position
    if position is not None:
        x, y, z = position
        cmds.setAttr(f'{transform}.translateX', x)
        cmds.setAttr(f'{transform}.translateY', y)
        cmds.setAttr(f'{transform}.translateZ', z)

    # Enable selection handle for visibility
    cmds.toggle(transform, selectHandle=True)

    # Select the transform
    cmds.select(transform)

    return transform
