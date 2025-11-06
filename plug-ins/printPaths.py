# pyPrintPaths.py

import sys
import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass

kPluginCmdName = 'pyPrintPaths'

##########################################################
# Plug-in
##########################################################
class printPathsCmd(OpenMaya.MPxCommand):

    def __init__(self):
        ''' Constructor. '''
        OpenMaya.MPxCommand.__init__(self)

    def doIt(self, args):
        '''
        Print the DAG paths of the selected objects.
        If no DAG objects are selected, print the entire
        scene graph.
        '''

        # Populate the MSelectionList with the currently selected
        # objects using the static function MGlobal.getActiveSelectionList().

        #selectionList = OpenMaya.MSelectionList()
        selectionList = OpenMaya.MGlobal.getActiveSelectionList()

        # This selection list can contain more than just scene elements (DAG nodes),
        # so we must create an iterator over this selection list (MItSelectionList),
        # and filter for objects compatible with the MFnDagNode function set (MFn.kDagNode).
        iterator = OpenMaya.MItSelectionList( selectionList, OpenMaya.MFn.kDagNode )

        if iterator.isDone():
            # Print the whole scene if there are no DAG nodes selected.
            print('=====================')
            print(' SCENE GRAPH (DAG):  ')
            print('=====================')
            self.printScene()
        else:
            # Print the paths of the selected DAG objects.
            print('=======================')
            print(' SELECTED DAG OBJECTS: ')
            print('=======================')
            self.printSelectedDAGPaths( iterator )

    def printSelectedDAGPaths(self, pSelectionListIterator):
        ''' Print the DAG path(s) of the selected object(s). '''

        # Create an MDagPath object which will be populated on each iteration.
        dagPath = OpenMaya.MDagPath()

        # Obtain a reference to MFnDag function set to print the name of the DAG object
        dagFn = OpenMaya.MFnDagNode()



        # Perform each iteration.
        while( not pSelectionListIterator.isDone() ):

            # Populate our MDagPath object. This will likely provide
            # us with a Transform node.
            dagPath = pSelectionListIterator.getDagPath()
            try:
                # Attempt to extend the path to the shape node.
                dagPath.extendToShape()
            except Exception as e:
                # Do nothing if this operation fails.
                pass

            # Obtain the name of the object.
            dagObject = dagPath.node()
            dagFn.setObject( dagObject )
            name = dagFn.name()

            # Obtain the compatible function sets for this DAG object.
            # These values refer to the enumeration values of MFn
            fntypes = []
            fntypes = OpenMaya.MGlobal.getFunctionSetList( dagObject )

            # Print the DAG object information.
            print(name + ' (' + dagObject.apiTypeStr + ')')
            print('\tDAG path: [' + str( dagPath.fullPathName() ) + ']')
            print('\tCompatible function sets: ' + str( fntypes ))

            # Advance to the next item
            pSelectionListIterator.next()

        print('=====================')

    def printScene(self):
        ''' Traverse and print the elements in the scene graph (DAG)  '''

        # Create a function set which we will re-use throughout our scene graph traversal.
        dagNodeFn = OpenMaya.MFnDagNode()

        # Create an iterator to traverse the scene graph starting at the world node
        # (the scene's origin). We use a depth-first traversal, and we do not filter for
        # any scene elements, as indicated by the 'OpenMaya.MFn.kInvalid' parameter.
        dagIterator = OpenMaya.MItDag( OpenMaya.MItDag.kDepthFirst,
                                       OpenMaya.MFn.kInvalid )

        # Traverse the scene.
        while( not dagIterator.isDone() ):

            # Obtain the current item.
            dagObject = dagIterator.currentItem()
            depth = dagIterator.depth()

            # Make our MFnDagNode function set operate on the current DAG object.
            dagNodeFn.setObject( dagObject )

            # Extract the DAG object's name.
            name = dagNodeFn.name()

            # Generate our output by first incrementing the tabs based on the depth
            # of the current object. This formats our output nicely.
            output = ''
            for i in range( 0, depth ):
                output += '\t'

            output += name + ' (' + dagObject.apiTypeStr + ')'
            print(output)

            # Increment to the next item.
            dagIterator.next()

        print('=====================')




##########################################################
# Plug-in initialization.
##########################################################
def cmdCreator():
    ''' Creates an instance of our command class. '''
    return printPathsCmd()

def initializePlugin(mobject):
    ''' Initializes the plug-in.'''
    mplugin = OpenMaya.MFnPlugin( mobject )
    try:
        mplugin.registerCommand( kPluginCmdName, cmdCreator )
    except:
        sys.stderr.write( "Failed to register command: %s\n" % kPluginCmdName )

def uninitializePlugin(mobject):
    ''' Uninitializes the plug-in '''
    mplugin = OpenMaya.MFnPlugin( mobject )
    try:
        mplugin.deregisterCommand( kPluginCmdName )
    except:
        sys.stderr.write( "Failed to unregister command: %s\n" % kPluginCmdName )

##########################################################
# Sample usage.
##########################################################
'''
# Copy the following lines and run them in Maya's Python Script Editor:

import maya.cmds as cmds
from pathlib import Path

plugin_dir = Path.home().joinpath("Dropbox/Technology/Python3/Projects/Maya2025/plug-ins")
plugin_path = plugin_dir / "printPaths.py"
cmds.loadPlugin(plugin_path.as_posix())
cmds.pyPrintPaths()

'''