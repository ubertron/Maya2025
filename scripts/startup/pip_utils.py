import hashlib
import logging
import os
import shutil

from core.core_paths import SITE_PACKAGES, MAYA_INTERPRETER_PATH, MAYA_REQUIREMENTS
from maya_tools.robotools_utils import MAYA_CONFIG


def install_requirements():
    """
    Install requirements to the site-packages directory
    @return:
    """
    if  check_requirements_hash() is False or not SITE_PACKAGES.exists():
        SITE_PACKAGES.mkdir(exist_ok=True)
        cmd = f'{MAYA_INTERPRETER_PATH} -m pip install -r {MAYA_REQUIREMENTS} -t {SITE_PACKAGES} --upgrade'
        logging.debug(f'Terminal command: {cmd}')
        os.system(cmd)
        installed = [x.strip() for x in open(MAYA_REQUIREMENTS, 'r').readlines()]
        logging.info(f'>>> Packages installed: {", ".join(installed)}')


def uninstall_requirements():
    """
    Uninstall requirements and delete site-packages directory
    """
    if SITE_PACKAGES.exists():
        cmd = f'{MAYA_INTERPRETER_PATH} -m pip uninstall -r {MAYA_REQUIREMENTS}'
        os.system(cmd)
        shutil.rmtree(SITE_PACKAGES)


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
    saved_hash = MAYA_CONFIG.get(section=modules_key, option=requirements_key)
    MAYA_CONFIG.set(section=modules_key, option=requirements_key, value=new_hash, save=True)

    return new_hash == saved_hash
