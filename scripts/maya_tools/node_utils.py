import pymel.core as pm

from maya_tools.maya_enums import ComponentType


class State:
    def __init__(self):
        """
        Query and restore selection/component mode
        """
        self.component_mode = get_component_mode()
        self.selection = pm.ls(sl=True)
        if self.object_mode:
            self.object_selection = pm.ls(sl=True)
            self.component_selection = []
        else:
            self.component_selection = pm.ls(sl=True)
            set_component_mode(ComponentType.object)
            self.object_selection = pm.ls(sl=True)
            set_component_mode(self.component_mode)
            pm.hilite(self.object_selection)

    def restore(self):
        if self.object_selection:
            pm.select(self.object_selection, noExpand=True)
            set_component_mode(self.component_mode)
        else:
            set_component_mode(ComponentType.object)
            pm.select(clear=True)
        if not self.object_mode:
            pm.select(self.component_selection)

    @property
    def object_mode(self):
        return self.component_mode == ComponentType.object

    def remove_objects(self, objects):
        # Sometimes necessary as pm.objExists check causes an exception
        for item in list(objects):
            if item in self.object_selection:
                self.object_selection.remove(item)


def get_component_mode():
    """
    Query the component mode
    @return:
    """
    if pm.selectMode(query=True, object=True):
        return ComponentType.object
    elif pm.selectType(query=True, vertex=True):
        return ComponentType.vertex
    elif pm.selectType(query=True, edge=True):
        return ComponentType.edge
    elif pm.selectType(query=True, facet=True):
        return ComponentType.face
    elif pm.selectType(query=True, polymeshUV=True):
        return ComponentType.uv
    else:
        return 'unknown'


def set_component_mode(component_type=ComponentType.object):
    """
    Set component mode
    @param component_type:
    """
    if component_type == ComponentType.object:
        pm.selectMode(object=True)
    else:
        pm.selectMode(component=True)
        if component_type == ComponentType.vertex:
            pm.selectType(vertex=True)
        elif component_type == ComponentType.edge:
            pm.selectType(edge=True)
        elif component_type == ComponentType.face:
            pm.selectType(facet=True)
        elif component_type == ComponentType.uv:
            pm.selectType(polymeshUV=True)
        else:
            pm.warning('Unknown component type')


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
        pm.select(transform.vtx[components])
    elif component_type == ComponentType.edge:
        pm.select(transform.e[components])
    elif component_type == ComponentType.face:
        pm.select(transform.f[components])
    elif component_type == ComponentType.uv:
        pm.select(transform.map[components])
    else:
        pm.warning('Component type not supported')

    if hilite:
        pm.hilite(transform)
    else:
        state.restore()


def delete_history(nodes=None):
    """
    Delete construction history
    @param nodes:
    """
    state = State()
    set_component_mode(ComponentType.object)
    pm.delete(pm.ls(nodes, tr=True) if nodes else pm.ls(sl=True, tr=True), constructionHistory=True)
    state.restore()


def freeze_transformations(nodes=None):
    """
    Freeze transformations on supplied nodes
    @param nodes:
    """
    for node in list(nodes) if nodes else pm.ls(sl=True, tr=True):
        pm.makeIdentity(node, apply=True, translate=True, rotate=True, scale=True)


def reset_pivot(nodes=None):
    """
    Fix transformations on the pivot so that it is relative to the origin
    @param nodes:
    """
    for item in pm.ls(nodes, tr=True) if nodes else pm.ls(sl=True, tr=True):
        pivot_node = pm.xform(item, query=True, worldSpace=True, rotatePivot=True)
        pm.xform(item, relative=True, translation=[-i for i in pivot_node])
        pm.makeIdentity(item, apply=True, translate=True)
        pm.xform(item, translation=pivot_node)


def super_reset(nodes=None):
    """
    Reset transformations, reset pivot and delete construction history
    @param nodes:
    """
    nodes = pm.ls(nodes, tr=True) if nodes else pm.ls(sl=True, tr=True)
    freeze_transformations(nodes)
    reset_pivot(nodes)
    delete_history(nodes)


def pivot_to_base(pm_obj=None, reset=True):
    """
    Send pivot to the base of the object
    @param pm_obj:
    @param reset:
    """
    for item in list(pm_obj) if pm_obj else pm.ls(sl=True, tr=True):
        bounding_box = pm.exactWorldBoundingBox(item)  # [x_min, y_min, z_min, x_max, y_max, z_max]
        base = [(bounding_box[0] + bounding_box[3]) / 2, bounding_box[1], (bounding_box[2] + bounding_box[5]) / 2]
        pm.xform(item, piv=base, ws=True)

    if reset:
        reset_pivot(pm_obj)


def pivot_to_center(pm_obj=None, reset=True):
    """
    Send pivot to the center of the object
    @param pm_obj:
    @param reset:
    """
    for item in list(pm_obj) if pm_obj else pm.ls(sl=True, tr=True):
        pm.xform(item, centerPivotsOnComponents=True)

    if reset:
        reset_pivot(pm_obj)


def pivot_to_origin(pm_obj=None, reset=True):
    """
    Send pivot to the origin
    @param pm_obj:
    @param reset:
    """
    for item in list(pm_obj) if pm_obj else pm.ls(sl=True, tr=True):
        pm.xform(item, piv=[0, 0, 0], ws=True)

    if reset:
        reset_pivot(pm_obj)


def move_to_origin(pm_obj=None):
    """
    Move objects to the origin
    @param pm_obj:
    """
    for item in list(pm_obj) if pm_obj else pm.ls(sl=True, tr=True):
        pm.setAttr(item.translate, (0, 0, 0), type='float3')
