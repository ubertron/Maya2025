"""Window Creator."""
import logging

from maya_tools.utilities.architools.arch_creator import ArchCreator
from core.logging_utils import get_logger

LOGGER = get_logger(name=__name__, level=logging.DEBUG)


class WindowCreator(ArchCreator):
    def __init__(self):
        super().__init__()
        LOGGER.debug(">>> Initializing WindowCreator")

    def initialize_arch_data(self):
        LOGGER.debug(">>> Validating data")
        self.data = TEST_WINDOW_DATA

    def create(self):
        pass


if __name__ == "__main__":
    window_creator = WindowCreator()
    print(window_creator.data)