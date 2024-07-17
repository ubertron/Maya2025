import numpy as np
from random import uniform
from importlib import reload

from core.point_classes import Point3, Y_AXIS
from core.math_funcs import get_midpoint, vector_to_euler_angles, get_average_normal_from_points, dot_product
from typing import Sequence


def test_func():
    # generate some random test points
    m = 40  # number of points
    delta = 0.01  # size of random displacement
    origin = np.random.rand(3, 1)  # random origin for the plane
    basis = np.random.rand(3, 2)  # random basis vectors for the plane
    coefficients = np.random.rand(2, m)  # random coefficients for points on the plane

    # generate random points on the plane and add random displacement
    points = basis @ coefficients + np.tile(origin, (1, m)) + delta * np.random.rand(3, m)
    # for point in points:
    #     print(point)

    # now find the best-fitting plane for the test points

    # subtract out the centroid and take the SVD
    svd = np.linalg.svd(points - np.mean(points, axis=1, keepdims=True))

    # Extract the left singular vectors
    left = svd[0]
    print(left[:, -1])


def test_func_2():
    num_points: int = 20
    points = [Point3(uniform(-10, 10), uniform(-10, 10), uniform(-10, 10)) for _ in range(num_points)]
    average_normal = get_average_normal_from_points(points=points)

    euler_rotation = vector_to_euler_angles(average_normal)
    print(f'Average normal is {average_normal}')
    print(f'Euler rotation is {euler_rotation}')
    print(f'Midpoint = {get_midpoint(points)}')
    print(f'Y Axis DP is {dot_product(Y_AXIS, average_normal)}')


def get_average_normal_from_points_(points: Sequence[Point3]) -> Point3:
    """
    Finds the average normal of the plane matching a set of arbitrary points
    :param points:
    :return:
    """
    point_np_array = np.empty([3, len(points)])

    for i in range(len(points)):
        for j in range(3):
            point_np_array[j][i] = points[i].values[j]

    for x in point_np_array:
        print(x)

    # Subtract out the centroid and take the SVD
    singular_value_decomposition = np.linalg.svd(point_np_array - np.mean(point_np_array, axis=1, keepdims=True))

    # Extract the left singular vectors
    left = singular_value_decomposition[0]

    return Point3(*left[:, -1])


if __name__ == '__main__':
    test_func_2()

