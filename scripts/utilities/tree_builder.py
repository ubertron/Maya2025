"""Creates text representations of folder structures.

Use characters like |-- for items that are not the last in a list and └── for the last item in a list to create a visual tree structure.

RootFolder/
|-- FolderA/
|   |-- FileA1.txt
|   └── FileA2.txt
|-- FolderB/
|   └── SubFolderB1/
|       └── FileB1.txt
|-- FileC.text
└── FileD.txt

"""
from __future__ import annotations
from pathlib import Path
from typing import Iterable, Tuple


class TreeBuilder:
    """Class to create text representations of folder structures."""

    def __init__(self, root: str | Path, dir_token: str = "", omit_list: Iterable[str] = ()):
        """Init.

        Args:
            root: Path to the root folder.
            dir_token: Token used to identify folders.
            omit_list: Items to omit from the folder structure.
        """
        self.root = Path(root)
        self.dir_token = dir_token
        self.omit_list = omit_list

    @property
    def parent(self) -> Path:
        return self.root.parent

    @property
    def paths(self) -> list[tuple[Path, bool]]:
        """Returns a list of paths and a bool indicating if a path is last item in a directory."""
        paths = []
        def get_paths(dir_path: Path, path_list: list[Path], is_last: bool) -> list[Path]:
            if dir_path.name not in self.omit_list:
                directories = [x for x in dir_path.glob("*") if x.is_dir()]
                directories.sort(key=lambda x: x.as_posix())
                files = [x for x in dir_path.glob("*") if x.is_file() if x.name not in self.omit_list]
                files.sort(key=lambda x: x.as_posix())
                path_list.append((dir_path.relative_to(self.parent), is_last))
                for directory in directories:
                    is_last = directory == directories[-1] and len(files) == 0
                    get_paths(dir_path=directory, path_list=path_list, is_last=is_last)
                path_list.extend((f.relative_to(self.parent), f == files[-1]) for f in files)
        get_paths(self.root, path_list=paths, is_last=len(list(self.parent.glob("*"))) == 1)
        return paths

    @property
    def formatted_paths(self) -> list[str]:
        """Converts the paths to strings formatted with folder structure characters."""
        str_list = []
        for path, is_last in self.paths:
            depth = len(path.parts) - 1
            prefix = "└── " if is_last else "├── " if depth else ""
            if depth:
                prefix = ((depth - 1) * "│   ") + prefix
            suffix = self.dir_token if self.parent.joinpath(path).is_dir() else ""
            str_list.append(f"{prefix}{path.name}{suffix}")
        return str_list

    def plot(self) -> None:
        """Print out the paths."""
        print("\n".join(self.formatted_paths))


if __name__ == "__main__":
    my_path = Path(__file__).parents[0]
    TreeBuilder(root=my_path, omit_list=["__pycache__", ".DS_Store"]).plot()
