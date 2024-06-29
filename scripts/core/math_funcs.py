import numpy as np
import math
import logging
import pyperclip

from typing import Sequence, Optional

from core.point_classes import Point2, Point3, Point3Pair, Y_AXIS, X_AXIS, Z_AXIS

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


IDENTITY_MATRIX: np.array = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])


def interpolate_linear(input_range: Point2, output_range: Point2, value: float) -> float:
    """
    Maps a value from an input range to a corresponding output range
    :param input_range:
    :param output_range:
    :param value:
    :return:
    """
    input_size = input_range.y - input_range.x
    output_size = output_range.y - output_range.x
    coefficient = (value - input_range.x) / input_size
    mapped_value = output_range.x + output_size * coefficient

    return mapped_value


def get_midpoint(points: Sequence[Point3]) -> Point3:
    """
    Gets the midpoint from a list of points
    :param points:
    :return:
    """
    x = sum(item.x for item in points) / len(points)
    y = sum(item.y for item in points) / len(points)
    z = sum(item.z for item in points) / len(points)

    return Point3(x, y, z)


def normalize_vector(input_vector: Point3):
    """
    Convert to a vector with a magnitude of 1
    :param input_vector:
    :return:
    """
    assert input_vector != Point3(0, 0, 0), 'Invalid vector'
    result = np.array(input_vector.values) / np.sqrt(np.sum(np.array(input_vector.values) ** 2))

    return Point3(*result)


def dot_product(vector_a: Point3, vector_b: Point3, normalize: bool = True) -> int:
    """
    Returns an integer which indicates whether two vectors are parallel

    :param vector_a:
    :param vector_b:
    :param normalize:
    :return:
    """
    if normalize:
        vector_a = normalize_vector(vector_a)
        vector_b = normalize_vector(vector_b)

    return np.dot(vector_a.values, vector_b.values)


def angle_between_two_vectors(vector_a: Point3, vector_b: Point3, ref_axis: Optional[Point3] = None):
    """
    θ = acos [(a · b) / (| a | | b |)]
    :param vector_a:
    :param vector_b:
    :param ref_axis: provide a reference axis to get a signed result
    """
    magnitude_product = vector_a.magnitude * vector_b.magnitude
    angle = math.acos(dot_product(vector_a=vector_a, vector_b=vector_b, normalize=False) / magnitude_product)

    return -angle if ref_axis and dot_product(vector_a, ref_axis) < 0 else angle


def cross_product(vector_a: Point3, vector_b: Point3, normalize: bool = True):
    """
    The cross product a × b is defined as a vector c that is perpendicular (orthogonal) to both a and b,
    with a direction given by the right-hand rule and a magnitude equal to the area of the parallelogram that the
    vectors span.
    :param vector_a:
    :param vector_b:
    :param normalize:
    :return:
    """
    result = Point3(*np.cross(vector_a.values, vector_b.values))

    return normalize_vector(result) if normalize else result


def vector_to_euler_angles(vector: Point3) -> Point3:
    """
    Converts a vector to Euler angles
    Note, this is for Y up Maya right-handed coordinate system
    The returned Point3 is of the form Point3(x, y, 0) with a zero z component
    The x_angle tilts vector with respect to the Y-axis
    The y-angle is determined as the angle of the Y-rotation the Z-axis, so the y-component is disregarded
    The y-angle has to be signed and that is determined by the dot product with the X-axis
    :param vector:
    :return:
    """
    x_angle = angle_between_two_vectors(vector_a=vector, vector_b=Y_AXIS)
    flattened_y = Point3(vector.x, 0, vector.z)
    y_angle = angle_between_two_vectors(vector_a=flattened_y, vector_b=Z_AXIS, ref_axis=X_AXIS)

    return Point3(radians_to_degrees(x_angle), radians_to_degrees(y_angle), 0)


def get_normal_vector(a: Point3, b: Point3, c: Point3) -> Point3:
    """
    Gets a normal vector from three points
    :param a:
    :param b:
    :param c:
    :return:
    """
    vector_a = Point3Pair(a, b).delta
    vector_b = Point3Pair(a, c).delta

    return cross_product(vector_a, vector_b)


def radians_to_degrees(x: float) -> float:
    """
    Convert radians to degrees
    :param x:
    :return:
    """
    return math.degrees(x)


def degrees_to_radians(degrees: float):
    """
    Convert degrees to radians
    :param degrees:
    :return:
    """
    return (degrees * math.pi) / 180.0


def get_vector(point_a: Point3, point_b: Point3):
    return Point3(*[point_a.values[i] - point_b.values[i] for i in range(3)])


def rotate_x(matrix, angle):
    rotation_matrix = np.array([[1, 0, 0, 0],
                                [0, np.cos(angle), np.sin(angle), 0],
                                [0, -np.sin(angle), np.cos(angle), 0],
                                [0, 0, 0, 1]])
    return np.dot(rotation_matrix, matrix)


def rotate_y(matrix, angle):
    rotation_matrix = np.array([[np.cos(angle), 0, -np.sin(angle), 0],
                                [0, 1, 0, 0],
                                [np.sin(angle), 0, np.cos(angle), 0],
                                [0, 0, 0, 1]])
    return np.dot(rotation_matrix, matrix)


def rotate_z(matrix, angle):
    rotation_matrix = np.array([[np.cos(angle), -np.sin(angle), 0, 0],
                                [np.sin(angle), np.cos(angle), 0, 0],
                                [0, 0, 1, 0],
                                [0, 0, 0, 1]])
    return np.dot(rotation_matrix, matrix)


def translation(matrix, value: Point3):
    translation_matrix = np.array([[1, 0, 0, value.x],
                                   [0, 1, 0, value.y],
                                   [0, 0, 1, value.z],
                                   [0, 0, 0, 1]])
    return np.dot(translation_matrix, matrix)


def flatten_matrix(matrix: np.array):
    return [x for y in matrix for x in y]


def get_point_position_on_ellipse(degrees: float, ellipse_radius_pair: Point2) -> Point2:
    """
    Get the position of a point on an ellipse
    :param degrees:
    :param ellipse_radius_pair:
    :return:
    """
    degrees = degrees % 360
    x_size, y_size, = ellipse_radius_pair.list

    if degrees == 0:
        return Point2(x_size, 0)

    radians = degrees_to_radians(degrees)
    tan_theta_squared = math.tan(radians) ** 2
    x_value = x_size * y_size / (math.sqrt(y_size ** 2 + x_size ** 2 * tan_theta_squared))
    y_value = x_size * y_size / (math.sqrt(x_size ** 2 + (y_size ** 2 / tan_theta_squared)))

    if math.pi/2 < radians < 3 * math.pi/2:
        x_value = - x_value

    if math.pi < radians < 2 * math.pi:
        y_value = - y_value

    return Point2(x_value, y_value)


def get_point_normal_angle_on_ellipse(point: Point2, ellipse_radius_pair: Point2):
    """
    theta = atan2(2y/semiminorradius, x/semimajorradius)
    :param point:
    :param ellipse_radius_pair:
    :return:
    """
    radians = math.atan2(-(ellipse_radius_pair.y ** 2) * point.x, (ellipse_radius_pair.x ** 2 * point.y))

    return radians_to_degrees(radians)


if __name__ == '__main__':
    print(interpolate_linear(Point2(0, 1), output_range=Point2(0, 100), value=0.5))
