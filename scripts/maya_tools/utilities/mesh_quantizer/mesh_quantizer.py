"""Mesh Quantizer."""
from __future__ import annotations

import random

from maya import cmds
import maya.api.OpenMaya as om

from maya_tools import node_utils
from maya_tools.geometry import geometry_utils


def create_test_mesh(name: str = "test_mesh", size: float = 10.0,
                     divisions: int = 6, factor: float = .1) -> str:
    """Create a test mesh."""
    if cmds.objExists(name):
        cmds.delete(name)
    test_mesh, _ = cmds.polyPlane(
        name=name, width=size, height=size,
        sx=divisions, sy=divisions,
        axis=(0, 1, 0))
    jiggle = size / divisions * factor
    jiggle_vertices(node=test_mesh, distance=jiggle)
    return test_mesh


def jiggle_vertices(node: str, distance: float = 0.1) -> None:
    """Jiggle the vertices on a selected mesh."""
    if node_utils.is_geometry(node=node):
        vertex_iterator: om.MItMeshVertex = geometry_utils.get_vertex_iterator(node=node)
        while not vertex_iterator.isDone():
            position = vertex_iterator.position(om.MSpace.kWorld)
            for i in range(3):
                delta = random.uniform(0, distance) - distance / 2
                position[i] = position[i] + delta
            vertex_iterator.setPosition(position, om.MSpace.kObject)
            next(vertex_iterator)
    else:
        cmds.warning(f"Invalid object: {node}")


def quantize_vertices(node: str, increment: float = 0.25):
    """Quantize vertices in a mesh according to a set size."""
    if node_utils.is_geometry(node=node):
        vertex_iterator: om.MItMeshVertex = geometry_utils.get_vertex_iterator(node=node)
        cmds.makeIdentity(node, apply=True, translate=True)
        node_utils.freeze_translation(node=node)
        while not vertex_iterator.isDone():
            position = vertex_iterator.position(om.MSpace.kWorld)
            for i in range(3):
                position[i] = round(position[i] / increment) * increment
            vertex_iterator.setPosition(position, om.MSpace.kObject)
            next(vertex_iterator)
        node_utils.reset_pivot(node)


if __name__ == "__main__":
    my_mesh = create_test_mesh(size=10, divisions=10)
    quantize_vertices(node=my_mesh, increment=.1)
    get_vertex_positions(node=my_mesh, verbose=True)