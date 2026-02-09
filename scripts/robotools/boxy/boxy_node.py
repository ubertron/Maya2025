"""
ROBOTOOLS STUDIO PROPRIETARY SOFTWARE LICENSE

Copyright (c) 2026 Andrew Davis / Robotools Studio. All Rights Reserved.

1. OWNERSHIP
   This software is the proprietary property of Andrew Davis / Robotools Studio.
   All intellectual property rights remain with the copyright holder.

2. RESTRICTIONS
   Without explicit written permission, you may NOT:
   - Copy, reproduce, or distribute this software
   - Modify, adapt, or create derivative works
   - Reverse engineer, decompile, or disassemble this software
   - Remove or alter any proprietary notices
   - Use this software in production environments without pre-arranged
     agreement with Andrew Davis / Robotools Studio
   - Sublicense, rent, lease, or lend this software

3. LICENSING
   Individual and commercial licenses are available.
   For licensing inquiries: andy_j_davis@yahoo.com

4. DISCLAIMER
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
   IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM,
   DAMAGES, OR OTHER LIABILITY ARISING FROM THE USE OF THIS SOFTWARE.

5. PROTECTED TECHNOLOGIES
   - Boxy Plugin and BoxyShape custom node
   - Bounds calculation utilities
   - Related tools and plugins
"""
# Boxy Node - Custom Maya DAG node rendering as a wireframe cube.
#
# This plugin provides:
# - BoxyShape: MPxLocatorNode subclass for the wireframe cube shape
# - BoxyDrawOverride: Viewport 2.0 draw override for rendering
# - create_boxy(): Python function for creating boxy nodes
#
# Usage:
#     import maya.cmds as cmds
#     cmds.loadPlugin('boxy_node.py')
#
#     # Option 1: Use cmds.createNode directly
#     cmds.createNode('boxyShape')
#
#     # Option 2: Use the helper function (after importing)
#     from robotools.boxy import boxy_node
#     boxy_node.create_boxy()
#     boxy_node.create_boxy(size=(10, 20, 10), pivot='bottom', color=(0, 1, 0))

import math
from pathlib import Path

import maya.api.OpenMaya as om
import maya.api.OpenMayaRender as omr
import maya.api.OpenMayaUI as omui

# File logger for debugging plugin load
LOG_FILE = Path.home() / "boxy_node_debug.log"


def _log(msg):
    """Write a message to the debug log file."""
    with open(LOG_FILE, "a") as f:
        f.write(f"{msg}\n")


def _clear_log():
    """Clear the debug log file."""
    with open(LOG_FILE, "w") as f:
        f.write("=== Boxy Plugin Debug Log ===\n")


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


