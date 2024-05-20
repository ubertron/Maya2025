import os

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget

from core.core_enums import Alignment, AssetType
from core.environment_utils import is_using_maya_python
from maya_tools.ams.asset import Asset
from widgets.generic_widget import GenericWidget
from widgets.scroll_widget import ScrollWidget


class CharacterExporter(GenericWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super(CharacterExporter, self).__init__('Character Exporter')
        self.parent_widget: QWidget or None = parent
        top_bar: GenericWidget = self.add_widget(GenericWidget(alignment=Alignment.horizontal))
        top_bar.add_button('Refresh', tool_tip='Update status info', event=self.collect_asset_data)
        top_bar.add_button('Browse...', tool_tip='Open assets in a Finder window')
        top_bar.add_stretch()
        top_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        scroll_panel = self.add_widget(ScrollWidget())
        self.label: QLabel = scroll_panel.add_label('Character data...', center_align=False)
        self.label.setWordWrap(True)

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
        print(self.character_asset_folders)
        # browse all the scene folders for Maya files and export data
        for folder in self.character_asset_folders:
            asset = Asset(source_folder=self.character_folder.joinpath(folder), asset_type=AssetType.character)
            if asset.scene_file_exists:
                characters.append(asset)

        # check the export folder
        info = f'Characters ({len(characters)} found):\n'
        info += '\n'.join(str(x) + '\n' for x in characters)
        self.label.setText(info)


