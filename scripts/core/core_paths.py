from pathlib import Path


PROJECT_ROOT: Path = Path(__file__).parents[2]
ICONS: Path = PROJECT_ROOT.joinpath('icons')


def icon_path(file_name: str) -> Path:
    return ICONS.joinpath(file_name)


if __name__ == '__main__':
    print(PROJECT_ROOT, PROJECT_ROOT.exists())
    print(icon_path('base_female.png').exists())