class BoxyShape(om.MPxSurfaceShape):
    """
    Custom surface shape node that represents a wireframe cube.

    Using MPxSurfaceShape instead of MPxLocatorNode to properly support
    bounding box queries for Frame Selected (f key) and viewFit.

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
        om.MPxSurfaceShape.__init__(self)

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
        try:
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

            # Get size for offset calculation (from shape attributes - unscaled)
            sizeX = fn.findPlug("sizeX", False).asFloat()
            sizeY = fn.findPlug("sizeY", False).asFloat()
            sizeZ = fn.findPlug("sizeZ", False).asFloat()

            # Update previousPivot attribute
            prevPivotPlug.setInt(newPivot)

            # If NOT preserving pivot position, adjust transform to keep cube in place
            if not preserve:
                # Get the DAG path to the shape node
                dagPath = om.MDagPath.getAPathTo(node)

                # Get the parent transform
                transformPath = om.MDagPath(dagPath)
                transformPath.pop()  # Go up to transform

                transformFn = om.MFnTransform(transformPath)

                # Get transform's scale - we need to apply scale to the offset
                scale = transformFn.scale()
                scaledSizeX = sizeX * scale[0]
                scaledSizeY = sizeY * scale[1]
                scaledSizeZ = sizeZ * scale[2]

                # Calculate pivot offset from center for each pivot type
                # Returns (x, y, z) offset from center to pivot position in LOCAL space
                # Use SCALED size since the visual offset in world space is affected by scale
                def pivot_offset(piv, sx, sy, sz):
                    if piv == 0:  # bottom
                        return (0.0, -sy / 2.0, 0.0)
                    elif piv == 2:  # top
                        return (0.0, sy / 2.0, 0.0)
                    elif piv == 3:  # left (min X)
                        return (-sx / 2.0, 0.0, 0.0)
                    elif piv == 4:  # right (max X)
                        return (sx / 2.0, 0.0, 0.0)
                    elif piv == 5:  # front (max Z)
                        return (0.0, 0.0, sz / 2.0)
                    elif piv == 6:  # back (min Z)
                        return (0.0, 0.0, -sz / 2.0)
                    return (0.0, 0.0, 0.0)  # center

                oldOffset = pivot_offset(oldPivot, scaledSizeX, scaledSizeY, scaledSizeZ)
                newOffset = pivot_offset(newPivot, scaledSizeX, scaledSizeY, scaledSizeZ)

                # Calculate the local-space offset (from old pivot to new pivot)
                localOffsetX = newOffset[0] - oldOffset[0]
                localOffsetY = newOffset[1] - oldOffset[1]
                localOffsetZ = newOffset[2] - oldOffset[2]

                # Get the transform's rotation to convert local offset to world space
                rotation = transformFn.rotation(om.MSpace.kTransform, asQuaternion=False)

                # Build rotation-only matrix and transform local offset to world space
                rotMatrix = rotation.asMatrix()
                localOffsetVec = om.MVector(localOffsetX, localOffsetY, localOffsetZ)
                worldOffsetVec = localOffsetVec * rotMatrix

                # Get current translation and adjust by the world-space offset
                translation = transformFn.translation(om.MSpace.kTransform)
                translation.x += worldOffsetVec.x
                translation.y += worldOffsetVec.y
                translation.z += worldOffsetVec.z

                transformFn.setTranslation(translation, om.MSpace.kTransform)
        except Exception:
            # Silently ignore errors during node initialization
            pass

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

        # ========== pivot (enum) ==========
        BoxyShape.pivot = eAttr.create("pivot", "piv", 1)  # default: center
        eAttr.addField("bottom", 0)
        eAttr.addField("center", 1)
        eAttr.addField("top", 2)
        eAttr.addField("left", 3)
        eAttr.addField("right", 4)
        eAttr.addField("front", 5)
        eAttr.addField("back", 6)
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
        nAttr.setMin(0.0)

        BoxyShape.sizeY = nAttr.create("sizeY", "sy", om.MFnNumericData.kFloat, DEFAULT_SIZE)
        nAttr.keyable = True
        nAttr.storable = True
        nAttr.setMin(0.0)

        BoxyShape.sizeZ = nAttr.create("sizeZ", "sz", om.MFnNumericData.kFloat, DEFAULT_SIZE)
        nAttr.keyable = True
        nAttr.storable = True
        nAttr.setMin(0.0)

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

    def isBounded(self):
        """Return True to indicate this shape has a bounding box for framing."""
        return True

    def boundingBox(self):
        """Return the bounding box for selection and framing (Frame Selected 'f' key)."""
        try:
            thisNode = self.thisMObject()

            # Use MFnDependencyNode.findPlug for robustness (survives plugin reloads)
            fn = om.MFnDependencyNode(thisNode)
            sx = fn.findPlug("sizeX", False).asFloat()
            sy = fn.findPlug("sizeY", False).asFloat()
            sz = fn.findPlug("sizeZ", False).asFloat()
            pivot = fn.findPlug("pivot", False).asInt()

            halfX, halfY, halfZ = sx / 2.0, sy / 2.0, sz / 2.0

            # Default: center pivot
            xMin, xMax = -halfX, halfX
            yMin, yMax = -halfY, halfY
            zMin, zMax = -halfZ, halfZ

            if pivot == 0:  # bottom
                yMin, yMax = 0.0, sy
            elif pivot == 2:  # top
                yMin, yMax = -sy, 0.0
            elif pivot == 3:  # left (min X)
                xMin, xMax = 0.0, sx
            elif pivot == 4:  # right (max X)
                xMin, xMax = -sx, 0.0
            elif pivot == 5:  # front (max Z)
                zMin, zMax = -sz, 0.0
            elif pivot == 6:  # back (min Z)
                zMin, zMax = 0.0, sz

            return om.MBoundingBox(om.MPoint(xMin, yMin, zMin), om.MPoint(xMax, yMax, zMax))
        except Exception:
            # Return default bounding box during plugin reload
            return om.MBoundingBox(om.MPoint(-50, -50, -50), om.MPoint(50, 50, 50))


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
        try:
            node = objPath.node()
            fn = om.MFnDependencyNode(node)

            sx = fn.findPlug("sizeX", False).asFloat()
            sy = fn.findPlug("sizeY", False).asFloat()
            sz = fn.findPlug("sizeZ", False).asFloat()
            pivot = fn.findPlug("pivot", False).asInt()

            halfX, halfY, halfZ = sx / 2.0, sy / 2.0, sz / 2.0

            # Default: center pivot
            xMin, xMax = -halfX, halfX
            yMin, yMax = -halfY, halfY
            zMin, zMax = -halfZ, halfZ

            if pivot == 0:  # bottom
                yMin, yMax = 0.0, sy
            elif pivot == 2:  # top
                yMin, yMax = -sy, 0.0
            elif pivot == 3:  # left (min X)
                xMin, xMax = 0.0, sx
            elif pivot == 4:  # right (max X)
                xMin, xMax = -sx, 0.0
            elif pivot == 5:  # front (max Z)
                zMin, zMax = -sz, 0.0
            elif pivot == 6:  # back (min Z)
                zMin, zMax = 0.0, sz

            return om.MBoundingBox(om.MPoint(xMin, yMin, zMin), om.MPoint(xMax, yMax, zMax))
        except Exception:
            # Return default bounding box during plugin reload
            return om.MBoundingBox(om.MPoint(-50, -50, -50), om.MPoint(50, 50, 50))

    def prepareForDraw(self, objPath, cameraPath, frameContext, oldData):
        data = oldData if isinstance(oldData, BoxyUserData) else BoxyUserData()

        try:
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

            halfX, halfY, halfZ = sx / 2.0, sy / 2.0, sz / 2.0

            # Default: center pivot
            xMin, xMax = -halfX, halfX
            yMin, yMax = -halfY, halfY
            zMin, zMax = -halfZ, halfZ

            if pivot == 0:  # bottom
                yMin, yMax = 0.0, sy
            elif pivot == 2:  # top
                yMin, yMax = -sy, 0.0
            elif pivot == 3:  # left (min X)
                xMin, xMax = 0.0, sx
            elif pivot == 4:  # right (max X)
                xMin, xMax = -sx, 0.0
            elif pivot == 5:  # front (max Z)
                zMin, zMax = -sz, 0.0
            elif pivot == 6:  # back (min Z)
                zMin, zMax = 0.0, sz

            data.vertices = [
                om.MPoint(xMin, yMin, zMin),
                om.MPoint(xMax, yMin, zMin),
                om.MPoint(xMax, yMin, zMax),
                om.MPoint(xMin, yMin, zMax),
                om.MPoint(xMin, yMax, zMin),
                om.MPoint(xMax, yMax, zMin),
                om.MPoint(xMax, yMax, zMax),
                om.MPoint(xMin, yMax, zMax),
            ]

            data.edges = [
                (0, 1), (1, 2), (2, 3), (3, 0),
                (4, 5), (5, 6), (6, 7), (7, 4),
                (0, 4), (1, 5), (2, 6), (3, 7),
            ]
        except Exception:
            # Return default data during plugin reload
            pass

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


class BoxyCommand(om.MPxCommand):
    """Command to create a boxy node with optional flags."""

    # Size flags
    kSizeXFlag = "-sx"
    kSizeXLongFlag = "-sizeX"
    kSizeYFlag = "-sy"
    kSizeYLongFlag = "-sizeY"
    kSizeZFlag = "-sz"
    kSizeZLongFlag = "-sizeZ"

    # Pivot flag (0=bottom, 1=center, 2=top)
    kPivotFlag = "-p"
    kPivotLongFlag = "-pivot"

    # Color flags
    kColorRFlag = "-cr"
    kColorRLongFlag = "-colorR"
    kColorGFlag = "-cg"
    kColorGLongFlag = "-colorG"
    kColorBFlag = "-cb"
    kColorBLongFlag = "-colorB"

    # Position flags
    kPosXFlag = "-px"
    kPosXLongFlag = "-positionX"
    kPosYFlag = "-py"
    kPosYLongFlag = "-positionY"
    kPosZFlag = "-pz"
    kPosZLongFlag = "-positionZ"

    # Name flag - use object selection instead of string flag
    kNameFlag = "-n"
    kNameLongFlag = "-name"

    def __init__(self):
        om.MPxCommand.__init__(self)
        self._created_node = None

    @staticmethod
    def creator():
        return BoxyCommand()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        # Size flags
        syntax.addFlag(BoxyCommand.kSizeXFlag, BoxyCommand.kSizeXLongFlag, om.MSyntax.kDouble)
        syntax.addFlag(BoxyCommand.kSizeYFlag, BoxyCommand.kSizeYLongFlag, om.MSyntax.kDouble)
        syntax.addFlag(BoxyCommand.kSizeZFlag, BoxyCommand.kSizeZLongFlag, om.MSyntax.kDouble)
        # Pivot flag (long: 0=bottom, 1=center, 2=top)
        syntax.addFlag(BoxyCommand.kPivotFlag, BoxyCommand.kPivotLongFlag, om.MSyntax.kLong)
        # Color flags
        syntax.addFlag(BoxyCommand.kColorRFlag, BoxyCommand.kColorRLongFlag, om.MSyntax.kDouble)
        syntax.addFlag(BoxyCommand.kColorGFlag, BoxyCommand.kColorGLongFlag, om.MSyntax.kDouble)
        syntax.addFlag(BoxyCommand.kColorBFlag, BoxyCommand.kColorBLongFlag, om.MSyntax.kDouble)
        # Position flags
        syntax.addFlag(BoxyCommand.kPosXFlag, BoxyCommand.kPosXLongFlag, om.MSyntax.kDouble)
        syntax.addFlag(BoxyCommand.kPosYFlag, BoxyCommand.kPosYLongFlag, om.MSyntax.kDouble)
        syntax.addFlag(BoxyCommand.kPosZFlag, BoxyCommand.kPosZLongFlag, om.MSyntax.kDouble)
        # Name uses command argument instead of flag to avoid kString issues
        syntax.setObjectType(om.MSyntax.kStringObjects, 0, 1)
        return syntax

    def doIt(self, args):
        """Create a boxy node with optional flags."""
        import maya.cmds as cmds

        # Parse arguments
        argParser = om.MArgParser(self.syntax(), args)

        # Parse size
        size = None
        if (argParser.isFlagSet(BoxyCommand.kSizeXFlag) or
            argParser.isFlagSet(BoxyCommand.kSizeYFlag) or
            argParser.isFlagSet(BoxyCommand.kSizeZFlag)):
            size = (
                argParser.flagArgumentDouble(BoxyCommand.kSizeXFlag, 0) if argParser.isFlagSet(BoxyCommand.kSizeXFlag) else DEFAULT_SIZE,
                argParser.flagArgumentDouble(BoxyCommand.kSizeYFlag, 0) if argParser.isFlagSet(BoxyCommand.kSizeYFlag) else DEFAULT_SIZE,
                argParser.flagArgumentDouble(BoxyCommand.kSizeZFlag, 0) if argParser.isFlagSet(BoxyCommand.kSizeZFlag) else DEFAULT_SIZE,
            )

        # Parse pivot (0=bottom, 1=center, 2=top)
        pivot = None
        if argParser.isFlagSet(BoxyCommand.kPivotFlag):
            pivot = argParser.flagArgumentInt(BoxyCommand.kPivotFlag, 0)

        # Parse color
        color = None
        if (argParser.isFlagSet(BoxyCommand.kColorRFlag) or
            argParser.isFlagSet(BoxyCommand.kColorGFlag) or
            argParser.isFlagSet(BoxyCommand.kColorBFlag)):
            color = (
                argParser.flagArgumentDouble(BoxyCommand.kColorRFlag, 0) if argParser.isFlagSet(BoxyCommand.kColorRFlag) else DEFAULT_COLOR[0],
                argParser.flagArgumentDouble(BoxyCommand.kColorGFlag, 0) if argParser.isFlagSet(BoxyCommand.kColorGFlag) else DEFAULT_COLOR[1],
                argParser.flagArgumentDouble(BoxyCommand.kColorBFlag, 0) if argParser.isFlagSet(BoxyCommand.kColorBFlag) else DEFAULT_COLOR[2],
            )

        # Parse position
        position = None
        if (argParser.isFlagSet(BoxyCommand.kPosXFlag) or
            argParser.isFlagSet(BoxyCommand.kPosYFlag) or
            argParser.isFlagSet(BoxyCommand.kPosZFlag)):
            position = (
                argParser.flagArgumentDouble(BoxyCommand.kPosXFlag, 0) if argParser.isFlagSet(BoxyCommand.kPosXFlag) else 0.0,
                argParser.flagArgumentDouble(BoxyCommand.kPosYFlag, 0) if argParser.isFlagSet(BoxyCommand.kPosYFlag) else 0.0,
                argParser.flagArgumentDouble(BoxyCommand.kPosZFlag, 0) if argParser.isFlagSet(BoxyCommand.kPosZFlag) else 0.0,
            )

        # Parse name from command objects (first positional argument)
        name = None
        if argParser.numberOfFlagUses(BoxyCommand.kNameFlag) == 0:
            # Check for positional argument
            objs = argParser.getObjectStrings()
            if objs:
                name = objs[0]

        # Create shape node
        if name:
            shape = cmds.createNode('boxyShape', name=f'{name}Shape')
        else:
            shape = cmds.createNode('boxyShape')

        transform = cmds.listRelatives(shape, parent=True)[0]

        # Rename transform if name provided
        if name:
            transform = cmds.rename(transform, name)
            # Get the updated shape name after transform rename
            shape = cmds.listRelatives(transform, shapes=True)[0]

        # Set size if provided
        if size:
            cmds.setAttr(f'{shape}.sizeX', size[0])
            cmds.setAttr(f'{shape}.sizeY', size[1])
            cmds.setAttr(f'{shape}.sizeZ', size[2])

        # Set pivot if provided (set previousPivot first to avoid unwanted translation adjustment)
        if pivot is not None:
            cmds.setAttr(f'{shape}.previousPivot', pivot)
            cmds.setAttr(f'{shape}.pivot', pivot)

        # Set color if provided
        if color:
            cmds.setAttr(f'{shape}.wireframeColorR', color[0])
            cmds.setAttr(f'{shape}.wireframeColorG', color[1])
            cmds.setAttr(f'{shape}.wireframeColorB', color[2])

        # Set position if provided
        if position:
            cmds.setAttr(f'{transform}.translateX', position[0])
            cmds.setAttr(f'{transform}.translateY', position[1])
            cmds.setAttr(f'{transform}.translateZ', position[2])

        # Enable selection handle
        cmds.toggle(transform, selectHandle=True)

        # Select and return
        cmds.select(transform)
        self._created_node = transform

        self.setResult(transform)

    def isUndoable(self):
        return True


def initializePlugin(mobject):
    """Register all plugin components."""
    _clear_log()
    _log("initializePlugin started")

    mplugin = om.MFnPlugin(mobject, "Robonobo", "1.0", "Any")
    _log("MFnPlugin created")

    try:
        _log("Registering node...")
        mplugin.registerNode(
            BOXY_SHAPE_NAME,
            BOXY_SHAPE_ID,
            BoxyShape.creator,
            BoxyShape.initialize,
            om.MPxNode.kSurfaceShape,
            BOXY_SHAPE_CLASSIFICATION
        )
        _log("Node registered successfully")
    except Exception as e:
        _log(f"Failed to register node: {e}")
        om.MGlobal.displayError(f"Failed to register node: {e}")
        raise

    try:
        _log("Registering draw override...")
        omr.MDrawRegistry.registerDrawOverrideCreator(
            BOXY_SHAPE_CLASSIFICATION,
            BOXY_DRAW_OVERRIDE_NAME,
            BoxyDrawOverride.creator
        )
        _log("Draw override registered successfully")
    except Exception as e:
        _log(f"Failed to register draw override: {e}")
        om.MGlobal.displayError(f"Failed to register draw override: {e}")
        raise

    try:
        _log("Registering command...")
        _log(f"  Command name: {BOXY_COMMAND_NAME}")
        _log(f"  Creator function: {BoxyCommand.creator}")
        _log(f"  Syntax function: {BoxyCommand.createSyntax}")
        mplugin.registerCommand(BOXY_COMMAND_NAME, BoxyCommand.creator, BoxyCommand.createSyntax)
        _log("Command registered successfully")
    except Exception as e:
        _log(f"Failed to register command: {e}")
        om.MGlobal.displayError(f"Failed to register command: {e}")
        raise

    _log("initializePlugin completed successfully")
    om.MGlobal.displayInfo("Boxy plugin loaded. Use: cmds.boxy()")


def uninitializePlugin(mobject):
    """Unregister all plugin components."""
    mplugin = om.MFnPlugin(mobject)

    try:
        mplugin.deregisterCommand(BOXY_COMMAND_NAME)
    except:
        pass

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


def build(boxy_data, name: str = "boxy") -> str:
    """
    Build a custom boxy node from BoxyData.

    Args:
        boxy_data: BoxyData instance with size, translation, rotation, pivot_side, color
        name: Name for the created node (default: "boxy")

    Returns:
        str: The name of the created transform node
    """
    import maya.cmds as cmds
    import logging
    from core.core_enums import Side
    from core.logging_utils import get_logger

    LOGGER = get_logger(__name__, level=logging.INFO)
    LOGGER.debug(f"=== boxy_node.build() ===")
    LOGGER.debug(f"  name: {name}")
    LOGGER.debug(f"  boxy_data.pivot_side: {boxy_data.pivot_side}")
    LOGGER.debug(f"  boxy_data.size: {boxy_data.size}")
    LOGGER.debug(f"  boxy_data.translation: {boxy_data.translation}")
    LOGGER.debug(f"  boxy_data.rotation: {boxy_data.rotation}")
    LOGGER.debug(f"  boxy_data.scale: {boxy_data.scale}")

    _ensure_plugin_loaded()

    # Create the shape node
    shape = cmds.createNode('boxyShape', name=f'{name}Shape')
    transform = cmds.listRelatives(shape, parent=True)[0]
    transform = cmds.rename(transform, name)

    # Get the updated shape name after transform rename (Maya renames shape too)
    shape = cmds.listRelatives(transform, shapes=True)[0]

    # Set size
    cmds.setAttr(f'{shape}.sizeX', boxy_data.size.x)
    cmds.setAttr(f'{shape}.sizeY', boxy_data.size.y)
    cmds.setAttr(f'{shape}.sizeZ', boxy_data.size.z)

    # Set pivot
    pivot_map = {
        Side.bottom: 0, Side.center: 1, Side.top: 2,
        Side.left: 3, Side.right: 4, Side.front: 5, Side.back: 6
    }
    pivot_value = pivot_map.get(boxy_data.pivot_side, 1)
    cmds.setAttr(f'{shape}.previousPivot', pivot_value)
    cmds.setAttr(f'{shape}.pivot', pivot_value)

    # Set wireframe color (normalize 0-255 to 0-1)
    r, g, b = boxy_data.color.normalized
    cmds.setAttr(f'{shape}.wireframeColorR', r)
    cmds.setAttr(f'{shape}.wireframeColorG', g)
    cmds.setAttr(f'{shape}.wireframeColorB', b)

    # Set translation (where the pivot is placed)
    LOGGER.debug(f"  Setting transform position to: {boxy_data.translation}")
    cmds.setAttr(f'{transform}.translateX', boxy_data.translation.x)
    cmds.setAttr(f'{transform}.translateY', boxy_data.translation.y)
    cmds.setAttr(f'{transform}.translateZ', boxy_data.translation.z)

    # Set rotation
    cmds.setAttr(f'{transform}.rotateX', boxy_data.rotation.x)
    cmds.setAttr(f'{transform}.rotateY', boxy_data.rotation.y)
    cmds.setAttr(f'{transform}.rotateZ', boxy_data.rotation.z)

    # Set scale if non-identity
    if boxy_data.scale and (boxy_data.scale.x != 1.0 or
                            boxy_data.scale.y != 1.0 or
                            boxy_data.scale.z != 1.0):
        LOGGER.debug(f"  Setting transform scale to: {boxy_data.scale}")
        cmds.setAttr(f'{transform}.scaleX', boxy_data.scale.x)
        cmds.setAttr(f'{transform}.scaleY', boxy_data.scale.y)
        cmds.setAttr(f'{transform}.scaleZ', boxy_data.scale.z)

    # Enable selection handle
    cmds.toggle(transform, selectHandle=True)

    # Select the transform
    cmds.select(transform)

    LOGGER.debug(f"=== end boxy_node.build() ===")
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
        # Get the updated shape name after transform rename
        shape = cmds.listRelatives(transform, shapes=True)[0]

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
