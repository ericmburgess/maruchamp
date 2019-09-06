"""vitamins.match.base -- base objects."""

from vitamins.geometry import Vec3, Orientation
from vitamins import math


class Location(Vec3):
    """A position in 3D space together with a velocity."""

    modified: bool = False

    def __init__(self, position: Vec3 = None, velocity: Vec3 = None):
        if position is None:
            position = Vec3(0)
        if velocity is None:
            velocity = Vec3(0)
        super().__init__(position)
        self.velocity = velocity

    @property
    def position(self) -> Vec3:
        return Vec3(self.x, self.y, self.z)

    @position.setter
    def position(self, value: Vec3):
        self.x, self.y, self.z = value
        self.modified = True

    @property
    def speed(self) -> float:
        """Shorthand for `velocity.length()`."""
        return self.velocity.length()

    @property
    def direction(self) -> Vec3:
        """Shorthand for `velocity.normalized()`."""
        return self.velocity.normalized()

    def __add__(self, other) -> "Location":
        if isinstance(other, Location):
            return Location(
                position=self.position + other.position,
                velocity=self.velocity + other.velocity,
            )
        elif isinstance(other, Vec3):
            return Location(position=self.position + other, velocity=self.velocity)
        else:
            raise TypeError("Can only add Vec3 or Location to Location.")

    def __sub__(self, other: "Location") -> "Location":
        return Location(
            position=self.position - other.position,
            velocity=self.velocity - other.velocity,
        )

    def __neg__(self) -> "Location":
        return Location(position=-self.position, velocity=-self.velocity)

    def __mul__(self, scale: float) -> "Location":
        return Location(position=self.position * scale, velocity=self.velocity * scale)

    def __truediv__(self, scale: float) -> "Location":
        return self * (1 / float(scale))

    def to(self, other) -> Vec3:
        """Returns the `Vec3` from `self` to `other`, i.e. the relative position."""
        if hasattr(other, "position"):
            return other.position - self.position
        else:
            return other - self.position

    def flat(self) -> "Location":
        """Returns a copy of the Location with position and velocity projected onto
        the z=0 plane.
        """
        return Location(self.position.flat(), self.velocity.flat())

    def lerp(self, other: "Location", t: float) -> "Location":
        """(Linearly interpolation) Returns a point on the line between `self` and
        `other`. The parameter `t` determines where on the line. For example:
            * If t = 0, returns `self`.
            * If t = 1, returns `other`.
            * If t = 0.5, returns the midpoint between `self` and `other`.
            * If t = 0.9, returns the point 90% of the way to `other` from `self`.
        """
        return Location(
            position=self.position.lerp(other.position, t),
            velocity=self.velocity.lerp(other.velocity, t),
        )

    def relative_velocity(self, other: Vec3) -> Vec3:
        """Returns the velocity of `self`, relative to `other`. If `other ` is
        stationary, then `relative_velocity` is the same as `velocity`.
        """
        if hasattr(other, "velocity"):
            return self.velocity - other.velocity
        else:
            return self.velocity

    def speed_toward(self, other) -> float:
        """The closing speed of `self` toward `other`. If `self` is approaching `other`,
        the returned speed will be positive. If `self` is moving away from `other`, then
        a negative value is returned. Zero if the distance between `self` and `other` is
        not changing (e.g. both are stationary, or one is moving in a circle around the
        other).
        """
        return self.relative_velocity(other).dot(self.to(other).normalized())

    def distance_in_direction(self, direction: Vec3, distance: float) -> "Location":
        """The Location at the given `distance` from `self` in the specified
        `direction`.
        """
        return Location(
            position=self.position + distance * direction, velocity=self.velocity
        )

    def distance_toward(self, other: "Location", distance: float) -> "Location":
        """The Location at the given `distance` from `self` in the direction of `other`.
        Similar to `lerp`, except it works with absolute distance rather than a fraction
        of the total distance.
        """
        # Since distance is constant, only the perpendicular component of velocity
        # contributes to the output velocity.
        return self.lerp(
            Location(
                position=other.position, velocity=other.velocity.perp(other.to(self))
            ),
            distance / self.distance(other),
        )


class OrientedObject(Location):
    """Objects that have a location, as well as velocity, angular velocity, and
    orientation.
    """

    def __init__(
        self,
        position: Vec3 = 0,
        velocity: Vec3 = 0,
        angular_velocity: Vec3 = 0,
        orientation: Orientation = None,
    ):
        super().__init__(position, velocity)
        self.angular_velocity = Vec3(angular_velocity)
        if orientation is None:
            orientation = Orientation(Vec3())
        self.orientation = orientation

    @property
    def up(self) -> Vec3:
        """Returns a normalized `Vec3` in this object's up direction."""
        return self.orientation.up

    @property
    def down(self) -> Vec3:
        """Returns a normalized `Vec3` in this object's down direction."""
        return -self.orientation.up

    @property
    def left(self) -> Vec3:
        """Returns a normalized `Vec3` in this object's left direction."""
        return -self.orientation.right

    @property
    def right(self) -> Vec3:
        """Returns a normalized `Vec3` in this object's right direction."""
        return self.orientation.right

    @property
    def forward(self) -> Vec3:
        """Returns a normalized `Vec3` in this object's forward direction."""
        return self.orientation.forward

    @property
    def backward(self) -> Vec3:
        """Returns a normalized `Vec3` in this object's backward direction."""
        return -self.orientation.forward

    @property
    def yaw(self) -> float:
        """Returns the object's current yaw value."""
        return self.orientation.yaw

    @property
    def pitch(self) -> float:
        """Returns the object's current pitch value."""
        return self.orientation.pitch

    @property
    def roll(self) -> float:
        """Returns the object's current roll value."""
        return self.orientation.roll

    @property
    def yaw_rate(self) -> float:
        """How fast the object is turning in the yaw direction. The game imposes a
        maximum yaw rate of 5.5 radians/sec. A positive value for a car would mean it
        was turning to the right (turning clockwise viewed from above).
        """
        return self.angular_velocity.dot(self.orientation.up)

    @property
    def pitch_rate(self) -> float:
        """How fast the object is turning in the pitch direction. The game imposes a
        maximum pitch rate of 5.5 radians/sec. A positive value for a car would mean it
        was raising its nose up (turning clockwise viewed from the left).
        """
        return self.angular_velocity.dot(-self.orientation.right)

    @property
    def roll_rate(self) -> float:
        """How fast the object is turning in the roll direction. The game imposes a
        maximum roll rate of 5.5 radians/sec. A positive value for a car would mean it
        was rolling to the right (turning clockwise viewed from behind).
        """
        return self.angular_velocity.dot(-self.orientation.forward)

    def yaw_to(self, other: Vec3) -> float:
        """Returns the yaw angle from the object's forward vector to the given location
        (projected onto the object's horizontal plane). This is the function to use,
        for steering toward another location. It returns the correct answer regardless
        of the object's orientation, e.g. a car driving on the wall or flying upside-
        down. A positive value means the car needs to turn right, negative means left.
        """
        ovec = self.to(other)
        ox = ovec.dot(self.left)
        oy = ovec.dot(self.forward)
        return -math.atan2(ox, oy)

    @property
    def forward_speed(self) -> float:
        """The component of velocity in the forward direction. May be negative."""
        return self.velocity.dot(self.forward)
