from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ColorRGB:
    r: int
    g: int
    b: int

    @property
    def css(self) -> str:
        return f"rgb({self.r},{self.g},{self.b})"

    @property
    def hex(self) -> str:
        return "#%02x%02x%02x" % self.values
    
    @property
    def normalized(self) -> tuple[float, float, float]:
        return tuple(map(lambda x: x/255, self.values))

    @property
    def values(self):
        return self.r, self.g, self.b


@dataclass
class ColorRGBA:
    r: int
    g: int
    b: int
    a: int

    @property
    def css(self) -> str:
        return f"rgb({self.r},{self.g},{self.b},{self.a})"

    @property
    def hex(self) -> str:
        return "#%02x%02x%02x%02x" % self.values

    @property
    def normalized(self) -> tuple[float, float, float, float]:
        return tuple(map(lambda x: x/255, self.values))

    @property
    def values(self):
        return self.r, self.g, self.b, self.a


BABY_BLUE = ColorRGB(128, 216, 255)
BABY_PINK = ColorRGB(255, 192, 192)
CYAN = ColorRGB(0, 255, 255)
DEEP_GREEN = ColorRGB(0, 160, 0)
GREEN = ColorRGB(0, 255, 0)
GREY = ColorRGB(128, 128, 128)
LIGHT_GREY = ColorRGB(216, 216, 216)
LIME = ColorRGB(128, 255, 0)
MAGENTA = ColorRGB(255, 0, 255)
MAYA_BLUE = ColorRGB(72, 170, 181)
ORANGE = ColorRGB(255, 128, 0)
RED = ColorRGB(255, 0, 0)
WHITE = ColorRGB(255, 255, 255)

if __name__ == "__main__":
    print(BABY_BLUE.normalized, BABY_PINK.values, BABY_BLUE.hex)