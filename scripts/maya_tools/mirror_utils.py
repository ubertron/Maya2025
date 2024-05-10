import pymel.core as pm


from core_tools.enums import Axis


def mirror_geometry(nodes=None, axis=Axis.x, positive=False, merge_threshold=0.001, verbose=False):
    """
    Mirrors geometry along an axis
    :param nodes: Supply nodes
    :param axis: Specify geometric axis
    :param positive: Specify positive or negative axis
    :param merge_threshold: threshold along axis
    """
    selection = pm.ls(sl=True)
    nodes = pm.ls(nodes) if nodes else pm.ls(sl=True, tr=True)
    direction = {
        Axis.x: 0 + positive,
        Axis.y: 2 + positive,
        Axis.z: 4 + positive
    }

    for item in nodes:
        pm.select(item)
        pivot_position = [pm.xform(item, query=True, piv=True, ws=True)[i] for i in range(3)]
        slice_geometry(item, axis, not positive)
        pm.polyMirrorFace(item,  ws=True, d=direction[axis], mergeMode=1, p=pivot_position, mt=merge_threshold, mtt=1)

    if verbose:
        print('Mirrored: {}'.format(str(selection)))

    pm.select(selection)
    return selection


def slice_geometry(nodes=None, axis=Axis.x, positive=True):
    """
    Slices geometry along an axis
    :param nodes:
    :param axis: Specify geometric axis
    :param positive: Specify positive or negative axis
    """
    selection = pm.ls(sl=True)
    nodes = pm.ls(nodes) if nodes else pm.ls(sl=True, tr=True)
    angles = {
        Axis.x: [0, positive * 180 - 90, 0],
        Axis.y: [90 - positive * 180, 0, 0],
        Axis.z: [0, 180 - positive * 180, 0]
    }
    cut_axis = angles[axis]

    for item in nodes:
        pm.select(item)
        pivot_matrix = pm.xform(item, query=True, piv=True, ws=True)
        pivot_position = [pivot_matrix[0], pivot_matrix[1], pivot_matrix[2]]
        pm.polyCut(
            cutPlaneCenter=pivot_position,
            cutPlaneRotate=cut_axis,
            extractFaces=True,
            extractOffset=[0, 0, 0],
            deleteFaces=True
        )

    pm.select(selection)
