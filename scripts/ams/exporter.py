from __future__ import annotations

import json
import shutil

from maya import cmds
from pathlib import Path
from PySide6.QtWidgets import QLabel

from ams import ams_paths
from ams.asset import Asset
from core.core_enums import AssetType, Side
from core.core_paths import image_path
from core import date_time_utils, file_utils
from core.version_info import VersionInfo
from maya_tools import material_utils, node_utils, scene_utils
from maya_tools.io import fbx_utils, fbx_presets
from widgets.button_bar import ButtonBar
from widgets.form_widget import FormWidget
from widgets.generic_widget import GenericWidget
from widgets.group_box import GroupBox


TOOL_NAME = "Exporter"
UI_SCRIPT = "from ams import exporter; exporter.Exporter().restore()"
VERSIONS = [
    VersionInfo(name=TOOL_NAME, version="0.0.1", codename="streethawk", info="initial version"),
    VersionInfo(name=TOOL_NAME, version="0.0.2", codename="airwolf", info="added info about maya source file"),
    VersionInfo(name=TOOL_NAME, version="0.0.3", codename="blue thunder", info="texture transfer")
]


class Exporter(GenericWidget):

    def __init__(self, padding_length: int = 3):
        super().__init__(title=VERSIONS[-1].title)
        button_bar: ButtonBar = self.add_widget(ButtonBar())
        button_bar.add_icon_button(
            icon_path=image_path("refresh.png"), tool_tip="Update details", clicked=self.update_form)
        self.export_button = button_bar.add_icon_button(
            icon_path=image_path("export.png"), tool_tip="Export Scene", clicked=self.export_button_clicked)
        button_bar.add_icon_button(
            icon_path=image_path("metadata.png"), tool_tip="Open metadata", clicked=self.metadata_button_clicked)
        button_bar.add_stretch()
        self.form: FormWidget = self.add_widget(FormWidget())
        self.form.add_label(label="Project")
        self.form.add_label(label="Project root")
        self.form.add_label(label="Asset name")
        self.form.add_label(label="Scene name")
        self.form.add_label(label="Asset type")
        self.form.add_label(label="UUID")
        self.form.add_label(label="Source directory")
        self.form.add_label(label="Current version")
        self.form.add_label(label="Scene version")
        self.form.add_label(label="Export path")
        self.form.add_label(label="Target path")
        self.add_stretch()
        self.info_label = self.add_label(side=Side.left)
        self.padding_length = padding_length
        self._setup_ui()

    def _setup_ui(self):
        self.update_form()

    def _validate(self):
        valid = bool(ams_paths.PROJECT_ROOT and self.target_path)
        self.export_button.setEnabled(valid)
        self.info = "Ready for export..." if valid else "Warning: Fix issues before export"

    @property
    def asset_name(self) -> str | None:
        return self.scene_name.split(".")[0] if self.scene_name else None

    @property
    def asset_type(self) -> AssetType | None:
        asset_type = self.metadata.get("asset_type")
        return AssetType[asset_type] if asset_type else None

    @property
    def current_version(self) -> str | None:
        if self.export_dir and self.export_dir.exists():
            versions = [x for x in self.export_dir.iterdir() if x.suffix == ".fbx"]
            versions.sort()
            return versions[-1].name
        return None

    @property
    def export_dir(self) -> Path | None:
        return self.scene_path.parent / "Exports" if self.scene_path else None

    @property
    def export_path(self) -> Path | None:
        current_version = self.current_version
        if current_version:
            _, version, _ = current_version.split(".")
        else:
            version = 1
        filename = f"{self.asset_name}.{int(version) + 1:0{self.padding_length}}.fbx"
        return self.export_dir.joinpath(filename).relative_to(ams_paths.PROJECT_ROOT)

    @property
    def export_path_abs(self) -> Path | None:
        return ams_paths.PROJECT_ROOT / self.export_path if self.export_path else None

    @property
    def info(self) -> str:
        return self.info_label.text()

    @info.setter
    def info(self, text: str):
        self.info_label.setText(text)

    @property
    def metadata(self) -> dict:
        if self.metadata_path and self.metadata_path.exists():
            with self.metadata_path.open("r") as f:
                return json.load(f)
        return {}

    @property
    def metadata_path(self) -> Path | None:
        return scene_utils.get_scene_path().parent / "metadata.json" if scene_utils.get_scene_path() else None

    @property
    def scene_name(self) -> str | None:
        return scene_utils.get_scene_name()

    @property
    def scene_path(self) -> Path | None:
        return scene_utils.get_scene_path()

    @property
    def source_dir(self) -> Path | None:
        return self.scene_path.parent.relative_to(ams_paths.PROJECT_ROOT) if self.scene_path else None

    @property
    def scene_version(self) -> Path | None:
        """Get the scene version from the most recently saved metadata."""
        path = self.metadata.get("scene_version")
        return Path(path) if path else None

    @property
    def target_path(self) -> Path | None:
        path = self.metadata.get("target_path")
        return Path(path) if path else None

    @property
    def target_path_abs(self) -> Path | None:
        return ams_paths.PROJECT_ROOT / self.target_path if self.target_path else None

    @property
    def uuid(self) -> str | None:
        return self.metadata.get("uuid")

    def export_button_clicked(self):
        """Event for export button."""
        fbx_presets.GeometryExportPreset().activate()
        geometry_root_nodes = node_utils.get_root_geometry_transforms()
        if geometry_root_nodes:
            cmds.select(geometry_root_nodes)
            export_path = self.export_path_abs
            fbx_utils.export_fbx(export_path=self.export_path_abs, selected=True)
            self.target_path_abs.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(export_path, self.target_path_abs)
            self.transfer_textures()
            self.update_form()
            self.info = f"{self.asset_name} exported successfully -> {self.current_version}"
            self.update_metadata()
        else:
            self.info = "Warning: no geometry found in scene."

    def metadata_button_clicked(self):
        if self.metadata_path.exists():
            file_utils.open_in_text_edit(path=self.metadata_path)

    @staticmethod
    def transfer_textures():
        """Collect the textures and send to the textures directory."""
        ams_paths.TEXTURES.mkdir(parents=True, exist_ok=True)
        for texture in material_utils.collect_textures():
            shutil.copy(texture, ams_paths.TEXTURES / texture.name)

    def update_form(self):
        """Update the form with export details."""
        self.form.set_value(label="Project", value=ams_paths.PROJECT_NAME)
        self.form.set_value(label="Project root", value=ams_paths.PROJECT_ROOT)
        self.form.set_value(label="Scene name", value=self.scene_name)
        self.form.set_value(label="Asset name", value=self.asset_name)
        self.form.set_value(label="Asset type", value=self.asset_type.name if self.asset_type else "?")
        self.form.set_value(label="UUID", value=self.uuid if self.uuid else "?")
        self.form.set_value(label="Source directory", value=self.source_dir)
        self.form.set_value(label="Export path", value=self.export_path if self.export_path else "?")
        self.form.set_value(label="Scene version", value=self.scene_version.name if self.scene_version else "?")
        self.form.set_value(label="Target path", value=self.target_path)
        self.form.set_value(label="Current version", value=self.current_version if self.current_version else "None")
        self._validate()

    def update_metadata(self):
        """Update the metadata with export details."""
        if self.metadata_path.exists():
            metadata = self.metadata
            metadata["export_date"] = date_time_utils.get_date_time_string()
            metadata["export_version"] = self.current_version
            metadata["scene_version"] = self.scene_name
            sorted_data = sorted(metadata.items())
            updated = dict(sorted_data)
            with self.metadata_path.open("w") as f:
                json.dump(updated, f, indent=4)
