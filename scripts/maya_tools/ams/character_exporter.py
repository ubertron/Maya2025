import logging

from functools import partial
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from core.core_enums import Alignment, AssetType, ResourceType
from core.environment_utils import is_using_maya_python
from core.system_utils import open_file_location
from maya_tools.ams.ams_enums import ItemStatus
from maya_tools.ams.asset import Asset
from maya_tools.ams.project_definition import ProjectDefinition
from maya_tools.ams.resource import Resource
from maya_tools.ams.validation.test_result import TestResult
from maya_tools.ams.validation.asset_test import AssetTest
from maya_tools.maya_enums import LayerDisplayType
from widgets.clickable_label import ClickableLabel
from widgets.generic_widget import GenericWidget
from widgets.grid_widget import GridWidget
from widgets.panel_widget import PanelWidget
from widgets.scroll_widget import ScrollWidget


logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


class CharacterExporter(GenericWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super(CharacterExporter, self).__init__('Character Exporter')
        self.parent_widget: QWidget or None = parent
        self.button_bar: GenericWidget = self.add_widget(GenericWidget(alignment=Alignment.horizontal))
        self.button_bar.add_button('Refresh', tool_tip='Update status info', event=self.refresh_button_clicked)
        self.button_bar.add_button('Browse...', tool_tip='Open assets in a Finder window',
                                   event=self.browse_button_clicked)
        self.button_bar.add_stretch()
        self.button_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.scroll_widget: ScrollWidget = self.add_widget(ScrollWidget())
        self.label: QLabel = QLabel('Character data...')
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.info_panel: Panel_Widget = PanelWidget(title='Character Information', widget=self.label, active=False)
        self.characters = []

    def refresh(self):
        self.button_bar.setEnabled(self.project_root is not None)

    @property
    def project_root(self) -> Path:
        return self.parent_widget.project_root

    @property
    def project(self) -> ProjectDefinition:
        return self.parent_widget.project

    @property
    def characters_folder(self) -> Path or None:
        if self.project:
            return self.project.source_art_root.joinpath('Characters')

    @property
    def character_asset_folders(self) -> list[str]:
        result = [x.name for x in self.characters_folder.iterdir() if x.is_dir()] if self.characters_folder.exists() else []
        result.sort(key=lambda x: x.lower())
        return [x for x in result if not x.startswith('_')]

    def browse_button_clicked(self):
        """
        Event for Browse button
        """
        open_file_location(self.characters_folder)

    def refresh_button_clicked(self):
        """
        Event for refresh_button
        """
        panel_states = self.panel_states
        self.scroll_widget.clear_layout()
        self.scroll_widget.add_widget(self.info_panel)
        self.characters = []

        # browse all the scene folders for Maya files and export data
        if self.characters_folder:
            for name in self.character_asset_folders:
                asset = Asset(name=name, asset_type=AssetType.character, project=self.project)

                if asset.scene_file_path.exists():
                    self.characters.append(asset)

        # check the export folder
        info = f'Characters ({len(self.characters)} found):\n'
        info += '\n'.join(str(x) + '\n' for x in self.characters)
        self.label.setText(info)

        for asset in self.characters:
            character_export_widget = CharacterExportWidget(asset=asset, parent=self)
            panel_label = f'{asset.name} [{asset.status.name}]'
            panel = PanelWidget(title=panel_label, widget=character_export_widget, active=False)
            panel.inactive_style = 'QLabel {color:rgb' + str(asset.status.value) + '};'
            panel.update_panel_header()
            character_export_widget.panel_widget = panel
            self.scroll_widget.add_widget(panel)

        self.scroll_widget.add_stretch()
        self.restore_panel_states(state_dict=panel_states)

    @property
    def panel_widgets(self) -> list[PanelWidget]:
        return [x for x in self.scroll_widget.child_widgets if type(x) is PanelWidget]

    @property
    def panel_states(self) -> dict:
        return {x.windowTitle().split(' [')[0]: x.active for x in self.panel_widgets}

    def restore_panel_states(self, state_dict: dict):
        """
        Set the state of the panel widgets
        :param state_dict:
        """
        for title, value in state_dict.items():
            panel_widget = next((x for x in self.panel_widgets if x.windowTitle().split(' [')[0] == title), None)
            if panel_widget is not None and value:
                panel_widget.toggle_active()


class CharacterExportWidget(GenericWidget):
    title_column_width: int = 80
    exported = 'exported'
    missing = 'missing'
    needs_export = 'needs export'
    needs_update = 'needs update'
    rig_only = '[rig only]'
    up_to_date = 'up to date'
    rig = '[base rig]'

    def __init__(self, asset: Asset, parent: CharacterExporter):
        super(CharacterExportWidget, self).__init__(title=asset.name)
        self.asset = asset
        self.parent_widget: CharacterExporter = parent
        button_bar: GenericWidget = self.add_widget(GenericWidget(alignment=Alignment.horizontal))
        button_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.browse_button = button_bar.add_button('Open Folder', tool_tip=f'Open {self.asset.name} folder',
                                                   event=partial(open_file_location, self.asset.source_art_folder))
        self.export_rig_button = button_bar.add_button('Export Rig', tool_tip='Export just the character rig',
                                                       event=self.export_rig_button_clicked)
        self.export_animations_button = button_bar.add_button('Export Animations', tool_tip='Export the animations',
                                                              event=self.export_animations_button_clicked)
        self.metadata_button = button_bar.add_button(
            'View metadata', tool_tip='View the asset metadata file',
            event=partial(self.view_metadata_menu_item_clicked, self.asset.metadata_path))
        self.metadata_button.setVisible(logging.DEBUG >= logging.root.level)

        if logging.DEBUG >= logging.root.level:
            pass
            # self.debug_button = button_bar.add_button(text='Debug Function', event=self.debug_routine)

        button_bar.add_stretch()
        self.asset_grid: GridWidget = self.add_widget(GridWidget())
        self.add_stretch()
        self.init_asset_grid()
        self.update_button_states()
        self.panel_widget = None

    def update_button_states(self):
        """
        Standalone export capabilities currently not supported
        """
        self.export_rig_button.setEnabled(is_using_maya_python())
        self.export_animations_button.setEnabled(is_using_maya_python() and len(self.asset.animations) > 0)
        self.metadata_button.setEnabled(self.asset.metadata_path.exists())

    def update_panel_header(self):
        """
        Change the name of the parent panel
        self.panel_widget property must be set prior to using this
        """
        assert self.panel_widget is not None, 'Set the panel_widget property'
        panel_label = f'{self.asset.name} [{self.asset.status.name}]'
        self.panel_widget.set_panel_header(panel_label)
        self.panel_widget.inactive_style = 'QLabel {color:rgb' + str(self.asset.status.value) + '};'

    def init_asset_grid(self):
        """
        Clear the grid layout and add the base rig component
        """
        self.asset_grid.clear_layout()
        self.set_component(resource=self.asset.scene_resource)
        self.export_animations_button.setEnabled(len(self.asset.animation_resources))

        for animation_resource in self.asset.animation_resources:
            self.set_component(resource=animation_resource)

    @property
    def panel_widget(self) -> PanelWidget or None:
        return self._panel_widget

    @panel_widget.setter
    def panel_widget(self, panel_widget: PanelWidget):
        self._panel_widget = panel_widget

    def export_rig_button_clicked(self):
        """
        Event for self.export_rig_button
        """
        from maya_tools.scene_utils import get_scene_name, get_scene_path, load_scene

        scene_file_path: Path = self.asset.scene_file_path

        if get_scene_path() != scene_file_path:
            load_scene(scene_file_path)

        test_results: list[TestResult] = self.validate_rig()
        self.set_info(f'Exporting {get_scene_name()}')
        self.parent_widget.parent_widget.progress = 30

        if False in [test.passed for test in test_results]:
            self.notify_failed_validation(test_results)
            self.set_export_abort_message('Check log for errors')
        else:
            from maya_tools.ams.export_utils import export_rig

            export_rig(asset=self.asset)
            self.parent_widget.parent_widget.progress = 95
            self.set_component(resource=self.asset.scene_resource)

            for resource in self.asset.animation_resources:
                self.set_component(resource)

            self.update_panel_header()
            self.update_button_states()
            self.set_info(f'Export complete.')
            self.parent_widget.parent_widget.progress = 0

    def export_animations_button_clicked(self):
        """
        Event for self.export_animations_button
        """
        from maya_tools.ams.export_utils import export_animation
        from maya_tools.scene_utils import get_scene_path, load_scene, get_scene_name

        self.parent_widget.parent_widget.progress = 0
        num_anims = len(self.asset.animation_resources)

        for resource in self.asset.animation_resources:
            self.parent_widget.parent_widget.progress += 100 / num_anims
            if resource.status in (ItemStatus.export, ItemStatus.update):
                scene_file_path: Path = self.asset.get_animation_path(resource.scene_file_name)

                if get_scene_path() != scene_file_path:
                    load_scene(scene_file_path)

                self.set_info(f'Exporting {get_scene_name()}')
                test_results: list[TestResult] = self.validate_animation()

                if False in [test.passed for test in test_results]:
                    self.notify_failed_validation(test_results)
                    self.set_export_abort_message('Check log for errors')
                    return
                else:
                    export_animation(asset=self.asset, resource=resource)
                    updated_resource = self.asset.get_animation_resource_by_name(resource.name)
                    self.set_component(resource=updated_resource)

        self.update_panel_header()
        self.update_button_states()
        self.set_info(f'Animations for {self.asset.name} exported.')
        self.parent_widget.parent_widget.progress = 0

    def export_animation_menu_item_clicked(self, resource: Resource, *args):
        """
        Event for animation export menu item
        N.B. Can't invoke self.init_asset_grid() after export as QMenu would delete itself
        :param resource:
        :param args:
        """
        _ = args

        if is_using_maya_python():
            from maya_tools.scene_utils import get_scene_path, load_scene, get_scene_name

            scene_file_path: Path = self.asset.get_animation_path(resource.scene_file_name)

            if get_scene_path() != scene_file_path:
                load_scene(scene_file_path)

            test_results: list[TestResult] = self.validate_animation()
            self.set_info(f'Exporting {get_scene_name()}')

            if False in [test.passed for test in test_results]:
                self.notify_failed_validation(test_results)
                self.set_export_abort_message('Check log for errors')
            else:
                from maya_tools.ams.export_utils import export_animation

                self.set_info(f'Exporting {resource.name} as {resource.export_file_name}')
                export_animation(asset=self.asset, resource=resource)
                updated_resource = self.asset.get_animation_resource_by_name(resource.name)
                self.set_component(resource=updated_resource)
                self.update_panel_header()
                self.update_button_states()
        else:
            self.set_info('Use Export Manager in Maya to open scene')

    @staticmethod
    def notify_failed_validation(test_results: list[TestResult]):
        """
        Log the failure messages
        :param test_results:
        """
        for test_result in test_results:
            for message in test_result.failure_list:
                logging.info(message)

    def set_export_abort_message(self, message: str):
        """
        Convenience method to set export abort message
        :param message:
        """
        self.set_info(f'Export aborted: {message}')

    def set_info(self, text: str):
        """
        Conenience method to set info
        :param text:
        """
        self.parent_widget.parent_widget.info = text

    def view_metadata_menu_item_clicked(self, file_path, *args):
        """
        Event for view metadata button
        :param file_path:
        :param args:
        """
        _ = args
        self.set_info('Viewing metadata')
        open_file_location(file_path)

    @property
    def components(self) -> list:
        return self.asset_grid.get_column_values(column=0)

    def set_component(self, resource: Resource):
        """
        Creates a row with a name and a styled status label
        If the row exists already, it is updated
        :param resource
        """
        row = self.asset_grid.get_row_by_text(resource.scene_file_name)
        status_style = resource.status
        style_str = 'QLabel {background-color:rgb' + str(resource.status.value) + ';color:rgb(40, 40, 40)};'

        if row is not None:
            self.asset_grid.set_text(row=row, column=2, text=status_style.name, style=style_str, nice=True)
        else:
            row_count = self.asset_grid.row_count
            row = 0 if row_count == 1 and self.asset_grid.first_row_empty else row_count
            label: ClickableLabel = self.asset_grid.add_widget(
                ClickableLabel(resource.scene_file_name, button=Qt.MouseButton.RightButton), row=row, column=0)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            label.clicked.connect(partial(self.context_menu, self.asset, resource))
            self.asset_grid.add_label(text=f'[{resource.resource_type.name}]', row=row, column=1)
            self.asset_grid.add_label(status_style.name, row=row, column=2, style=style_str, nice=True)

    def context_menu(self, *args):
        """
        Shows a context menu at the clicked location
        :param args:
        """
        asset: Asset = args[0]
        resource: Resource = args[1]
        point: QPoint = args[2]
        scene_path = asset.source_art_folder.joinpath(resource.scene_file_name)
        export_file_path: Path = asset.get_resource_export_path(resource)
        open_scene_routine = partial(self.open_scene, scene_path)

        menu = QMenu()
        menu.addAction(resource.name)
        menu.addSeparator()
        menu.addAction(QAction(f'Open {resource.scene_file_name} in Maya', self, triggered=open_scene_routine))

        if resource.status is ItemStatus.exported:
            routine = partial(self.open_file_location, export_file_path)
            menu.addAction(QAction(f'Open {resource.export_file_name} in file browser', self, triggered=routine))

        if resource.status in (ItemStatus.export, ItemStatus.update) and resource.resource_type is ResourceType.animation:
            routine = partial(self.export_animation_menu_item_clicked, resource)
            menu.addAction(QAction(f'Export {resource.name} animation', self, triggered=routine))

        menu.exec_(point)

    @staticmethod
    def open_file_location(folder_location: Path, *args):
        """
        Open file location in file browser
        :param folder_location:
        :param args:
        """
        _ = args
        print(f'Opening file browser: {folder_location}')
        print(folder_location.exists())
        open_file_location(file_location=folder_location)

    def open_scene(self, scene_path: Path, *args):
        """
        Open scene in Maya
        :param scene_path:
        :param args:
        """
        _ = args

        if is_using_maya_python():
            self.set_info(f'Opening scene in Maya: {scene_path.name}')
            from maya_tools.scene_utils import load_scene
            load_scene(file_path=scene_path)
        else:
            self.set_info('Use Export Manager in Maya to open scene.')

    def debug_routine(self):
        """
        Just for testing stuff
        """
        logging.debug('debug routine')
        self.set_component(name='run', status_style=ItemStatus.export)
        self.set_component(name='walk', status_style=ItemStatus.export)

    def validate_animation(self) -> list[TestResult]:
        """
        Run the tests for animations
        :return:
        """
        from maya_tools.ams.validation.tests import latest_rig, asset_structure
        return self.run_test_suite([latest_rig.LatestRig(), asset_structure.AssetStructure()])

    def validate_rig(self) -> list[TestResult]:
        """
        Run the tests for rigs
        :return:
        """
        from maya_tools.ams.validation.tests import asset_structure
        return self.run_test_suite([asset_structure.AssetStructure()])

    def run_test_suite(self, asset_tests: list[AssetTest]) -> list[TestResult]:
        """
        Run a suite of AssetTest tests
        :param asset_tests:
        :return:
        """
        logging.info(f'Validating {self.asset.name}')

        return [asset_test.test(self.asset) for asset_test in asset_tests]


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    widget = CharacterExportWidget(name='Clairee', parent=None)
    widget.show()
    app.exec()

