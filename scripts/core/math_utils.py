import numpy as np
import math
import logging
import pyperclip

# from scipy.linalg import expm, norm
from typing import Sequence, Optional

from core.point_classes import Point2, Point3, Point3Pair, Y_AXIS, X_AXIS, Z_AXIS, NEGATIVE_Y_AXIS, NEGATIVE_X_AXIS, \
    NEGATIVE_Z_AXIS, ZERO3

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


IDENTITY_MATRIX: np.array = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])


def calculate_bounds_with_y_offset(points: Point3Pair, y_offset: float) -> Point3Pair:
    """
    Rotate a pair of points about the Y-axis (right-handed, Y-up), then calculate the size
    Coordinate system (right-handed, Y-up). (i.e. Maya, Unity)

    :param points: Point3Pair
    :param y_offset: Rotation angle in degrees
    :return: Size: Point3
    """
    ref_point = points.delta

    # Convert degrees to radians
    theta = math.radians(y_offset)

    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    rotated = Point3(
        ref_point.x * cos_t + ref_point.z * sin_t,
        ref_point.y,
        -ref_point.x * sin_t + ref_point.z * cos_t)

    return Point3Pair(ZERO3, rotated)


def calculate_size_with_y_offset(points: Point3Pair, y_offset: float) -> Point3:
    """
    Rotate a pair of points about the Y-axis (right-handed, Y-up), then calculate the size
    Coordinate system (right-handed, Y-up). (i.e. Maya, Unity)

    :param points: Point3Pair
    :param y_offset: Rotation angle in degrees
    :return: Size: Point3
    """
    return calculate_bounds_with_y_offset(points=points, y_offset=y_offset).size


def get_bounds_from_points(points: list[Point3], y_offset: float = 0.0) -> Point3Pair:
    if y_offset:
        rotated = []
        for x in points:
            rotated.append(rotate_point_about_y(point=x, y_rotation=y_offset))
        points = rotated
    minimum_point = Point3(*[min(point.values[i] for point in points) for i in range(3)])
    maximum_point = Point3(*[max(point.values[i] for point in points) for i in range(3)])
    return Point3Pair(minimum_point, maximum_point)


def get_midpoint_from_point_list(points: Sequence[Point3]) -> Point3:
    """
    Gets the midpoint from a list of points
    :param points:
    :return:
    """
    x = sum(item.x for item in points) / len(points)
    y = sum(item.y for item in points) / len(points)
    z = sum(item.z for item in points) / len(points)

    return Point3(x, y, z)


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


def normalize_vector(input_vector: Point3):
    """
    Convert to a vector with a magnitude of 1
    :param input_vector:
    :return:
    """
    assert input_vector != Point3(0, 0, 0), 'Invalid vector'
    result = np.array(input_vector.values) / np.sqrt(np.sum(np.array(input_vector.values) ** 2))

    return Point3(*result)


