from enum import Enum


class ItemStatus(Enum):
    export = (255, 255, 216)
    exported = (216, 255, 216)
    missing = (255, 216, 216)
    update = (255, 216, 255)
    static = (216, 216, 216)
