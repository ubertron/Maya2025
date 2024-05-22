import logging

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget
from PySide6.QtCore import Qt

from core.core_enums import Alignment, AssetType
from maya_tools.ams.ams_enums import StatusStyle
from maya_tools.ams.asset import Asset
from widgets.generic_widget import GenericWidget
from widgets.scroll_widget import ScrollWidget
from widgets.grid_widget import GridWidget
from widgets.panel_widget import PanelWidget


logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


class CharacterExporter(GenericWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super(CharacterExporter, self).__init__('Character Exporter')
        self.parent_widget: QWidget or None = parent
        self.button_bar: GenericWidget = self.add_widget(GenericWidget(alignment=Alignment.horizontal))
        self.button_bar.add_button('Refresh', tool_tip='Update status info', event=self.collect_asset_data)
        self.button_bar.add_button('Browse...', tool_tip='Open assets in a Finder window')
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
    def source_art(self) -> Path:
        return self.project_root.joinpath('SourceArt')

    @property
    def character_folder(self):
        return self.source_art.joinpath('Characters')

    @property
    def exports(self):
        return self.project_root.joinpath('Assets/Models')

    @property
    def character_asset_folders(self) -> list[str]:
        result = [x.name for x in self.character_folder.iterdir() if x.is_dir()] if self.character_folder.exists() else []
        result.sort(key=lambda x: x.lower())
        return [x for x in result if not x.startswith('_')]

    def collect_asset_data(self):
        self.scroll_widget.clear_layout()
        self.scroll_widget.add_widget(self.info_panel)
        self.characters = []

        # browse all the scene folders for Maya files and export data
        for folder in self.character_asset_folders:
            asset = Asset(source_folder=self.character_folder.joinpath(folder), asset_type=AssetType.character)
            if asset.scene_file_exists:
                self.characters.append(asset)

        # check the export folder
        info = f'Characters ({len(self.characters)} found):\n'
        info += '\n'.join(str(x) + '\n' for x in self.characters)
        self.label.setText(info)

        for character in self.characters:
            character_export_widget = CharacterExportWidget(asset=character, parent=self)
            panel = PanelWidget(title=character.name, widget=character_export_widget, active=False)
            self.scroll_widget.add_widget(panel)

        self.scroll_widget.add_stretch()


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
        self.export_rig_button = button_bar.add_button('Export Rig', tool_tip='Export just the character rig')
        self.export_animations_button = button_bar.add_button('Export Animations',
                                                              tool_tip='Export the rig and the animations')

        if logging.DEBUG >= logging.root.level:
            self.debug_button = button_bar.add_button(text='Debug Function', event=self.debug_routine)

        button_bar.add_stretch()
        self.asset_grid: GridWidget = self.add_widget(GridWidget())
        self.add_stretch()
        self.init_asset_grid()

    def init_asset_grid(self):
        """
        Clear the grid layout and add the base rig component
        """
        self.asset_grid.clear_layout()
        self.set_component(name=self.rig, status_style=StatusStyle.needs_export)

        for animation in self.asset.animations:
            self.set_component(name=animation, status_style=StatusStyle.needs_export)

    @property
    def components(self) -> list:
        return self.asset_grid.get_column_values(column=0)

    def set_component(self, name: str, status_style: StatusStyle):
        """
        Creates a row with a name and a styled status label
        :param name:
        :param status_style:
        """
        row = self.asset_grid.get_row_by_text(name)

        if row:
            self.asset_grid.set_text(row=row, column=1, text=status_style.name, style=status_style.value, nice=True)
        else:
            row_count = self.asset_grid.row_count
            row = 0 if row_count == 1 and self.asset_grid.first_row_empty else row_count
            self.asset_grid.add_label(name, row=row, column=0, alignment=Qt.AlignmentFlag.AlignLeft)
            self.asset_grid.add_label(status_style.name, row=row, column=1, style=status_style.value, nice=True)

    def debug_routine(self):
        """
        Just for testing stuff
        """
        logging.debug('debug routine')
        # self.set_component(name='run', status_style=StatusStyle.needs_export)
        # self.set_component(name='walk', status_style=StatusStyle.needs_export)


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    widget = CharacterExportWidget(name='Clairee', parent=None)
    widget.show()
    app.exec()
