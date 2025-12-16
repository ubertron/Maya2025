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
    def compact_repr(self) -> str:
        return f'x: {self.x:.2f}, y: {self.y:.2f}, z: {self.z:.2f}'

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

    def within_y_threshold(self, y_value: float, threshold: float = 0.01) -> bool:
        """
        Returns true if the y-values fit within threshold
        :param y_value:
        :param threshold:
        :return:
        """
        return abs(y_value - self.y) <= threshold

    def multiply(self, scalar: float):
        """
        Multiply vector by a scalar value
        :param scalar:
        :return:
        """
        return Point3(*[component * scalar for component in self.values])

    def dot_product(self, point) -> float:
        return sum(self.values[i] * point.values[i] for i in range(3))


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
        return info

    @property
    def compact_repr(self) -> str:
        return f'[{self.a.compact_repr}], [{self.b.compact_repr}]'

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
    def dot_product(self):
        return sum(self.a.values[i] * self.b.values[i] for i in range(3))

    @property
    def midpoint(self) -> Point3:
        return Point3(*[(self.a.values[i] + self.b.values[i]) / 2 for i in range(3)])

    @property
    def minimum(self) -> Point3:
        return Point3(*[min(self.a.values[i], self.b.values[i]) for i in range(3)])

    @property
    def maximum(self) -> Point3:
        return Point3(*[max(self.a.values[i], self.b.values[i]) for i in range(3)])

    @property
    def size(self) -> float:
        return Point3(*[abs(x) for x in self.delta.values])

    @property
    def sum(self) -> Point3:
        return Point3(self.a.x + self.b.x, self.a.y + self.b.y, self.a.z + self.b.z)

    def interpolate(self, value: float):
        """
        Returns a value along the line between points a and b
        :param value:
        :return:
        """
        return Point3(*[self.a.values[i] + value * self.delta.values[i] for i in range(3)])

    def vertices_within_bounds(self, vertices: list[Point3]):
        """Returns true if vertices are within bounds."""
        for v in vertices:
            for axis_index in range(3):
                if v.values[axis_index] < self.a.values[axis_index] or v.values[axis_index] > self.b.values[axis_index]:
                    return False
        return True


POINT2_ORIGIN: Point2 = Point2(0.0, 0.0)
POINT3_ORIGIN: Point3 = Point3(0.0, 0.0, 0.0)
X_AXIS: Point3 = Point3(1.0, 0.0, 0.0)
Y_AXIS: Point3 = Point3(0.0, 1.0, 0.0)
Z_AXIS: Point3 = Point3(0.0, 0.0, 1.0)
NEGATIVE_X_AXIS: Point3 = Point3(-1.0, 0.0, 0.0)
NEGATIVE_Y_AXIS: Point3 = Point3(0.0, -1.0, 0.0)
NEGATIVE_Z_AXIS: Point3 = Point3(0.0, 0.0, -1.0)

if __name__ == '__main__':
    point3_pair = Point3Pair(Point3(1.0, 0.0, 2.0), Point3(0.0, 1.0, 0.0))
    print(point3_pair.minimum)
    print(point3_pair.maximum)