"""Utils to handle Maya ascii files."""
from __future__ import annotations

import logging

from core.logging_utils import get_logger
from pathlib import Path

from core.path_utils import get_incremented_file_path
from widgets.are_you_sure_widget import AreYouSureWidget

LOGGER = get_logger(name=__name__, level=logging.DEBUG)


class MayaAsciiEditor:
    def __init__(self, path: Path):
        self.path = path
        with path.open("r") as file:
            self.lines = file.read().split("\n")

    @property
    def count(self) -> int:
        return len(self.lines)

    @property
    def lines(self) -> list[str]:
        return self._lines

    @lines.setter
    def lines(self, val: list[str]):
        self._lines = val

    def purge_reference(self, reference: str):
        """Remove vray nodes from a scene file."""
        complete = False
        lines_to_remove = []
        count = self.count
        while not complete:
            index = next((i for i in range(count) if reference in self.lines[i].lower() and i not in lines_to_remove), None)
            if index:
                lines_to_remove.append(index)

                # get remaining items in the block
                block_found = False
                block_index = index + 1
                while not block_found:
                    if self.lines[block_index].startswith("\t"):
                        lines_to_remove.append(block_index)
                        block_index += 1
                    else:
                        block_found = True
            else:
                complete = True
        for x in lines_to_remove:
            LOGGER.debug(self.lines[x])
        self.lines = [self.lines[i] for i in range(count) if i not in lines_to_remove]

    def save(self, path: Path | None):
        path = path if path else self.path
        with path.open("w") as file:
            file.write("\n".join(self.lines))


def fix_maya_ascii() -> Path | None:
    """Automatic scene fixer.

    Saves and opens a fixed version of the Maya ASCII file.
    """
    from maya import mel
    from maya_tools import scene_utils
    scene_path = scene_utils.get_scene_path()
    if scene_path.suffix != ".ma":
        LOGGER.warning(f"{scene_path} is not a Maya ASCII file.")
        return None
    editor = MayaAsciiEditor(path=scene_path)
    editor.purge_reference(reference="vray")
    if scene_path.stem[-1].isnumeric():
        fixed_file_path = get_incremented_file_path(path=scene_path)
    else:
        fixed_file_path = scene_path.with_stem(f"{scene_path.stem}_")
    def do_it(arg: bool):
        if arg:
            editor.save(path=fixed_file_path)
            scene_utils.load_scene(file_path=fixed_file_path)
    if fixed_file_path.exists():
        dialog = AreYouSureWidget(question=f"Overwrite {fixed_file_path.name} ?")
        dialog.responded.connect(do_it)
        dialog.show()
    else:
        do_it(arg=True)
        return fix_maya_ascii()


if __name__ == "__main__":
    scene_path = Path.home() / "Dropbox/Projects/Maya/USD Sandbox/scenes/room/room.004.ma"
    new_path = Path.home() / "Dropbox/Projects/Maya/USD Sandbox/scenes/room/room.005.ma"
    # editor = MayaAsciiEditor(path=scene_path)
    # editor.purge_reference(reference="vray")
    # editor.save(path=new_path)
    result = get_incremented_file_path(path=scene_path)
    print(result)
