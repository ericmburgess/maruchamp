"""geometry.py -- like it says
"""
from typing import Any, Tuple
import math


class Vec2:
    """The `Vec2` class provides operations on two-dimensional vectors with `float`
    coordinates.
    """

    def __init__(self, x: object = 0, y: object = 0):
        """Creates a `Vec2` instance, either from coordinates or from a `Vec2` or
        other object which has `x` and `y` attributes."""
        if hasattr(x, "x") and hasattr(x, "y"):
            x, y = x.x, x.y
        self.x, self.y = float(x), float(y)

    def __str__(self):
        return f"Vec2({self.x}, {self.y})"

    def __repr__(self):
        return str(self)

    def rotated(self, theta: float) -> "Vec2":
        return Vec2(
            x=self.x * math.cos(theta) - self.y * math.sin(theta),
            y=self.x * math.sin(theta) + self.y * math.cos(theta),
        )


class Vec3:
    """The `Vec3` class provides operations on three-dimensional vectors with `float`
    coordinates.
    """

    def __init__(self, x: Any = 0, y: float = 0, z: float = 0):
        if hasattr(x, "x"):
            # We have been given a vector. Copy it
            self.x = float(x.x)
            self.y = float(x.y) if hasattr(x, "y") else 0
            self.z = float(x.z) if hasattr(x, "z") else 0
        else:
            self.x = float(x)
            self.y = float(y)
            self.z = float(z)

    def __getitem__(self, item: int) -> float:
        return (self.x, self.y, self.z)[item]

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)

    def __mul__(self, scale: float) -> "Vec3":
        return Vec3(self.x * scale, self.y * scale, self.z * scale)

    def __rmul__(self, scale: float) -> "Vec3":
        return self * scale

    def __truediv__(self, scale: float) -> "Vec3":
        scale = 1 / float(scale)
        return self * scale

    def __str__(self):
        return "Vec3(" + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + ")"

    def __repr__(self):
        return str(self)

    def plane(self, x_dir: "Vec3" = None, y_dir: "Vec3" = None) -> Vec2:
        """Projects onto a plane (the z=0 plane by default), returning a `Vec2`.
        """
        if x_dir is None:
            x_dir = Vec3(1, 0, 0)
        if y_dir is None:
            y_dir = Vec3(0, 1, 0)
        return Vec2(self.dot(x_dir), self.dot(y_dir))

    def flat(self) -> "Vec3":
        """Returns a copy of the vector projected onto the z=0 plane."""
        return Vec3(self.x, self.y, 0)

    def length(self) -> float:
        """Returns the length of the vector. Also called magnitude and norm."""
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def to(self, other: "Vec3") -> "Vec3":
        return other - self

    def distance(self, other: "Vec3") -> float:
        """Returns the distance between this vector and another vector using pythagoras.
        """
        return (self - other).length()

    def normalized(self) -> "Vec3":
        """Returns a vector with the same direction but a length of one."""
        if self.length() == 0:
            return self
        else:
            return self / self.length()

    def rescaled(self, new_len: float) -> "Vec3":
        """Returns a vector with the same direction but a different length."""
        return new_len * self.normalized()

    def dot(self, other: "Vec3") -> float:
        """Returns the dot product."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def ndot(self, other: "Vec3") -> float:
        """Returns the dot product after normalizing both vectors."""
        if self.length() == 0 or other.length == 0:
            return 0
        return self.normalized().dot(other.normalized())

    def cross(self, other: "Vec3") -> "Vec3":
        """Returns the cross product."""
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def direction_to(self, other: "Vec3") -> "Vec3":
        """The direction (normalized vector) from `self` toward `other`."""
        return self.to(other).normalized()

    def ang_to(self, ideal: "Vec3") -> float:
        """Returns the angle to the ideal vector. Angle will be between 0 and pi."""
        cos_ang = self.dot(ideal) / (self.length() * ideal.length())
        return math.acos(cos_ang)

    def yaw_to(self, other: "Vec3") -> float:
        """Returns the signed angle to the other vector."""
        return angle_diff(math.atan2(-self.x, self.y), math.atan2(-other.x, other.y))

    def proj(self, other: "Vec3") -> "Vec3":
        """The projection of `self` onto `other`."""
        other_dir = other.normalized()
        return self.dot(other_dir) * other_dir

    def perp(self, other: "Vec3") -> "Vec3":
        """The component of `self` perpendicular to `other`."""
        return self - self.proj(other)

    def decompose(self, other: "Vec3") -> Tuple["Vec3", "Vec3"]:
        """Returns the tuple (proj, perp)."""
        other_dir = other.normalized()
        proj = self.dot(other_dir) * other_dir
        perp = self - proj
        return proj, perp

    def lerp(self, other: "Vec3", t: float) -> "Vec3":
        """Linearly interpolate beween self and `other`."""
        return self + t * (self.to(other))

    def midpoint(self, other: "Vec3") -> "Vec3":
        return self.lerp(other, 1 / 2)

    def nearest(self, others: ["Vec3"]) -> "Vec3":
        """Return the nearest vector in `others`."""
        min_dist = 1e9
        nearest = None
        for other in others:
            d = self.distance(other)
            if d < min_dist:
                min_dist, nearest = d, other
        return nearest

    def offline(self, other: "Vec3") -> float:
        """Return the distance from `other` to the closest point on the line parallel
        to `self`.
        """
        return (self - self.proj(other)).length()


class Orientation:
    """
    This class describes the orientation of an object from the rotation of the object.
    Use this to find the direction of cars: forward, right, up.
    It can also be used to find relative locations.
    """

    def __init__(self, rotation):
        if isinstance(rotation, Vec3):
            self.yaw, self.roll, self.pitch = rotation
        else:
            self.yaw = float(rotation.yaw)
            self.roll = float(rotation.roll)
            self.pitch = float(rotation.pitch)

        cr = math.cos(self.roll)
        sr = math.sin(self.roll)
        cp = math.cos(self.pitch)
        sp = math.sin(self.pitch)
        cy = math.cos(self.yaw)
        sy = math.sin(self.yaw)

        self.forward: Vec3 = Vec3(cp * cy, cp * sy, sp)
        self.right: Vec3 = Vec3(
            cy * sp * sr - cr * sy, sy * sp * sr + cr * cy, -cp * sr
        )
        self.up: Vec3 = Vec3(-cr * cy * sp - sr * sy, -cr * sy * sp + sr * cy, cp * cr)


def angle_diff(a1: float, a2: float) -> float:
    diff = a2 - a1
    if abs(diff) > math.pi:
        if diff < 0:
            diff += 2 * math.pi
        else:
            diff -= 2 * math.pi
    return diff


class Line:
    """Represents a 2D line on the ground level of the field."""

    def __init__(self, pos: Vec3, direction: Vec3):
        self.base_point = Vec3(pos.x, pos.y, 0.0)
        self.direction = direction.flat().normalized()

    def offset(self, loc: Vec3) -> Vec3:
        """Returns the shortest vector from `loc` to a point on the Line."""
        _, perp = loc.flat().to(self.base_point).decompose(self.direction)
        return perp

    def nearest_point(self, loc: Vec3) -> Vec3:
        """Return the nearest point on this line to the given point."""
        return loc + self.offset(loc)

    def intersection(self, other: "Line") -> Vec3:
        """Intersection of two Lines. Exists and is unique unless lines are parallel."""
        if abs(self.direction.dot(other.direction)) > 1 - 1e-9:
            # If the lines are parallel, just approximate a "point at infinity":
            return other.base_point + other.direction * 1e6
        perp = self.offset(other.base_point)
        toward = other.direction.proj(perp)
        plen = math.copysign(perp.length(), other.direction.dot(perp))
        return other.base_point + other.direction * plen / toward.length()
