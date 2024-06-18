import math
from dataclasses import dataclass


@dataclass
class Point2:
    x: float
    y: float

    def __repr__(self) -> str:
        return f'[{self.x}, {self.y}]'

    @property
    def area(self) -> float:
        return self.x * self.y

    @property
    def values(self) -> tuple[float]:
        return self.x, self.y

    @property
    def list(self) -> list[float]:
        return [self.x, self.y]


@dataclass
class Point3:
    x: float
    y: float
    z: float

    def __repr__(self) -> str:
        return f'[{self.x}, {self.y}, {self.z}]'

    @property
    def volume(self) -> float:
        return self.x * self.y * self.z

    @property
    def values(self) -> tuple[float]:
        return self.x, self.y, self.z

    @property
    def list(self) -> list[float]:
        return [self.x, self.y, self.z]

    @property
    def magnitude(self) -> float:
        return math.sqrt(sum(self.values[i] ** 2 for i in range(3)))


@dataclass
class Point2Pair:
    a: Point2
    b: Point2

    def __repr__(self) -> str:
        return f'{self.a}, {self.b}\nLength: {self.length:.3f}'

    @property
    def length(self) -> float:
        delta_x = self.b.x - self.a.x
        delta_y = self.b.y - self.a.y
        return math.sqrt(sum(x ** 2 for x in (delta_x, delta_y)))

    @property
    def delta(self) -> Point2:
        return Point2(*[self.b.values[i] - self.a.values[i] for i in range(2)])

    def interpolate(self, value: float):
        """
        Returns a value along the line between points a and b
        :param value:
        :return:
        """
        return Point2(*[self.a.values[i] + value * self.delta.values[i] for i in range(2)])


@dataclass
class Point3Pair:
    a: Point3
    b: Point3

    def __repr__(self) -> str:
        info = f'Position: {self.a}, {self.b}\nLength: {self.length:.3f}\nDelta: {self.delta}'
        info += f'\nMidpoint: {self.midpoint}'
        info += f'\nX Angle: {self.x_angle:.3f}'
        info += f'\nY Angle: {self.y_angle:.3f}'
        return info

    @property
    def length(self) -> float:
        delta_x = self.b.x - self.a.x
        delta_y = self.b.y - self.a.y
        delta_z = self.b.z - self.a.z
        return math.sqrt(sum(x ** 2 for x in (delta_x, delta_y, delta_z)))

    @property
    def delta(self) -> Point3:
        return Point3(*[self.b.values[i] - self.a.values[i] for i in range(3)])

    @property
    def midpoint(self) -> Point3:
        return Point3(*[(self.a.values[i] + self.b.values[i]) / 2 for i in range(3)])

    def interpolate(self, value: float):
        """
        Returns a value along the line between points a and b
        :param value:
        :return:
        """
        return Point3(*[self.a.values[i] + value * self.delta.values[i] for i in range(3)])


POINT2_ORIGIN: Point2 = Point2(0.0, 0.0)
POINT3_ORIGIN: Point3 = Point3(0.0, 0.0, 0.0)
X_AXIS: Point3 = Point3(1.0, 0.0, 0.0)
Y_AXIS: Point3 = Point3(0.0, 1.0, 0.0)
Z_AXIS: Point3 = Point3(0.0, 0.0, 1.0)
