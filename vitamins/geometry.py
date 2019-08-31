"""geometry.py -- like it says
"""
import math


class Vec3:
    """Remember that the in-game axis are left-handed.

    When in doubt visit the wiki: https://github.com/RLBot/RLBot/wiki/Useful-Game-Values
    """

    def __init__(self, x: object = 0, y: object = 0, z: object = 0) -> object:
        """ Create a new Vec3. The x component can alternatively be another vector with
        an x, y, and z component, in which case the created vector is a copy of the
        given vector and the y and z parameter is ignored. Examples:

        a = Vec3(1, 2, 3)

        b = Vec3(a)
        """

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

    def flat(self) -> "Vec3":
        """Returns a new Vec3 that equals this Vec3 but projected onto the ground plane.
        I.e. where z=0.
        """
        return Vec3(self.x, self.y, 0)

    def length(self) -> float:
        """Returns the length of the vector. Also called magnitude and norm."""
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def to(self, other: "Vec3") -> "Vec3":
        return other - self

    def dist(self, other: "Vec3") -> float:
        """Returns the distance between this vector and another vector using pythagoras.
        """
        return (self - other).length()

    def normalized(self) -> "Vec3":
        """Returns a vector with the same direction but a length of one."""
        return self / self.length()

    def rescale(self, new_len: float) -> "Vec3":
        """Returns a vector with the same direction but a different length."""
        return new_len * self.normalized()

    def dot(self, other: "Vec3") -> float:
        """Returns the dot product."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def ndot(self, other: "Vec3") -> float:
        """Returns the dot product after normalizing both vectors."""
        return self.normalized().dot(other.normalized())

    def cross(self, other: "Vec3") -> "Vec3":
        """Returns the cross product."""
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def ang_to(self, ideal: "Vec3") -> float:
        """Returns the angle to the ideal vector. Angle will be between 0 and pi."""
        cos_ang = self.dot(ideal) / (self.length() * ideal.length())
        return math.acos(cos_ang)

    def yaw_to(self, other: "Vec3") -> float:
        """Returns the signed angle to the other vector."""
        return angle_diff(math.atan2(-self.x, self.y), math.atan2(-other.x, other.y))

    def proj(self, other: "Vec3") -> "Vec3":
        other_dir = other.normalized()
        return self.dot(other_dir) * other_dir

    def decompose(self, other: "Vec3") -> ("Vec3", "Vec3"):
        other_dir = other.normalized()
        proj = self.dot(other_dir) * other_dir
        perp = self - proj
        return proj, perp

    def lerp(self, other: "Vec3", t: float) -> "Vec3":
        """Linearly interpolate beween self and `other`."""
        return self + t * (self.to(other))

    def midpoint(self, other: "Vec3") -> "Vec3":
        return self.lerp(other, 1 / 2)

    def nearest(self, *others: "Vec3", n=1):
        """Return the 'n' nearest vectors from `others`."""
        dists = [(self.dist(v), v) for v in others]
        return [pair[1] for pair in sorted(dists)[:n]]

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

        self.forward = Vec3(cp * cy, cp * sy, sp)
        self.right = Vec3(cy * sp * sr - cr * sy, sy * sp * sr + cr * cy, -cp * sr)
        self.up = Vec3(-cr * cy * sp - sr * sy, -cr * sy * sp + sr * cy, cp * cr)


def find_correction(current: Vec3, ideal: Vec3) -> float:
    """Finds the angle from current to ideal vector in the xy-plane. Angle will be
    between -pi and +pi. The in-game axes are left handed, so we use -x.
    """
    current_in_radians = math.atan2(current.y, -current.x)
    ideal_in_radians = math.atan2(ideal.y, -ideal.x)
    diff = ideal_in_radians - current_in_radians
    # Make sure that diff is between -pi and +pi.
    if abs(diff) > math.pi:
        if diff < 0:
            diff += 2 * math.pi
        else:
            diff -= 2 * math.pi
    return -diff


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

    def __init__(self, pos: Vec3, dir: Vec3):
        self.pos = pos.flat()
        self.dir = dir.flat().normalized()

    def offset(self, loc: Vec3) -> Vec3:
        """Returns the shortest vector from `loc` to a point on the Line."""
        _, perp = loc.flat().to(self.pos).decompose(self.dir)
        return perp

    def nearest_point(self, loc: Vec3) -> Vec3:
        """Return the nearest point on this line to the given point."""
        return loc + self.offset(loc)

    def intersection(self, other: "Line") -> Vec3:
        """Intersection of two Lines. Exists and is unique unless lines are parallel."""
        if abs(self.dir.dot(other.dir)) > 0.999:
            return None
        perp = self.offset(other.pos)
        toward = other.dir.proj(perp)
        plen = math.copysign(perp.length(), other.dir.dot(perp))
        return other.pos + other.dir * plen / toward.length()
