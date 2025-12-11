import sys

from functools import partial
from PySide6.QtCore import QSettings, QRegularExpression, Qt
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QLabel, QSizePolicy
# from maya import cmds

from core import DEVELOPER
from core.version_info import VersionInfo
from widgets.form_widget import FormWidget
from widgets.generic_widget import GenericWidget
from widgets.button_bar import ButtonBar
from ams.asset import Asset
from ams.ams_enums import AssetType
from ams.ams_paths import PROJECT_NAME
from core.core_enums import Alignment, Side
from core.core_paths import image_path
from core import uuid_utils

TOOL_NAME = "Stubber"
VERSIONS = [
    VersionInfo(name=TOOL_NAME, version="1.0", codename="commando", info="initial release")
]
UI_SCRIPT = "from ams import stubber\nstubber.Stubber().restore()"


class Stubber(GenericWidget):
    asset_type_key: str = "asset"
    pad: int = 20

    def __init__(self):
        super().__init__(title=VERSIONS[-1].title)
        self.settings = QSettings(DEVELOPER, TOOL_NAME)
        button_bar: ButtonBar = self.add_widget(ButtonBar())
        self.uuid_button = button_bar.add_icon_button(
            icon_path=image_path("uuid.png"), tool_tip="Generate UUID", clicked=self.generate_uuid_button_clicked)
        self.create_button = button_bar.add_icon_button(
            icon_path=image_path("add.png"), tool_tip="Create Asset", clicked=self.create_asset_button_clicked)
        button_bar.add_stretch()
        self.help_button = button_bar.add_icon_button(
            icon_path=image_path("help.png"), tool_tip="Help", clicked=self.help_button_clicked)
        self.form: FormWidget = self.add_widget(FormWidget())
        self.project_label: QLabel = self.form.add_row(label="Project", widget=QLabel())
        self.name_line_edit = self.form.add_line_edit(label="Name", placeholder_text="Enter asset name...")
        self.asset_type_combo_box = self.form.add_combo_box(label="Asset Type", items=[x.value.title() for x in AssetType.geometry_types()])
        self.tags_line_edit = self.form.add_line_edit(label="Tags", placeholder_text="Enter tags...")
        self.uuid_label = self.add_label()
        self.add_stretch()
        self.info_label: Label = self.add_label("Ready...", side=Side.left)
        self.ready: bool = False
        self._setup_ui()

    def _setup_ui(self):
        asset_type_index = self.settings.value(self.asset_type_key, 0)
        self.asset_type_combo_box.setCurrentIndex(asset_type_index)
        self.asset_type_combo_box.currentIndexChanged.connect(self.asset_type_index_changed)
        self.uuid_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.generate_uuid_button_clicked()
        self.project_label.setText(PROJECT_NAME)
        name_validator = QRegularExpressionValidator(QRegularExpression("^[a-z][a-z_]*$"), self)
        self.name_line_edit.setValidator(name_validator)
        self.name_line_edit.textChanged.connect(self.form_updated)
        tags_validator = QRegularExpressionValidator(QRegularExpression("^[a-z_,\s]*$"), self)
        self.tags_line_edit.setValidator(tags_validator)
        self.tags_line_edit.returnPressed.connect(self.evaluate_tags)
        self.uuid_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.form_updated()

    def asset_type_index_changed(self, arg):
        self.settings.setValue(self.asset_type_key, arg)

    @property
    def info(self) -> str:
        return self.info_label.text()

    @info.setter
    def info(self, value):
        self.info_label.setText(value)

    @property
    def name(self) -> str:
        return self.name_line_edit.text()

    @property
    def tags(self) -> list:
        self.evaluate_tags()
        return [x for x in self.tags_line_edit.text().split(", ") if x]

    @property
    def uuid(self):
        return self.uuid_label.text()

    def create_asset_button_clicked(self):
        self.info = "create button clicked"
        self.ready = False
        self.form_updated()

    def evaluate_tags(self):
        tag_string = self.tags_line_edit.text()
        tokens = [x for x in tag_string.split(",") if x]
        tokens = sorted(x.strip() for x in tokens)
        self.tags_line_edit.setText(", ".join(tokens))

    def generate_uuid_button_clicked(self):
        """Event for generate uuid button."""
        self.ready = True
        self.uuid_label.setText(str(uuid_utils.generate_uuid(max_length=8)))
        self.form_updated()

    def help_button_clicked(self):
        """Event for generate help button."""
        self.info = "help button clicked"

    def form_updated(self):
        self.create_button.setEnabled(self.name != "" and self.ready)

    def refresh_button_clicked(self):
        self.info = "refresh button clicked"


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QSizePolicy

    app = QApplication(sys.argv)
    window = Stubber()
    window.show()
    app.exec()