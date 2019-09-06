"""vitamins.match.hitbox -- hitbox class and data."""

from functools import partial

from vitamins.geometry import Vec3
from vitamins.match.base import OrientedObject
from vitamins import draw


class Hitbox:
    width: float
    length: float
    height: float
    angle: float  # todo: take this into account
    root_to_front: float
    root_to_top: float
    root_to_side: float
    root_to_back: float

    def __init__(self, car: OrientedObject, width: float):
        self.car = car
        hitbox_class = {
            832: DominusHitbox,
            842: OctaneHitbox,
            846: PlankHitbox,
            805: BreakoutHitbox,
            822: HybridHitbox,
        }.get(int(width * 10), OctaneHitbox)
        self.width = hitbox_class.width
        self.length = hitbox_class.length
        self.height = hitbox_class.height
        self.angle = hitbox_class.angle
        self.root_to_front = hitbox_class.root_to_front
        self.root_to_top = hitbox_class.root_to_top
        self.root_to_side = hitbox_class.root_to_side
        self.root_to_back = hitbox_class.root_to_back

    def __call__(self, corner_str: str, dt: float = 0) -> Vec3:
        return self.location(corner_str, dt)

    @property
    def _fwd(self):
        return self.car.forward * self.root_to_front

    @property
    def _back(self):
        return self.car.backward * self.root_to_back

    @property
    def _left(self):
        return self.car.left * self.root_to_side

    @property
    def _up(self):
        return self.car.up * self.root_to_top

    @property
    def _down(self):
        return self.car.down * (self.height - self.root_to_top)

    def location(self, corner_str: str, dt: float = 0) -> Vec3:
        """Returns a location on the hitbox.
        Args:
            corner_str: Specifies the location on the hibox (see below).
            dt: Estimates the position `dt` seconds into the future (or past if <0).
                This is useful for drawing the hitbox since rendering is a couple
                of frames behind.

        Location specifier:
            FB: front/back
            UD: up/down
            LR: left/right
        Examples:
            FLU = forward left top corner
            FU = center of the top front edge
            U = center of the top face

        Note: The order and case of the letters do not matter. So FRU, URF, urf, rFu
            all refer to the same top-right-front corner of the hitbox.

        Note: "Center" means aligned with the center of rotation. So e.g. RU is closer
            to RUB than to RUF, because the center of rotation for all cars is shifted
            somewhat toward the rear of the hitbox.
        """
        corner_str = corner_str.upper()
        # todo: take angular velocity into account, too:
        pos = self.car.position + dt * self.car.velocity
        if "F" in corner_str:
            pos += self._fwd
        if "B" in corner_str:
            pos += self._back
        if "L" in corner_str:
            pos += self._left
        if "R" in corner_str:
            pos -= self._left
        if "U" in corner_str:
            pos += self._up
        if "D" in corner_str:
            pos += self._down
        return pos

    def draw(self, color: str = "", dt: float = 0):
        """Draw a wireframe hitbox for visualization."""
        c = partial(self.location, dt=dt)
        draw.line_3d(c("blu"), c("flu"), color)
        draw.line_3d(c("bru"), c("fru"), color)
        draw.line_3d(c("bld"), c("fld"), color)
        draw.line_3d(c("brd"), c("frd"), color)
        draw.line_3d(c("flu"), c("fru"), color)
        draw.line_3d(c("fld"), c("frd"), color)
        draw.line_3d(c("blu"), c("bru"), color)
        draw.line_3d(c("bld"), c("brd"), color)
        draw.line_3d(c("fld"), c("flu"), color)
        draw.line_3d(c("frd"), c("fru"), color)
        draw.line_3d(c("bld"), c("blu"), color)
        draw.line_3d(c("brd"), c("bru"), color)


# Specific hitbox data for each car type. Source:
# https://onedrive.live.com/view.aspx?resid=F0182A0BAEBB5DFF!14583&ithint=file%2cxlsx&app=Excel&authkey=!ALu0cMkDZDoWOws


class DominusHitbox(Hitbox):
    width = 83.28
    length = 127.93
    height = 31.30
    angle = -0.96
    root_to_front = 72.96
    root_to_top = 31.40
    root_to_side = 41.64
    root_to_back = 54.96


class OctaneHitbox(Hitbox):
    width = 84.20
    length = 118.01
    height = 36.16
    angle = -0.55
    root_to_front = 72.88
    root_to_top = 38.83
    root_to_side = 42.10
    root_to_back = 45.13


class PlankHitbox(Hitbox):
    width = 84.67
    length = 128.82
    height = 29.39
    angle = -0.34
    root_to_front = 73.42
    root_to_top = 26.79
    root_to_side = 42.34
    root_to_back = 55.40


class BreakoutHitbox(Hitbox):
    width = 80.52
    length = 131.49
    height = 30.30
    angle = -0.98
    root_to_front = 78.25
    root_to_top = 26.90
    root_to_side = 40.26
    root_to_back = 53.25


class HybridHitbox(Hitbox):
    width = 82.19
    length = 127.02
    height = 34.16
    angle = -0.055
    root_to_front = 77.39
    root_to_top = 37.83
    root_to_side = 41.09
    root_to_back = 49.63
