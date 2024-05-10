import configparser
import hashlib

from pathlib import Path
from core.config_utils import MayaConfig

PROJECT_ROOT: Path = Path(__file__).parents[1]
MAYA_REQUIREMENTS: Path = PROJECT_ROOT.joinpath('maya_requirements.txt')


def check_requirements_hash() -> bool:
    """
    Compares the current requirements with the previously used file by comparing hash values
    :return:
    """
    modules_key = 'MODULES'
    requirements_key = 'REQUIREMENTS'
    sha256 = hashlib.sha256()

    with open(MAYA_REQUIREMENTS.as_posix(), 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256.update(byte_block)

    new_hash = sha256.hexdigest()
    config = MayaConfig()
    saved_hash = config.get(section=modules_key, option=requirements_key)
    config.set(section=modules_key, option=requirements_key, value=new_hash, save=True)

    return new_hash == saved_hash


if __name__ == '__main__':
    # print(PROJECT_ROOT)
    # print(MAYA_REQUIREMENTS.exists())
    result = check_requirements_hash()
    print(result)
