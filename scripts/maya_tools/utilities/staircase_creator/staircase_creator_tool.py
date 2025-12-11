from maya_tools.utilities.staircase_creator import staircase_creator
from core.core_enums import Side
from core.core_paths import image_path
from core.version_info import VersionInfo, Versions
from widgets.button_bar import ButtonBar
from widgets.generic_widget import GenericWidget
from core.core_enums import Axis
from core.core_paths import image_path
from widgets.form_widget import FormWidget

TOOL_NAME = "Staircase Creator"
VERSIONS = Versions(versions=[
    VersionInfo(name=TOOL_NAME, version="0.0.1", codename="hawk", info="first_release")])


class StaircaseCreatorTool(GenericWidget):
    def __init__(self):
        super().__init__(title=VERSIONS.title)
        buttons: ButtonBar = self.add_widget(ButtonBar())
        buttons.add_icon_button(
            icon_path=image_path("refresh.png"), tool_tip="Refresh", clicked=self.refresh_button_clicked)
        buttons.add_icon_button(
            icon_path=image_path("stairs.png"), tool_tip="Create Stairs", clicked=self.stairs_button_clicked)
        buttons.add_icon_button(
            icon_path=image_path("locators.png"), tool_tip="Create Locators", clicked=self.locators_button_clicked)
        form: FormWidget = self.add_widget(FormWidget())
        self.rise_input = form.add_float_field(
            label="Target rise", default_value=20.0, minimum=1.0, maximum=200.0, step=1.0)
        self.axis_combo_box = form.add_combo_box(label="Axis", items=("x", "z"), default_index=1)
        buttons.add_stretch()
        self.add_stretch()
        self.info_label = self.add_label("Ready...", side=Side.left)

    @property
    def axis(self) -> Axis:
        return Axis[self.axis_combo_box.currentText()]

    @property
    def info(self) -> str:
        return self.info_label.text()

    @info.setter
    def info(self, value: str):
        self.info_label.setText(value)

    @staticmethod
    def locators_button_clicked(self):
        """Event for locators button."""
        from maya import cmds
        for i in range(2):
            locator = cmds.spaceLocator()
            cmds.setAttr(f"{locator[0]}.localScale", 50, 50, 50, type="float3")
            cmds.rename(locator[0], f"stair_locator{i}")

    def stairs_button_clicked(self):
        try:
            creator = staircase_creator.StaircaseCreator(default_rise=self.rise_input.value(), axis=self.axis)
            creator.create()
            self.info = "Stairs created"
        except AssertionError as e:
            self.info = str(e)

    def refresh_button_clicked(self):
        self.info = "Refresh button clicked"


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    tool = StaircaseCreatorTool()
    tool.show()
    app.exec_()
