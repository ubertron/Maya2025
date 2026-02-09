from __future__ import annotations

from maya import cmds

from pathlib import Path
from typing import Optional, Sequence

from ams import ams_project
from core import image_utils
from core.color_classes import ColorRGB
from maya_tools.maya_enums import ObjectType
from maya_tools import node_utils, uv_utils

DEFAULT_LAMBERT_SHADER = "lambert1"
FILE_TEXTURE_NODES: list[str] = cmds.ls(type=ObjectType.file.name)
LAMBERT_SHADER_NODES: list[str] = cmds.ls(type=ObjectType.lambert.name)


def apply_checker_shader(transform: str | None = None):
    """Apply checker shader to current selection."""
    selection = transform if transform else cmds.ls(selection=True)
    checker_shader = next((x for x in cmds.ls("checkerShader") if cmds.objectType(x) == ObjectType.lambert.name), None)
    if checker_shader:
        shading_group = get_shading_group_from_shader(shader=checker_shader)
    else:
        _, shading_group = create_checker_shader(
            divisions=4, color1=ColorRGB(64, 64, 64), color2=ColorRGB(128, 128, 128))
    apply_shader(shading_group=shading_group, transforms=selection)


def apply_default_lambert_shader(transform: str | None = None):
    """Apply default shader to current selection."""
    selection = transform if transform else cmds.ls(selection=True)
    shading_group = get_shading_group_from_shader(shader=DEFAULT_LAMBERT_SHADER)
    apply_shader(shading_group=shading_group, transforms=selection)


def apply_shader(shading_group: str, transforms: Optional[str] = None):
    """
    Apply a shader to a collection of Transforms
    @param shading_group:
    @param transforms:
    """
    target = cmds.ls(transforms) if transforms else cmds.ls(sl=True)
    cmds.sets(target, edit=True, forceElement=shading_group)


def auto_texture(transform: str | None = None):
    """Apply a checker shader and box map."""
    state = node_utils.State()
    selection = transform if transform else cmds.ls(selection=True)
    uv_utils.box_map(transform=transform, size=100)
    apply_checker_shader(transform=selection)
    state.restore()


def collect_textures():
    """Gets all the textures in a scene linked to geometry."""
    textures = []
    for node in FILE_TEXTURE_NODES:
        shading_group = get_shading_group_from_file_node(file_node=node)
        if shading_group:
            if is_shading_group_applied(shading_group=shading_group):
                texture = get_texture_from_file_node(file_node=node)
                if texture and texture.exists():
                    textures.append(texture)
    return textures


def create_file_texture_node(texture_path: Path, name: Optional[str] = None, check_existing: bool = True):
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
    placement_node = create_placement_node(name=name)
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


def create_checker_shader(
        divisions: int  = 4,
        color1: ColorRGB = ColorRGB(64, 64, 64),
        color2: ColorRGB = ColorRGB(128, 128, 128)) -> tuple:
    """Create a checker shader."""
    name = "checker"
    lambert_shader, shading_group = create_lambert_shader(name)
    checker_node = cmds.shadingNode("checker", asTexture=True, name="checker_node")
    placement_node = create_placement_node(name=name)
    cmds.connectAttr(f'{placement_node}.outUV', f'{checker_node}.uvCoord', force=True)
    cmds.connectAttr(f'{placement_node}.outUvFilterSize', f'{checker_node}.uvFilterSize', force=True)
    cmds.connectAttr(f'{checker_node}.outColor', f'{lambert_shader}.color')
    cmds.setAttr(f'{checker_node}.color1', *color1.normalized, type='double3')
    cmds.setAttr(f'{checker_node}.color2', *color2.normalized, type='double3')
    cmds.setAttr(f"{placement_node}.repeatU", divisions)
    cmds.setAttr(f"{placement_node}.repeatV", divisions)
    return lambert_shader, shading_group


def create_lambert_shader(name: str, color: Optional[Sequence[float]] = None) -> tuple[str, str]:
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


def create_lambert_file_texture_shader(texture_path: Path, name=None, check_existing: bool = True) -> tuple:
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
    output_shader, shading_group = create_lambert_shader(name)
    file_node = create_file_texture_node(texture_path, name)
    cmds.connectAttr(f'{file_node}.outColor', f'{output_shader}.color')
    return output_shader, shading_group


def create_placement_node(name: str) -> str:
    """Create a placement node."""
    return cmds.shadingNode(ObjectType.place2dTexture.name, asUtility=True, name=f'{name}Place2dTexture')


def is_shading_group_applied(shading_group: str) -> bool:
    """Query to find out if a shading group is applied to geometry."""
    return next((True for x in cmds.listConnections(shading_group) if node_utils.is_geometry(x)), False)


def get_shading_group_from_file_node(file_node: str) -> str | None:
    """Get the shading group from a file node."""
    shader_types = ("lambert", "phong", "blinn", "openPBRSurface")
    shader = next((x for x in cmds.listConnections(file_node) if cmds.objectType(x) in shader_types), None)
    if shader:
        return get_shading_group_from_shader(shader=shader)
    return None


def get_shading_group_from_shader(shader) -> str | None:
    """
    Get the shading group for a shader
    @param shader:
    @return:
    """
    shadingGroups = cmds.listConnections(shader, type=ObjectType.shadingEngine.name)
    return shadingGroups[0] if shadingGroups else None


def get_texture_from_file_node(file_node: str) -> Path | None:
    """Get a texture from a file node."""
    result = cmds.getAttr(f"{file_node}.fileTextureName")
    return Path(result) if result else None


def set_diffuse_color(shader, color: tuple[float]):
    """
    Set the diffuse value of a shader
    @param shader:
    @param color:
    """
    for idx, value in enumerate(['.colorR', '.colorG', '.colorB']):
        cmds.setAttr(f'{shader}{value}', color[idx])
