"""draw.py -- convenience routines for rendering."""
import time

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


def line_3d(vec1: Vec3, vec2: Vec3, color: str = ""):
    renderer.draw_line_3d(vec1, vec2, get_color(color))


def line_flat(vec1: Vec3, vec2: Vec3, color: str = ""):
    renderer.draw_line_3d(vec1.flat() + flat_z, vec2.flat() + flat_z, get_color(color))


def polyline_3d(locations, color: str = ""):
    renderer.draw_polyline_3d(locations, get_color(color))


def point(loc: Vec3, size: int = 10, color: str = ""):
    col = get_color(color)
    renderer.draw_rect_3d(loc, size, size, True, col, True)


def cross(loc: Vec3, length: int = 15, thickness: int = 3, color: str = ""):
    col = get_color(color)
    renderer.draw_rect_3d(loc, thickness, length, True, col, True)
    renderer.draw_rect_3d(loc, length, thickness, True, col, True)


def text(x: int, y: int, size: int = 1, text: str = "", color: str = ""):
    renderer.draw_string_2d(x, y, size, size, text, get_color(color))


def text_3d(location, size: int = 1, text: str = "", color: str = ""):
    renderer.draw_string_3d(location, size, size, text, get_color(color))


def line(line: Line, color: str = "", bump_color: str = ""):
    if bump_color == "":
        bump_color = color
    bumps = 5
    bump_spd = 5000
    length = 20000
    bump_period = length / (bumps * bump_spd)
    height = Vec3(z=20)
    start = line.pos - line.dir * length / 2 + height
    end = line.pos + line.dir * length / 2 + height
    line_3d(start, end, color)
    for i in range(bumps):
        t = (i + (time.time() / bump_period) % 1) * length / bumps
        point(start + t * line.dir, size=7, color=bump_color)


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
