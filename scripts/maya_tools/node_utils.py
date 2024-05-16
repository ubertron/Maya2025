from maya import cmds

from core.core_enums import ComponentType, Attr, DataType, ObjectType


class State:
    def __init__(self):
        """
        Query and restore selection/component mode
        """
        self.component_mode = get_component_mode()
        self.selection = cmds.ls(sl=True)
        if self.object_mode:
            self.object_selection = cmds.ls(sl=True)
            self.component_selection = []
        else:
            self.component_selection = cmds.ls(sl=True)
            set_component_mode(ComponentType.object)
            self.object_selection = cmds.ls(sl=True)
            set_component_mode(self.component_mode)
            cmds.hilite(self.object_selection)

    def restore(self):
        if self.object_selection:
            cmds.select(self.object_selection, noExpand=True)
            set_component_mode(self.component_mode)
        else:
            set_component_mode(ComponentType.object)
            cmds.select(clear=True)
        if not self.object_mode:
            cmds.select(self.component_selection)

    @property
    def object_mode(self):
        return self.component_mode == ComponentType.object

    def remove_objects(self, objects):
        # Sometimes necessary as cmds.objExists check causes an exception
        for item in [objects]:
            if item in self.object_selection:
                self.object_selection.remove(item)


def get_component_mode():
    """
    Query the component mode
    @return:
    """
    if cmds.selectMode(query=True, object=True):
        return ComponentType.object
    elif cmds.selectType(query=True, vertex=True):
        return ComponentType.vertex
    elif cmds.selectType(query=True, edge=True):
        return ComponentType.edge
    elif cmds.selectType(query=True, facet=True):
        return ComponentType.face
    elif cmds.selectType(query=True, polymeshUV=True):
        return ComponentType.uv
    else:
        return 'unknown'


def set_component_mode(component_type=ComponentType.object):
    """
    Set component mode
    @param component_type:
    """
    if component_type == ComponentType.object:
        cmds.selectMode(object=True)
    else:
        cmds.selectMode(component=True)
        if component_type == ComponentType.vertex:
            cmds.selectType(vertex=True)
        elif component_type == ComponentType.edge:
            cmds.selectType(edge=True)
        elif component_type == ComponentType.face:
            cmds.selectType(facet=True)
        elif component_type == ComponentType.uv:
            cmds.selectType(polymeshUV=True)
        else:
            cmds.warning('Unknown component type')


def select_components(transform, components, component_type=ComponentType.face, hilite=True):
    """
    Select geometry components
    @param transform:
    @param components:
    @param component_type:
    @param hilite:
    """
    state = State()

    if component_type == ComponentType.vertex:
        cmds.select(transform.vtx[components])
    elif component_type == ComponentType.edge:
        cmds.select(transform.e[components])
    elif component_type == ComponentType.face:
        cmds.select(transform.f[components])
    elif component_type == ComponentType.uv:
        cmds.select(transform.map[components])
    else:
        cmds.warning('Component type not supported')

    if hilite:
        cmds.hilite(transform)
    else:
        state.restore()


def delete_history(nodes=None):
    """
    Delete construction history
    @param nodes:
    """
    state = State()
    set_component_mode(ComponentType.object)
    cmds.delete(cmds.ls(nodes, tr=True) if nodes else cmds.ls(sl=True, tr=True), constructionHistory=True)
    state.restore()


def freeze_transformations(nodes=None):
    """
    Freeze transformations on supplied nodes
    @param nodes:
    """
    for node in [nodes] if nodes else cmds.ls(sl=True, tr=True):
        cmds.makeIdentity(node, apply=True, translate=True, rotate=True, scale=True)


def reset_pivot(nodes=None):
    """
    Fix transformations on the pivot so that it is relative to the origin
    @param nodes:
    """
    for item in cmds.ls(nodes, tr=True) if nodes else cmds.ls(sl=True, tr=True):
        pivot_node = cmds.xform(item, query=True, worldSpace=True, rotatePivot=True)
        cmds.xform(item, relative=True, translation=[-i for i in pivot_node])
        cmds.makeIdentity(item, apply=True, translate=True)
        cmds.xform(item, translation=pivot_node)


def super_reset(nodes=None):
    """
    Reset transformations, reset pivot and delete construction history
    @param nodes:
    """
    nodes = cmds.ls(nodes, tr=True) if nodes else cmds.ls(sl=True, tr=True)
    freeze_transformations(nodes)
    reset_pivot(nodes)
    delete_history(nodes)


def pivot_to_base(transform=None, reset=True):
    """
    Send pivot to the base of the object
    @param transform:
    @param reset:
    """
    for item in [transform] if transform else cmds.ls(sl=True, tr=True):
        bounding_box = cmds.exactWorldBoundingBox(item)  # [x_min, y_min, z_min, x_max, y_max, z_max]
        base = [(bounding_box[0] + bounding_box[3]) / 2, bounding_box[1], (bounding_box[2] + bounding_box[5]) / 2]
        cmds.xform(item, piv=base, ws=True)

    if reset:
        reset_pivot(transform)


def pivot_to_center(transform=None, reset=True):
    """
    Send pivot to the center of the object
    @param transform:
    @param reset:
    """
    for item in [transform] if transform else cmds.ls(sl=True, tr=True):
        cmds.xform(item, centerPivotsOnComponents=True)

    if reset:
        reset_pivot(transform)


def pivot_to_origin(transform=None, reset=True):
    """
    Send pivot to the origin
    @param transform:
    @param reset:
    """
    for item in [transform] if transform else cmds.ls(sl=True, tr=True):
        cmds.xform(item, piv=[0, 0, 0], ws=True)

    if reset:
        reset_pivot(transform)


def move_to_origin(transform=None):
    """
    Move objects to the origin
    @param transform:
    """
    for item in [transform] if transform else cmds.ls(sl=True, tr=True):
        cmds.setAttr(f'{item}{Attr.translate.value}', 0, 0, 0, type=DataType.float3.name)


def get_selected_transforms():
    state = State()
    set_component_mode(ComponentType.object)
    selection = cmds.ls(sl=True, tr=True)
    state.restore()
    return selection


def get_transforms(nodes=None):
    state = State()
    set_component_mode(ComponentType.object)
    selection = cmds.ls(nodes, tr=True) if nodes else cmds.ls(sl=True, tr=True)
    state.restore()
    return selection


def get_shape_from_transform(transform, full_path=False):
    """
    Gets the shape node if any from a transform
    :param transform:
    :param full_path:
    :return:
    """
    if cmds.nodeType(transform) == 'transform':
        shape_list = cmds.listRelatives(transform, f=full_path, shapes=True)
        return shape_list[0] if shape_list else None
    else:
        return None


def get_transform_from_shape(node, full_path=False):
    """
    Gets the transform node from a shape
    :param node:
    :param full_path:
    :return:
    """
    return node if cmds.nodeType(node) == 'transform' else cmds.listRelatives(node, fullPath=full_path, parent=True)[0]


def is_node_type(obj, object_type: ObjectType):
    shape = get_shapes_from_transform(obj)
    return cmds.objectType(shape) == object_type.name


def move_to_last():
    """
    Move selected objects to the location of the last selected object
    """
    transforms = cmds.ls(sl=True, tr=True)
    assert len(transforms) > 1, "Select more than one node."
    location = cmds.getAttr(f'{transforms[-1]}.translate')[0]

    for i in range(len(transforms) - 1):
        cmds.setAttr(f'{transforms[i]}.translate', *location, type='float3')
