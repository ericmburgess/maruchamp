"""geometry.py -- like it says
"""
import math


class Vec3:
    """Remember that the in-game axis are left-handed.

    When in doubt visit the wiki: https://github.com/RLBot/RLBot/wiki/Useful-Game-Values
    """

    def __init__(self, x: object = 0, y: object = 0, z: object = 0) -> object:
        """
        Create a new Vec3. The x component can alternatively be another vector with an
        x, y, and z component, in which case the created vector is a copy of the given
        vector and the y and z parameter is ignored. Examples:

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

    def __getitem__(self, item: int):
        return (self.x, self.y, self.z)[item]

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)

    def __mul__(self, scale: float) -> "Vec3":
        return Vec3(self.x * scale, self.y * scale, self.z * scale)

    def __rmul__(self, scale):
        return self * scale

    def __truediv__(self, scale: float) -> "Vec3":
        scale = 1 / float(scale)
        return self * scale

    def __str__(self):
        return "Vec3(" + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + ")"

    def flat(self):
        """Returns a new Vec3 that equals this Vec3 but projected onto the ground plane.
        I.e. where z=0.
        """
        return Vec3(self.x, self.y, 0)

    def length(self):
        """Returns the length of the vector. Also called magnitude and norm."""
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def dist(self, other: "Vec3") -> float:
        """Returns the distance between this vector and another vector using pythagoras.
        """
        return (self - other).length()

    def normalized(self):
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

    def proj(self, other: "Vec3") -> "Vec3":
        other_dir = other.normalized()
        return self.dot(other_dir) * other_dir

    def decompose(self, other: "Vec3"):
        other_dir = other.normalized()
        proj = self.dot(other_dir) * other_dir
        perp = self - proj
        return proj, perp


class Orientation:
    """
    This class describes the orientation of an object from the rotation of the object.
    Use this to find the direction of cars: forward, right, up.
    It can also be used to find relative locations.
    """

    def __init__(self, rotation):
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


# Sometimes things are easier, when everything is seen from your point of view.
# This function lets you make any location the center of the world.
# For example, set center to your car's location and ori to your car's orientation, then
# the target will be relative to your car!
def relative_location(center: Vec3, ori: Orientation, target: Vec3) -> Vec3:
    """Returns target as a relative location from center's point of view, using the
    given orientation. The components of the returned vector describes:
        x: how far in front
        y: how far right
        z: how far above
    """
    x = (target - center).dot(ori.forward)
    y = (target - center).dot(ori.right)
    z = (target - center).dot(ori.up)
    return Vec3(x, y, z)


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
