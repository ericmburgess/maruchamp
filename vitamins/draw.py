"""Convenience functions for rendering to the screen. There is no need to call
`begin_rendering` or `end_rendering`.

.. note:: The `color` parameter

    Colors are given as strings. The following are available:

    - black
    - white
    - gray
    - blue
    - red
    - green
    - lime
    - yellow
    - orange
    - cyan
    - pink
    - purple
    - teal

    If any other string (or no string) is given, the default `white` will be used.
"""

import time
from typing import List

from rlbot.utils.rendering.rendering_manager import RenderingManager

from vitamins.geometry import Vec3, Line

renderer: RenderingManager = None
colors = {}

white = None

flat_z = Vec3(z=20)


def set_renderer(rd: RenderingManager):
    global renderer, white
    renderer = rd


def get_color(name: str = ""):
    return getattr(renderer, name, renderer.white)()


def line_3d(start: Vec3, end: Vec3, color: str = ""):
    """Draw a 3D line between two locations with the given color.

    :param start: start location
    :param end: end location
    :param color: string naming the color
    :return: None
    """
    renderer.draw_line_3d(start, end, get_color(color))


def line_flat(start: Vec3, end: Vec3, color: str = ""):
    """Draw a line in 3D space which is confined to ground level (z=20 units, to
    prevent the line being hidden by grass or other ground decorations).

    :param start: start location
    :param end: end location
    :param color: string naming the color
    :return: None
    """
    renderer.draw_line_3d(start.flat() + flat_z, end.flat() + flat_z, get_color(color))


def polyline_3d(locations: List[Vec3], color: str = ""):
    """Draw a series of lines between a list of 3D positions in the given color.

    :param locations: A list of at least two 3D points
    :param color: Color name
    :return: None
    """
    renderer.draw_polyline_3d(locations, get_color(color))


def point(loc: Vec3, size: int = 10, color: str = ""):
    """Draw a point (actually a square) at the given location in 3D space.

    :param loc: Where to draw the point
    :param size: Side length of the square
    :param color: Color name
    :return: None
    """
    col = get_color(color)
    renderer.draw_rect_3d(loc, size, size, True, col, True)


def rect_3d(
    loc: Vec3, width: int, height: int, color: str = "", centered: bool = False
):
    col = get_color(color)
    renderer.draw_rect_3d(loc, width, height, True, col, centered)


def rect_2d(
    x: int, y: int, width: int, height: int, filled: bool = True, color: str = ""
):
    col = get_color(color)
    renderer.draw_rect_2d(x, y, width, height, filled, col)


def line_2d(x1: int, y1: int, x2: int, y2: int, color: str = ""):
    col = get_color(color)
    renderer.draw_line_2d(x1, y1, x2, y2, col)


def cross(loc: Vec3, length: int = 15, thickness: int = 3, color: str = ""):
    """Draw a cross (plus shape) at the specified location in 3D space.

    :param loc: Where to draw the point
    :param length: Length of the cross segments
    :param thickness: Thickness of the cross segments
    :param color: Color name
    :return: None
    """
    col = get_color(color)
    renderer.draw_rect_3d(loc, thickness, length, True, col, True)
    renderer.draw_rect_3d(loc, length, thickness, True, col, True)


def text(x: int, y: int, size: int = 1, text: str = "", color: str = ""):
    """Draw a string in 2D space (i.e. to a position on the screen, not in the world.)

    :param x,y: Where on screen to draw the text
    :param size: Font size (1=normal, 2=double, etc.)
    :param text: Text to draw
    :param color: Color name
    :return: None
    """
    renderer.draw_string_2d(x, y, size, size, text, get_color(color))


def text_3d(location, size: int = 1, text: str = "", color: str = ""):
    """Draw a string in 3D space.

    :param location: Where in world space to draw the text
    :param size: Font size (1=normal, 2=double, etc.)
    :param text: Text to draw
    :param color: Color name
    :return: None
    """
    renderer.draw_string_3d(location, size, size, text, get_color(color))


def line(line: Line, color: str = "", bump_color: str = ""):
    if bump_color == "":
        bump_color = color
    bumps = 5
    bump_spd = 5000
    length = 20000
    bump_period = length / (bumps * bump_spd)
    height = Vec3(z=20)
    start = line.base_point - line.direction * length / 2 + height
    end = line.base_point + line.direction * length / 2 + height
    line_3d(start, end, color)
    for i in range(bumps):
        t = (i + (time.time() / bump_period) % 1) * length / bumps
        point(start + t * line.direction, size=7, color=bump_color)


def path(points, line_color="", point_color=""):
    if point_color == "":
        point_color = line_color
    prev_pt = None
    h = Vec3(z=20)
    for pt in points:
        if prev_pt is not None:
            line_3d(prev_pt + h, pt + h, line_color)
        point(pt, size=10, color=point_color)
        prev_pt = pt
