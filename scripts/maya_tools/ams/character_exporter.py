import os

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget
from PySide6.QtCore import Qt

from core.core_enums import Alignment, AssetType
from core.environment_utils import is_using_maya_python
from maya_tools.ams.asset import Asset
from widgets.generic_widget import GenericWidget
from widgets.scroll_widget import ScrollWidget
from widgets.grid_widget import GridWidget
from widgets.panel_widget import PanelWidget


class CharacterExporter(GenericWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super(CharacterExporter, self).__init__('Character Exporter')
        self.parent_widget: QWidget or None = parent
        self.button_bar: GenericWidget = self.add_widget(GenericWidget(alignment=Alignment.horizontal))
        self.button_bar.add_button('Refresh', tool_tip='Update status info', event=self.collect_asset_data)
        self.button_bar.add_button('Browse...', tool_tip='Open assets in a Finder window')
        self.button_bar.add_stretch()
        self.button_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        scroll_panel: ScrollWidget = self.add_widget(ScrollWidget())
        self.label: QLabel = QLabel('Character data...')
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.info_panel: Panel_Widget = scroll_panel.add_widget(PanelWidget(title='Information', widget=self.label,
                                                                            active=False))

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
        characters = []
        # print(self.character_asset_folders)
        # browse all the scene folders for Maya files and export data
        for folder in self.character_asset_folders:
            asset = Asset(source_folder=self.character_folder.joinpath(folder), asset_type=AssetType.character)
            if asset.scene_file_exists:
                characters.append(asset)

        # check the export folder
        info = f'Characters ({len(characters)} found):\n'
        info += '\n'.join(str(x) + '\n' for x in characters)
        self.label.setText(info)


class CharacterExportWidget(GenericWidget):
    title_column_width: int = 80

    def __init__(self, name: str, parent: CharacterExporter):
        super(CharacterExportWidget, self).__init__(title=name)
        self.parent_widget: CharacterExporter = parent
        self.button_bar = GenericWidget(alignment=Alignment.horizontal)
        self.export_rig_button = self.add_button('Export Rig')
        self.export_animations_button = self.add_button('Export Animations')
        self.asset_grid: GridWidget = GridWidget()
        self.asset_grid.set_component(name='rig', status='to be exported')

    def set_component(self, name: str, status: str):
        self.asset_grid.add_label(name, row=0, column=0)
        self.asset_grid.add_label(status, row=0, column=1)


