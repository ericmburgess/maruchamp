"""draw.py -- convenience routines for rendering."""

from rlbot.utils.rendering.rendering_manager import RenderingManager

from vitamins.geometry import Vec3

renderer: RenderingManager = None
colors = {}

white = None


def set_renderer(rd: RenderingManager):
    global renderer, white
    renderer = rd


def get_color(name: str = None):
    return getattr(renderer, name, renderer.white)()


def line_3d(vec1: Vec3, vec2: Vec3, color: str = None):
    renderer.draw_line_3d(vec1, vec2, get_color(color))


def cross(loc: Vec3, length: int = 15, thickness: int = 3, color: str = None):
    col = get_color(color)
    renderer.draw_rect_3d(loc, thickness, length, True, col, True)
    renderer.draw_rect_3d(loc, length, thickness, True, col, True)