def dot_product(vector_a: Point3, vector_b: Point3, normalize: bool = False) -> int:
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
    vectors span
    :param vector_a:
    :param vector_b:
    :param normalize:
    :return:
    """
    result = Point3(*np.cross(vector_a.values, vector_b.values))

    return normalize_vector(result) if normalize else result


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
    _rotation_matrix = np.array([[1, 0, 0, 0],
                                [0, np.cos(angle), np.sin(angle), 0],
                                [0, -np.sin(angle), np.cos(angle), 0],
                                [0, 0, 0, 1]])
    return np.dot(_rotation_matrix, matrix)


def rotate_y(matrix, angle):
    _rotation_matrix = np.array([[np.cos(angle), 0, -np.sin(angle), 0],
                                [0, 1, 0, 0],
                                [np.sin(angle), 0, np.cos(angle), 0],
                                [0, 0, 0, 1]])
    return np.dot(_rotation_matrix, matrix)


def rotate_z(matrix, angle):
    _rotation_matrix = np.array([[np.cos(angle), -np.sin(angle), 0, 0],
                                [np.sin(angle), np.cos(angle), 0, 0],
                                [0, 0, 1, 0],
                                [0, 0, 0, 1]])
    return np.dot(_rotation_matrix, matrix)


def translation(matrix, value: Point3):
    translation_matrix = np.array([[1, 0, 0, value.x],
                                   [0, 1, 0, value.y],
                                   [0, 0, 1, value.z],
                                   [0, 0, 0, 1]])
    return np.dot(translation_matrix, matrix)


def flatten_matrix(matrix: np.array):
    return [x for y in matrix for x in y]


def get_average_normal_from_points(points: Sequence[Point3]) -> Point3:
    """
    Finds the normal of the plane fitting a set of arbitrary points
    :param points:
    :return:
    """
    point_np_array = np.empty([3, len(points)])

    for i in range(len(points)):
        for j in range(3):
            point_np_array[j][i] = points[i].values[j]

    # Subtract out the centroid and take the SVD
    singular_value_decomposition = np.linalg.svd(point_np_array - np.mean(point_np_array, axis=1, keepdims=True))

    # Extract the left singular vectors
    left = singular_value_decomposition[0]
    normal = Point3(*left[:, -1])

    # Flip if the Y axis is pointing down
    if dot_product(Y_AXIS, normal) < 0:
        normal = rotate_point(point=normal, axis=X_AXIS, theta=np.pi)

    return normal


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


def get_closest_position_on_line_to_point(point: Point3, line: Point3Pair) -> Point3:
    """
    Gets the closest position on a line to a point
    :param point:
    :param line:
    :return:
    """
    normalized_vector = normalize_vector(line.delta)
    point_vector = Point3Pair(line.a, point).delta
    dp = dot_product(point_vector, normalized_vector, normalize=False)

    return Point3Pair(line.a, normalized_vector.multiply(scalar=dp)).sum


def project_point_onto_plane(plane_position: Point3, unit_normal_vector: Point3, point: Point3) -> Point3:
    """
    https://stackoverflow.com/questions/9605556/how-to-project-a-point-onto-a-plane-in-3d
    :param plane_position:
    :param unit_normal_vector:
    :param point:
    """
    # Make a vector from your orig point to the point of interest
    point_vector: Point3 = Point3Pair(plane_position, point).delta

    # Take the dot product of that vector with the unit normal vector
    # dist = vx*nx + vy*ny + vz*nz; dist = scalar distance from point to plane along the normal
    scalar_distance = dot_product(point_vector, unit_normal_vector)

    # Multiply the unit normal vector by the distance, and subtract that vector from your point
    projection_vector = unit_normal_vector.multiply(scalar_distance)

    return Point3Pair(projection_vector, point).delta


def rotate_point(point: Point3, axis: Point3, theta: float, algorithm: bool = False) -> Point3:
    """
    Rotates a vector about an axis
    Both versions work, choose the algorithm
    :param point:
    :param axis:
    :param theta:
    :param algorithm:
    :return:
    """
    if algorithm:
        matrix = expm(np.cross(np.eye(3), np.array(axis.values)/norm(np.array(axis.values)) * theta))
    else:
        matrix = rotation_matrix(axis=axis, theta=theta)

    rotated = np.dot(matrix, np.array(point.values))

    return Point3(*rotated)


def rotate_point_about_y(point: Point3, y_rotation: float) -> Point3:
    """
    Rotates a 3D vector [x, y, z] around the y-axis using a right-hand coordinate system.

    Args:
        point (Point3): The input vector as [x, y, z].
        y_rotation (float): The angle of rotation in degrees (counter-clockwise).

    Returns:
        Point3: The rotated vector as [x', y', z'].
    """
    # Convert angle from degrees to radians for math functions
    angle_radians = math.radians(y_rotation)
    cos_theta = math.cos(angle_radians)
    sin_theta = math.sin(angle_radians)

    # Apply the rotation matrix multiplication:
    x_prime = point.x * cos_theta + point.z * sin_theta
    y_prime = point.y
    z_prime = -point.x * sin_theta + point.z * cos_theta

    return Point3(x_prime, y_prime, z_prime)



def rotation_matrix(axis: Point3, theta: float) -> np.array:
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(np.array(axis.values))
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d

    return np.array([[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                     [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                     [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])


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


if __name__ == '__main__':
    my_points = Point3Pair(ZERO3, Point3(4, 8, 1))
    print(calculate_size_with_y_offset(points=my_points, y_offset=0))
