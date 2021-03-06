"""
SakuyaEngine // GameDen // GameDen Rewrite (c) 2020-2021 Andrew Hong
This code is licensed under GNU LESSER GENERAL PUBLIC LICENSE (see LICENSE for details)
"""
from __future__ import annotations
from typing import Tuple, List, Union

import math
import pygame

from .errors import NegativeSpeedError

__all__ = [
    "vector2_ratio_xy",
    "vector2_ratio_yx",
    "get_angle",
    "move_toward",
    "raycast",
    "collide_segments",
    "rect_to_lines",
]

vector2 = Union[pygame.Vector2, Tuple[float, float]]


def vector2_ratio_xy(vector: vector2) -> float:
    return vector.x / vector.y


def vector2_ratio_yx(vector: vector2) -> float:
    return vector.y / vector.x


def get_angle(origin: vector2, target: vector2) -> float:
    """Returns an angle in radians of the object to look at from the origin point

    Parameters:
        origin: The original point.
        target: The target point.

    """
    distance = target - origin
    return math.atan2(distance.y, distance.x)


def move_toward(origin: float, target: float, speed: float) -> float:
    """Moves towards the origin to the target by speed.

    Must put in a loop until it's reach its goal.

    Parameters:
        origin: The first point.
        target: The target point.
        speed: The movement speed.

    """
    if speed < 0:
        raise NegativeSpeedError

    if abs(target - origin) <= speed:
        return target

    if target - origin > speed:
        return origin + speed

    if target - origin < speed:
        return origin - speed


def eval_segment_intersection(
    point1: vector2,
    point2: vector2,
    point3: vector2,
    point4: vector2,
) -> pygame.Vector2:
    """Evaluates if 2 line segments collide with each other.

    Parameters:
        point1: The starting point of line 1.
        point2: The ending point of line 1.
        point3: The starting point of line 2.
        point4: The ending point of line 2.

    Returns:
        Line 1's intersecting point on line 2.

    """
    x1, y1 = point1
    x2, y2 = point2
    x3, y3 = point3
    x4, y4 = point4

    dem = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if dem == 0:
        return point2

    t = (x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)
    u = (x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)
    t /= dem
    u /= dem
    if 0 < t < 1 and 0 < u < 1:
        return pygame.Vector2(x3 + u * (x4 - x3), y3 + u * (y4 - y3))
    else:
        return point2


def raycast(
    coord1: pygame.Vector2, coord2: pygame.Vector2, walls: List[Tuple(float, float)]
):
    """Casts a ray from coord1 to coord2.

    Parameters:
        coord1: Starting position.
        coord2: End position.
        walls: List of tuples with 2 floats.

    Returns:
        pygame.Vector2: Finalized point (coord2 if no collision detected).

    """
    x1, y1 = coord1
    x2, y2 = coord2
    line_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    highest_point = coord2
    sort_point_length = line_length
    for wall in walls:
        c = eval_segment_intersection(coord1, coord2, wall[0], wall[1])
        c_length = math.sqrt((x1 - c[0]) ** 2 + (y1 - c[1]) ** 2)
        if sort_point_length > c_length:
            highest_point = c
            sort_point_length = c_length

    return pygame.Vector2(highest_point)


def collide_segments(
    point1,
    point2,
    point3,
    point4,
):
    def ccw(a, b, c):
        return (c.y - a.y) * (b.x - a.x) > (b.y - a.y) * (c.x - a.x)

    return ccw(point1, point3, point4) != ccw(point2, point3, point4) and ccw(
        point1, point2, point3
    ) != ccw(point1, point2, point4)


def rect_to_lines(
    rect: pygame.Rect,
) -> List[vector2, vector2, vector2, vector2]:
    return [
        (rect.bottomleft, rect.bottomright),
        (rect.bottomleft, rect.topleft),
        (rect.bottomright, rect.topright),
        (rect.topleft, rect.topright),
    ]
