"""Instance of HotkeyManager for Maya 2025"""
import logging

from pathlib import Path

from core.core_enums import Language, ModifierKey
from core.core_paths import PROJECT_ROOT
from maya_tools.maya_environment_utils import is_using_mac_osx
from maya_tools.utilities import hotkey_manager
from legacy import hotkey_manager_legacy

ROBOTOOLS_HOTKEYS_NAME: str = 'Robotools_Hotkeys'
ROBOTOOLS_HOTKEYS_PATH: Path = PROJECT_ROOT.joinpath('scripts', 'startup', f'{ROBOTOOLS_HOTKEYS_NAME}.mhk')


class RobotoolsHotkeys(hotkey_manager.HotkeyManager):
    """Hotkey Manager."""

    def __init__(self):
        super(RobotoolsHotkeys, self).__init__(hotkey_set=ROBOTOOLS_HOTKEYS_NAME)

    def apply(self):
        self._set_hotkey(
            name="toggleGrid", annotation="Toggle the display grid.",
            command="ToggleGrid;", hotkey=";", modifier_keys=[ModifierKey.control],
            language=Language.mel)
        self._set_hotkey(
            name="createCube", annotation="Create a cube",command=self.cube_command,
            hotkey="c",
            modifier_keys=[ModifierKey.control,ModifierKey.alt, ModifierKey.command],
            language=Language.python)
        self._set_hotkey(
            name="appendToPolygon", annotation="Append to polygon tool",
            command="AppendToPolygonTool;", hotkey="a",
            modifier_keys=(ModifierKey.control, ModifierKey.command),
            language=Language.mel)
        self._set_hotkey(
            name="hotkeyEditor", annotation="Hotkey Editor",
            command="HotkeyPreferencesWindow;", hotkey="h",
            modifier_keys=[ModifierKey.control, ModifierKey.alt, ModifierKey.command],
            language=Language.mel)
        self._set_hotkey(
            name="createPolygon", annotation="Create polygon tool",
            command="CreatePolygonTool;", hotkey="C",
            modifier_keys=[ModifierKey.control], language=Language.mel)
        self._set_hotkey(
            name="combine", annotation="Combine geometry",
            command="CombinePolygons;", hotkey="A",
            modifier_keys=[ModifierKey.control, ModifierKey.alt], language=Language.mel)
        self._set_hotkey(
            name="mergeVertices", annotation="Merge vertices",
            command="PolyMergeVertices;", hotkey="W",
            modifier_keys=[ModifierKey.command], language=Language.mel)
        self._set_hotkey(
            name="selectEdgeLoop", annotation="Select Edge Loop",
            command="SelectEdgeLoopSp;", hotkey="]",
            modifier_keys=[ModifierKey.command], language=Language.mel)
        self._set_hotkey(
            name="selectEdgeRing", annotation="Select Edge Ring",
            command="SelectEdgeRingSp;", hotkey="[",
            modifier_keys=[ModifierKey.command], language=Language.mel)
        self._set_hotkey(
            name="connect", annotation="Merge vertices",
            command="ConnectComponents;", hotkey="C", language=Language.mel)

    @property
    def cube_command(self) -> str:
        """Command creates a cube."""
        return "from maya_tools.geometry_utils import create_cube; create_cube()"


class RobotoolsHotkeyManager(hotkey_manager_legacy.HotkeyManager):
    def __init__(self):
        super(RobotoolsHotkeyManager, self).__init__(name=ROBOTOOLS_HOTKEYS_NAME, path=ROBOTOOLS_HOTKEYS_PATH)

    def init_hotkeys(self):
        """
        Set up the hotkeys
        """
        logging.info('>>> Setting up Robotools hotkeys')
        is_mac: bool = is_using_mac_osx()
        is_pc: bool = not is_using_mac_osx()

        self.set_hotkey('hotkeyPrefs', annotation='Hotkey Editor', mel_command='HotkeyPreferencesWindow',
                        key='H', cmd=is_mac, ctrl=is_pc, overwrite=True)
        self.set_hotkey('appendToPoly', annotation='Append To Poly', mel_command='AppendToPolygonTool',
                        key='A', cmd=is_mac, ctrl=is_pc, overwrite=True)
        self.set_hotkey('createPoly', annotation='Create Polygon Tool', mel_command='CreatePolygonTool',
                        key='C', cmd=is_mac, ctrl=is_pc, overwrite=True)
        self.set_hotkey('combine', annotation='Combine', mel_command='CombinePolygons',
                        key='A', cmd=is_mac, ctrl=is_pc, alt=True, overwrite=True)
        self.set_hotkey('mergeVertices', annotation='Merge Vertices', mel_command='PolyMergeVertices',
                        key='W', cmd=is_mac, ctrl=is_pc, overwrite=True)
        self.set_hotkey('toggleGrid', annotation='Toggle Grid', mel_command='ToggleGrid',
                        key=';', cmd=is_mac, ctrl=is_pc, overwrite=True)
        self.set_hotkey('selectEdgeLoop', annotation='Select Edge Loop', mel_command='SelectEdgeLoopSp',
                        key=']', cmd=is_mac, ctrl=is_pc, overwrite=True)
        self.set_hotkey('selectEdgeRing', annotation='Select Edge Ring', mel_command='SelectEdgeRingSp',
                        key='[', cmd=is_mac, ctrl=is_pc, overwrite=True)
        self.set_hotkey('connect', annotation='Connect', mel_command='ConnectComponents', key='C', overwrite=True)

    def save_hotkeys(self):
        """
        Save the hotkeys file locally
        """
        ROBOTOOLS_HOTKEYS_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.export_set()
