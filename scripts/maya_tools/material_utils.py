from __future__ import annotations

from maya import cmds

from pathlib import Path
from typing import Optional, Sequence

from maya_tools.maya_enums import ObjectType

FILE_TEXTURE_NODES: list[str] = cmds.ls(type=ObjectType.file.name)
LAMBERT_SHADER_NODES: list[str] = cmds.ls(type=ObjectType.lambert.name)


def apply_shader(shading_group, transforms: Optional[str] = None):
    """
    Apply a shader to a collection of Transforms
    @param shading_group:
    @param transforms:
    """
    target = cmds.ls(transforms) if transforms else cmds.ls(sl=True)
    cmds.sets(target, edit=True, forceElement=shading_group)


def get_shading_group_from_shader(shader):
    """
    Get the shading group for a shader
    @param shader:
    @return:
    """
    shadingGroups = cmds.listConnections(shader, type=ObjectType.shadingEngine.name)
    if shadingGroups:
        return shadingGroups[0]


def get_texture_from_file_node(file_node: str) -> Path | None:
    """Get a texture from a file node."""
    result = cmds.getAttr(f"{file_node}.fileTextureName")
    return result if result else None


def lambert_shader(name: str, color: Optional[Sequence[float]] = None) -> tuple[str, str]:
    """
    Create a Lambert shader node
    @param name:
    @param color:
    @return:
    """
    shader = cmds.shadingNode(ObjectType.lambert.name, asShader=True, name=f'{name}Shader')
    shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=f'{name}SG')
    cmds.connectAttr(f'{shader}.outColor', f'{shading_group}.surfaceShader')

    if color:
        set_diffuse_color(shader=shader, color=color)

    return shader, shading_group


def lambert_file_texture_shader(texture_path: Path, name=None, check_existing: bool = True) -> tuple:
    """
    Create a Lambert shader with a file texture node
    @param texture_path:
    @param name:
    @param check_existing:
    @return:
    """
    assert texture_path.exists(), f'Path not found: {texture_path}'
    name = name if name else texture_path.stem
    shader_name = f'{name}Shader'
    if check_existing:
        output_shader = next((x for x in LAMBERT_SHADER_NODES if x == shader_name), None)

        if output_shader:
            return output_shader, get_shading_group_from_shader(output_shader)
    output_shader, shading_group = lambert_shader(name)
    file_node = file_texture_node(texture_path, name)
    cmds.connectAttr(f'{file_node}.outColor', f'{output_shader}.color')
    return output_shader, shading_group


def set_diffuse_color(shader, color: tuple[float]):
    """
    Set the diffuse value of a shader
    @param shader:
    @param color:
    """
    for idx, value in enumerate(['.colorR', '.colorG', '.colorB']):
        cmds.setAttr(f'{shader}{value}', color[idx])


def file_texture_node(texture_path: Path, name: Optional[str] = None, check_existing: bool = True):
    """
    create a file texture node with a texture placement node
    @param texture_path:
    @param name:
    @param check_existing:
    @return:
    """
    name = name if name else texture_path.stem
    file_node_name = f'{name}File'

    if check_existing:
        file_node = next((x for x in FILE_TEXTURE_NODES if x == file_node_name), None)
        
        if file_node:
            return file_node

    file_node = cmds.shadingNode(ObjectType.file.name, asTexture=True, name=file_node_name)
    placement_node = cmds.shadingNode(ObjectType.place2dTexture.name, asUtility=True, name=f'{name}Place2dTexture')
    cmds.setAttr(f'{file_node}.fileTextureName', texture_path, type='string')
    cmds.connectAttr(f'{placement_node}.outUV', f'{file_node}.uvCoord')
    cmds.connectAttr(f'{placement_node}.coverage', f'{file_node}.coverage')
    cmds.connectAttr(f'{placement_node}.mirrorU', f'{file_node}.mirrorU')
    cmds.connectAttr(f'{placement_node}.mirrorV', f'{file_node}.mirrorV')
    cmds.connectAttr(f'{placement_node}.noiseUV', f'{file_node}.noiseUV')
    cmds.connectAttr(f'{placement_node}.offset', f'{file_node}.offset')
    cmds.connectAttr(f'{placement_node}.outUvFilterSize', f'{file_node}.uvFilterSize')
    cmds.connectAttr(f'{placement_node}.repeatUV', f'{file_node}.repeatUV')
    cmds.connectAttr(f'{placement_node}.rotateFrame', f'{file_node}.rotateFrame')
    cmds.connectAttr(f'{placement_node}.rotateUV', f'{file_node}.rotateUV')
    cmds.connectAttr(f'{placement_node}.stagger', f'{file_node}.stagger')
    cmds.connectAttr(f'{placement_node}.translateFrame', f'{file_node}.translateFrame')
    cmds.connectAttr(f'{placement_node}.vertexCameraOne', f'{file_node}.vertexCameraOne')
    cmds.connectAttr(f'{placement_node}.vertexUvOne', f'{file_node}.vertexUvOne')
    cmds.connectAttr(f'{placement_node}.vertexUvTwo', f'{file_node}.vertexUvTwo')
    cmds.connectAttr(f'{placement_node}.vertexUvThree', f'{file_node}.vertexUvThree')
    cmds.connectAttr(f'{placement_node}.wrapU', f'{file_node}.wrapU')
    cmds.connectAttr(f'{placement_node}.wrapV', f'{file_node}.wrapV')
    return file_node
