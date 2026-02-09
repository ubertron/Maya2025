from __future__ import annotations

import math

from dataclasses import dataclass
from core.core_enums import Side


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
    def list(self) -> list[float]:
        return [self.x, self.y, self.z]

    @property
    def magnitude(self) -> float:
        return math.sqrt(sum(self.values[i] ** 2 for i in range(3)))

    @property
    def normalized(self) -> 'Point3':
        return Point3(self.x / self.magnitude, self.y / self.magnitude, self.z / self.magnitude)

    @property
    def values(self) -> tuple[float]:
        return self.x, self.y, self.z

    @property
    def volume(self) -> float:
        return self.x * self.y * self.z

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
        return (
            f'Position: a- {self.a}, b- {self.b}\n'
            f'Length: {self.length:.3f}\n'
            f'Delta: {self.delta}\n'
            f'Midpoint: {self.center}\n'
            f'Size: {self.size}'
        )

    @property
    def back(self) -> Point3:
        return Point3(self.center.x, self.center.y, self.minimum.z)

    @property
    def bottom(self) -> Point3:
        return Point3(self.center.x, self.minimum.y, self.center.z)

    @property
    def center(self) -> Point3:
        return Point3(*[(self.a.values[i] + self.b.values[i]) / 2 for i in range(3)])

    @property
    def compact_repr(self) -> str:
        return f'[{self.a.compact_repr}], [{self.b.compact_repr}]'

    @property
    def cross_product(self) -> Point3:
        return Point3(
            self.a.y * self.b.z - self.a.z * self.b.y,
            self.a.z * self.b.x - self.a.x * self.b.z,
            self.a.x * self.b.y - self.a.y * self.b.x
        )

    @property
    def delta(self) -> Point3:
        return Point3(*[self.b.values[i] - self.a.values[i] for i in range(3)])

    @property
    def dot_product(self):
        return sum(self.a.values[i] * self.b.values[i] for i in range(3))

    @property
    def front(self) -> Point3:
        return Point3(self.center.x, self.center.y, self.maximum.z)

    @property
    def left(self) -> Point3:
        return Point3(self.minimum.x, self.center.y, self.center.z)

    @property
    def length(self) -> float:
        delta_x = self.b.x - self.a.x
        delta_y = self.b.y - self.a.y
        delta_z = self.b.z - self.a.z
        return math.sqrt(sum(x ** 2 for x in (delta_x, delta_y, delta_z)))

    @property
    def maximum(self) -> Point3:
        return Point3(*[max(self.a.values[i], self.b.values[i]) for i in range(3)])

    @property
    def min_max_vector(self) -> Point3:
        """The vector from the minimum to the maximum point."""
        vector = Point3(*[self.maximum.values[i] - self.minimum.values[i] for i in range(3)])
        return Point3(*[vector.values[i] / vector.magnitude for i in range(3)])

    @property
    def minimum(self) -> Point3:
        return Point3(*[min(self.a.values[i], self.b.values[i]) for i in range(3)])

    @property
    def right(self) -> Point3:
        return Point3(self.maximum.x, self.center.y, self.center.z)

    @property
    def size(self) -> float:
        return Point3(*[abs(x) for x in self.delta.values])

    @property
    def sum(self) -> Point3:
        """Sum of the two vectors."""
        return Point3(self.a.x + self.b.x, self.a.y + self.b.y, self.a.z + self.b.z)

    @property
    def top(self) -> Point3:
        """Position of the top pivot."""
        return Point3(self.center.x, self.maximum.y, self.center.z)

    def get_pivot(self, side: Side) -> Point3:
        """Position of the pivot given by side."""
        # Use .name string keys to avoid module reload issues with enum identity
        pivot_map = {
            Side.bottom.name: self.bottom,
            Side.center.name: self.center,
            Side.top.name: self.top,
            Side.left.name: self.left,
            Side.right.name: self.right,
            Side.front.name: self.front,
            Side.back.name: self.back,
        }
        return pivot_map[side.name]

    def interpolate(self, value: float):
        """
        Returns a value along the line between points a and b
        :param value:
        :return:
        """
        return Point3(*[self.a.values[i] + value * self.delta.values[i] for i in range(3)])

    def vertices_within_bounds(self, vertices: list[Point3]) -> bool:
        """Returns true if vertices are within bounds."""
        for v in vertices:
            for axis_index in range(3):
                if v.values[axis_index] < self.a.values[axis_index] or v.values[axis_index] > self.b.values[axis_index]:
                    return False
        return True


ZERO2: Point2 = Point2(0.0, 0.0)
ZERO3: Point3 = Point3(0.0, 0.0, 0.0)
UNIT2: Point2 = Point2(1.0, 1.0)
UNIT3: Point3 = Point3(1.0, 1.0, 1.0)
X_AXIS: Point3 = Point3(1.0, 0.0, 0.0)
Y_AXIS: Point3 = Point3(0.0, 1.0, 0.0)
Z_AXIS: Point3 = Point3(0.0, 0.0, 1.0)
NEGATIVE_X_AXIS: Point3 = Point3(-1.0, 0.0, 0.0)
NEGATIVE_Y_AXIS: Point3 = Point3(0.0, -1.0, 0.0)
NEGATIVE_Z_AXIS: Point3 = Point3(0.0, 0.0, -1.0)


if __name__ == '__main__':
    point3_pair = Point3Pair(Point3(0.0, 0.0, 0.0), Point3(0.0, 1.0, 10.0))
    # print(point3_pair.minimum)
    # print(point3_pair.maximum)
    # print(Point3Pair(0, 10, 3).normalized)
    min_max_vector = point3_pair.min_max_vector
    print(min_max_vector)
    print(Point3Pair(min_max_vector, X_AXIS).dot_product)
    print(Point3Pair(min_max_vector, Z_AXIS).dot_product)