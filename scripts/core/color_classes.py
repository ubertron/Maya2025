from __future__ import annotations
from dataclasses import dataclass
from maya import cmds


@dataclass
class RGBColor:
    r: int
    g: int
    b: int

    @property
    def hex(self) -> str:
        return "#%02x%02x%02x" % self.values
    
    @property
    def normalized(self) -> tuple[float, float, float]:
        return tuple(map(lambda x: x/255, self.values))

    @property
    def values(self):
        return self.r, self.g, self.b


BABY_BLUE = RGBColor(128, 216, 255)
BABY_PINK = RGBColor(255, 192, 192)
CYAN = RGBColor(0, 255, 255)
DEEP_GREEN = RGBColor(0, 160, 0)
GREEN = RGBColor(0, 255, 0)
GREY = RGBColor(128, 128, 128)
LIGHT_GREY = RGBColor(216, 216, 216)
LIME = RGBColor(128, 255, 0)
MAGENTA = RGBColor(255, 0, 255)
MAYA_BLUE = RGBColor(72, 170, 181)
ORANGE = RGBColor(255, 128, 0)
RED = RGBColor(255, 0, 0)
WHITE = RGBColor(255, 255, 255)

if __name__ == "__main__":
    print(BABY_BLUE.normalized, BABY_PINK.values, BABY_BLUE.hex)