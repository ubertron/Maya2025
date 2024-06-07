from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QLabel, QPushButton, QSizePolicy, QTabWidget, QProgressBar
from PySide6.QtCore import QSettings, Qt

from widgets.generic_widget import GenericWidget
from core import DEVELOPER
from core.core_enums import Alignment
from core.environment_utils import is_using_maya_python
from maya_tools.ams.character_exporter import CharacterExporter
from maya_tools.ams.environment_exporter import EnvironmentExporter
from maya_tools.ams.project_utils import load_project_definition
from maya_tools.ams.project_definition import ProjectDefinition


class ExportManager(GenericWidget):
    title: str = 'Export Manager'
    version: str = '0.1'
    codename: str = 'hot mango'
    project_key: str = 'project_root'

    def __init__(self):
        super(ExportManager, self).__init__(title=f'{self.title} v{self.version} [{self.codename}]')
        project_widget: GenericWidget = self.add_widget(GenericWidget(alignment=Alignment.horizontal))
        project_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.settings = QSettings(DEVELOPER, self.title.replace(' ', ''))
        self.project_label: QLabel = project_widget.add_label('Project:')
        project_widget.add_stretch()
        self.set_project_button: QPushButton = project_widget.add_button(
            'Set Project...', tool_tip='Set the project for the tool.', event=self.set_project_button_clicked)
        self.tab_bar: QTabWidget = self.add_widget(QTabWidget())
        self.character_exporter: CharacterExporter = CharacterExporter(self)
        self.environment_exporter = EnvironmentExporter(self)
        self.tab_bar.addTab(self.character_exporter, 'Characters')
        self.tab_bar.addTab(self.environment_exporter, 'Environments')
        self.info_label: QLabel = self.add_label(center_align=False)
        self.info_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.progress_bar: QProgressBar = self.add_widget(QProgressBar())
        self.project = None
        self.project_root: Path = self.settings.value(self.project_key, defaultValue=None)
        self.setFixedSize(400 if is_using_maya_python() else 500, 500)
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        self.progress = 0

    def refresh(self):
        self.character_exporter.refresh_button_clicked()

    @property
    def progress(self):
        return self.progress_bar.value()

    @progress.setter
    def progress(self, value):
        self.progress_bar.setVisible(value > 0)
        self.progress_bar.setValue(value)

    def set_project_button_clicked(self):
        """
        Event for set_project_button
        """
        message = 'Browse for the project directory'
        default = self.project_root.parent.as_posix() if self.project_root else None
        d = QFileDialog.getExistingDirectory(self, caption=message, dir=default, options=QFileDialog.ShowDirsOnly)

        if d:
            self.project_root = Path(d)
            self.refresh()

    @property
    def info(self):
        return self.info_label.text()

    @info.setter
    def info(self, value: str):
        self.info_label.setText(value)

    @property
    def project_root(self) -> Path or None:
        return self._project_root

    @project_root.setter
    def project_root(self, value: Path or str or None):
        if value and Path(value).exists():
            path = Path(value)
            self._project_root = path
            self.project = load_project_definition(project_root=path)
            self.project_label.setText(str(self.project))
            self.settings.setValue(self.project_key, path.as_posix())
        else:
            self._project_root = None

        self.character_exporter.refresh()

    @property
    def project(self) -> ProjectDefinition or None:
        return self._project

    @project.setter
    def project(self, project_definition: ProjectDefinition or None):
        self._project = project_definition
        self.info = f'Welcome to {project_definition.name}.' if project_definition else 'Please set the project.'


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    export_manager = ExportManager()
    export_manager.show()
    sys.exit(app.exec())
