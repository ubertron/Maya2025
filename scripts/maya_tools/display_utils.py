import logging

from dataclasses import dataclass
from enum import auto

from maya import cmds, mel

from core.core_enums import Unit
from maya_tools.maya_enums import DisplayElement, ColorIndex


DEFAULT_DISPLAY_GRID_SIZE = 200
DEFAULT_DISPLAY_GRID_SPACING = 100
DEFAULT_DISPLAY_GRID_DIVISIONS = 8


@dataclass
class DisplayGridSettings:
    units: Unit
    size: int
    spacing: int
    divisions: int
    axis: ColorIndex
    line: ColorIndex
    subdivisions: ColorIndex

    def __repr__(self) -> str:
        return (
            f"units: {self.units}\n"
            f"size: {self.size}\n"
            f"spacing: {self.spacing}\n"
            f"divisions: {self.divisions}\n"
            f"axis: {self.axis}\n"
            f"line: {self.line}\n"
            f"subdivisions: {self.subdivisions}\n"
        )


DISPLAY_GRID_BLUE = DisplayGridSettings(
    units = Unit.centimeter,
    size = DEFAULT_DISPLAY_GRID_SIZE,
    spacing = DEFAULT_DISPLAY_GRID_SPACING,
    divisions = DEFAULT_DISPLAY_GRID_DIVISIONS,
    axis = ColorIndex.black,
    line = ColorIndex.blue,
    subdivisions = ColorIndex.cyan
)

DISPLAY_GRID_GREEN = DisplayGridSettings(
    units = Unit.centimeter,
    size = DEFAULT_DISPLAY_GRID_SIZE,
    spacing = DEFAULT_DISPLAY_GRID_SPACING,
    divisions = DEFAULT_DISPLAY_GRID_DIVISIONS,
    axis = ColorIndex.black,
    line = ColorIndex.dark_green,
    subdivisions = ColorIndex.green
)

DISPLAY_GRID_GREY = DisplayGridSettings(
    units = Unit.centimeter,
    size = DEFAULT_DISPLAY_GRID_SIZE,
    spacing = DEFAULT_DISPLAY_GRID_SPACING,
    divisions = DEFAULT_DISPLAY_GRID_DIVISIONS,
    axis = ColorIndex.black,
    line = ColorIndex.black,
    subdivisions = ColorIndex.light_grey
)

DISPLAY_GRID_RED = DisplayGridSettings(
    units = Unit.centimeter,
    size = DEFAULT_DISPLAY_GRID_SIZE,
    spacing = DEFAULT_DISPLAY_GRID_SPACING,
    divisions = DEFAULT_DISPLAY_GRID_DIVISIONS,
    axis = ColorIndex.black,
    line = ColorIndex.maroon,
    subdivisions = ColorIndex.red
)


def get_display_color(element: DisplayElement) -> ColorIndex:
    """Get the value of a """
    index = cmds.displayColor(element.value, query=True, dormant=True)
    return ColorIndex(index)


def get_display_grid_settings() -> DisplayGridSettings:
    """Get the settings of the display grid."""
    units: Unit = get_units()
    size = cmds.grid(query=True, size=True)
    spacing = cmds.grid(query=True, spacing=True)
    divisions = cmds.grid(query=True, divisions=True)
    axis = get_display_color(element=DisplayElement.axis)
    line = get_display_color(element=DisplayElement.line)
    subdivisions = get_display_color(element=DisplayElement.subdivisions)
    return DisplayGridSettings(
        units = units,
        size = size,
        spacing = spacing,
        divisions = divisions,
        axis = axis,
        line = line,
        subdivisions = subdivisions
    )


def get_units() -> Unit:
    result = cmds.currentUnit(query=True, linear=True)
    return Unit[result] if result in Unit.__dict__ else Unit(result)


def in_view_message(text: str, persist_time: int = 2000):
    """
    Display a message across the viewport
    :param text:
    :param persist_time:
    """
    cmds.inViewMessage(assistMessage=text, fade=True, pos='midCenter', fadeStayTime=persist_time)


def warning_message(text: str, persist_time: int = 2000):
    """
    Display a warning message in-view and in the log
    :param text:
    :param persist_time:
    """
    in_view_message(text=text, persist_time=persist_time)
    cmds.warning(text)


def info_message(text: str, persist_time: int = 2000):
    """
    Display an info message in-view and in the log
    :param text:
    :param persist_time:
    """
    in_view_message(text=text, persist_time=persist_time)
    logging.info(text)


def set_display_color(element: DisplayElement, color_index: ColorIndex):
    """Set the color of a display element."""
    cmds.displayColor(element.value, color_index.value, dormant=True)


def set_display_grid(settings: DisplayGridSettings):
    """Set up the display grid."""
    set_units(unit=settings.units)
    cmds.grid(size=settings.size, spacing=settings.spacing, divisions=settings.divisions)
    set_display_color(element=DisplayElement.axis, color_index=settings.axis)
    set_display_color(element=DisplayElement.line, color_index=settings.line)
    set_display_color(element=DisplayElement.subdivisions, color_index=settings.subdivisions)


def set_units(unit: Unit):
    """Set the units."""
    cmds.currentUnit(linear=unit.name)


def toggle_camera_visibility():
    """Toggle cameras in current viewport."""
    current_panel = cmds.getPanel(withFocus=True)
    if current_panel in cmds.getPanel(type='modelPanel'):
        visible = cmds.modelEditor(current_panel, query=True, cameras=True)
        cmds.modelEditor(current_panel, edit=True, cameras=not visible)
        info_message(f"Camera visibility switched to {not visible}")
    else:
        cmds.warning("No active model panel found.")


def toggle_shade_selected(warning=False):
    """Toggle between shade selected and shade all."""
    current_panel = cmds.getPanel(withFocus=True)
    if current_panel in cmds.getPanel(type='modelPanel'):
        state = str(not (cmds.modelEditor(current_panel, query=True, activeOnly=True))).lower()
        mel.eval(f'modelEditor -e -displayAppearance smoothShaded -activeOnly {state} {current_panel}')
    elif warning:
        cmds.warning('Not a model panel')


def toggle_transform_constraints():
    """
    Toggle the transform constraint mode
    """
    mode = cmds.xformConstraint(query=True, type=True)
    new_mode = 'edge' if mode == 'none' else 'none'
    cmds.xformConstraint(type=new_mode)
    in_view_message(text=f'Tranform constraint set to {new_mode}')
            
    
if __name__ == '__main__':
    toggle_transform_constraint()
