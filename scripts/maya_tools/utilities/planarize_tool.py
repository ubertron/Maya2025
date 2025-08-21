from widgets.generic_widget import GenericWidget
from widgets.radio_button_widget import RadioButtonWidget
from core.core_enums import Alignment, Axis, ComponentType, Position
from core.environment_utils import is_using_maya_python
from core.point_classes import Point3Pair

if is_using_maya_python():
    from maya import cmds

    from maya_tools.component_utils import planarize_vertices, planarize_selected_vertices, \
        get_selected_transform_and_vertices
    from maya_tools.node_utils import get_component_mode, get_selected_transforms
    from maya_tools.geometry_utils import get_component_list, get_component_indices
    from maya_tools.helpers import get_bounds, get_midpoint_from_transform


class PlanarizeTool(GenericWidget):
    title = 'Planarize Tool'
    axis_labels = ('X-Axis', 'Y-Axis', 'Z-Axis', 'Average')

    def __init__(self):
        super(PlanarizeTool, self).__init__(title=self.title)
        self.axis_widget: RadioButtonWidget = self.add_widget(
            RadioButtonWidget(title='Plane Axis', button_text_list=self.axis_labels, active_id=1))
        self.position_widget: RadioButtonWidget = self.add_widget(
            RadioButtonWidget(title='Plane Position', button_text_list=Position.values(), active_id=1))
        self.planarize_button = self.add_button('Planarize', clicked=self.planarize_button_clicked)
        self._init_signals()

    def _init_signals(self):
        """
        Initialize the signals
        """
        self.axis_widget.clicked.connect(self.axis_widget_clicked)

    def axis_widget_clicked(self, arg):
        """
        Event for axis widget
        :param arg:
        """
        self.position_widget.setDisabled(arg == 3)

    @property
    def current_axis(self) -> Axis or None:
        return {0: Axis.x, 1: Axis.y, 2: Axis.z, 3: None}[self.current_axis_id]

    @property
    def current_axis_id(self) -> int:
        return self.axis_widget.current_button_id

    @property
    def current_position(self) -> Position:
        return Position.get_by_value(self.position_widget.current_text)

    @property
    def component_mode(self) -> ComponentType:
        return get_component_mode()

    @property
    def info(self):
        if self.current_axis:
            return f'Axis: {self.current_axis}\nPosition: {self.current_position}' \
               f'\nComponent mode: {self.component_mode}'
        else:
            return f'Axis: average\nComponent mode: {self.component_mode}'

    def planarize_button_clicked(self):
        """
        Event for planarize button
        :return:
        """
        if self.component_mode == ComponentType.object:
            transforms = get_selected_transforms()

            if not len(transforms):
                cmds.warning('No geometry selected')
                return

            for transform in transforms:
                num_vertices = cmds.polyEvaluate(transform, vertex=True)
                planarize_vertices(transform=transform, vertices=list(range(num_vertices)), axis=self.current_axis,
                                   position=self.current_position)
        elif self.component_mode is ComponentType.element:
            cmds.warning('Invalid component type')
        else:
            transform = get_selected_transforms(first_only=True)
            components = cmds.ls(sl=True)

            if transform and components:
                if self.component_mode == ComponentType.vertex:
                    vertex_components = components
                elif self.component_mode == ComponentType.edge:
                    vertex_components = cmds.polyListComponentConversion(components, fromEdge=True, toVertex=True)
                elif self.component_mode == ComponentType.face:
                    vertex_components = cmds.polyListComponentConversion(components, fromFace=True, toVertex=True)
                elif self.component_mode == ComponentType.uv:
                    vertex_components = cmds.polyListComponentConversion(components, fromUV=True, toVertex=True)
                else:
                    return

                vertices = get_component_indices(component_list=vertex_components, component_type=ComponentType.vertex)
                planarize_vertices(transform=transform, vertices=vertices, axis=self.current_axis,
                                   position=self.current_position)
                cmds.select(components)
            else:
                cmds.warning('Nothing selected')


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication()
    planarize_tool = PlanarizeTool()
    planarize_tool.show()
    app.exec()
