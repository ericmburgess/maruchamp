"""game.py -- Classes to represent and manipulate game objects."""

from rlbot.utils.structures.game_data_struct import FieldInfoPacket, GameTickPacket
from rlbot.utils.game_state_util import (
    GameState,
    BallState,
    CarState,
    Physics,
    Vector3,
    Rotator,
)

from vitamins.geometry import Orientation, Vec3
from vitamins import draw
from vitamins import math
from vitamins.util import *


class Location(Vec3):
    """Objects that have a location."""

    @property
    def position(self) -> Vec3:
        return Vec3(self.x, self.y, self.z)

    @position.setter
    def position(self, value: Vec3):
        self.x, self.y, self.z = value

    def update(self, new_loc: Vec3):
        self.x, self.y, self.z = new_loc.x, new_loc.y, new_loc.z

    def draw_line_to(self, other: "Location", color: str):
        draw.line_3d(self, other, color)

    def draw_cross(self, size: int = 10, thickness: int = 3, color: str = ""):
        draw.cross(self, size, thickness, color)


class PhysicalObject(Location):
    """GameObjects that also have velocity, angular velocity, and orientation."""

    def __init__(
        self,
        location: Vec3 = 0,
        velocity: Vec3 = 0,
        avelocity: Vec3 = 0,
        orientation: Orientation = None,
    ):
        super().__init__(location)
        self.vel = Vec3(velocity)
        self.avel = Vec3(avelocity)
        if orientation is None:
            orientation = Orientation(Vec3())
        self.ort = orientation

    def rel_vel(self, other) -> Vec3:
        """Relative velocity."""
        return other.vel - self.vel

    def spd_to(self, other) -> float:
        """Closing speed (positive=approaching, negative=away)."""
        return -self.rel_vel(other).dot(self.to(other).normalized())

    def time_to(self, other) -> float:
        pass


class Car(PhysicalObject):
    """Convenient access to data about a car in game."""

    def __init__(self, index, packet=None):
        super().__init__()
        self.index = index
        if packet is not None:
            self.update(packet)

    def update(self, packet):
        pcar = packet.game_cars[self.index]
        phys = pcar.physics
        self.x, self.y, self.z = Vec3(phys.location)
        self.vel = Vec3(phys.velocity)
        self.avel = Vec3(phys.angular_velocity)
        self.spd = self.vel.length()
        self.ort = Orientation(phys.rotation)
        self.fwd = self.ort.forward
        self.back = -self.fwd
        self.right = self.ort.right
        self.left = -self.ort.right
        self.up = self.ort.up
        self.down = -self.ort.up
        self.yaw = self.ort.yaw
        self.pitch = self.ort.pitch
        self.roll = self.ort.roll
        self.dyaw = self.avel.dot(self.up)
        self.droll = self.avel.dot(self.back)
        self.dpitch = self.avel.dot(self.left)
        self.rot = Rotator(self.pitch, self.yaw, self.roll)
        self.wheel_contact = pcar.has_wheel_contact
        self.demolished = pcar.is_demolished
        self.supersonic = pcar.is_super_sonic
        self.boost = pcar.boost

    def yaw_to(self, other):
        if hasattr(other, "loc"):
            loc = other.loc
        else:
            loc = other
        ovec = self.to(loc)
        ox = ovec.dot(self.right)
        oy = ovec.dot(self.fwd)
        return math.atan2(-ox, oy)

    def time_to(self, target):
        """Rough estimate of how long it will take to reach `other`."""
        target = Location(target)
        yaw_to = self.yaw_to(target)
        yaw_time = yaw_to / 2.3
        loc1 = self + self.vel / 2 * yaw_time
        avg_spd = (2000 + self.spd) / 2
        return loc1.dist(target) / avg_spd

    def reset(self, bot, phys=None):
        """Update the real car to match current values, or given physics."""
        if phys is None:
            phys = Physics(
                location=Vector3(x=self.x, y=self.y, z=self.z),
                velocity=Vector3(x=self.vel.x, y=self.vel.y, z=self.vel.z),
                angular_velocity=Vector3(x=self.avel.x, y=self.avel.y, z=self.avel.z),
                rotation=self.rot,
            )
        car_state = CarState(physics=phys)
        game_state = GameState(cars={bot.index: car_state})
        bot.set_game_state(game_state)


class Ball(PhysicalObject):
    """Convenient access to data about the ball."""

    radius = 92.75

    def __init__(self, packet=None, phys=None):
        super().__init__()
        self.vel = Vec3()
        self.avel = Vec3()
        self.spd: float = 0
        self.update(packet, phys)

    def update(self, packet=None, phys=None):
        if packet is not None:
            phys = packet.game_ball.physics
        if phys is not None:
            self.x, self.y, self.z = Vec3(phys.location)
            self.vel = Vec3(phys.velocity)
            self.avel = Vec3(phys.angular_velocity)
            self.spd = self.vel.length()

    def reset(self, bot, phys=None):
        """Update the real ball to match current values, or given physics."""
        if phys is None:
            phys = Physics(
                location=Vector3(x=self.x, y=self.y, z=self.z),
                velocity=Vector3(x=self.vel.x, y=self.vel.y, z=self.vel.z),
                angular_velocity=Vector3(x=self.avel.x, y=self.avel.y, z=self.avel.z),
            )
        game_state = GameState(ball=BallState(physics=phys))
        bot.set_game_state(game_state)

    def is_rolling(self):
        return self.z < 95 and abs(self.vel.z) < 1

    def dist_to_corner(self):
        loc = self.flat()
        loc.x = abs(loc.x)
        loc.y = abs(loc.y)
        return loc.dist(Vec3(4000, 5000, 0))


class TheBall(Ball):
    """The one true ball (i.e. we can predict it)."""

    coarse: int = 16
    max_bounces = 5
    draw_path = False
    draw_bounces = False
    draw_rolling_transitions = False
    draw_seconds = False
    path_thickness = 1
    bounce_threshold = 300

    def __init__(self, bot):
        self.bot = bot
        self.bounces = []
        self.draw_path = True
        self.draw_step = 8
        self.draw_bounces = True
        self.on_opp_goal = False  # on a path to score!
        self.on_own_goal = False  # on a path to score...
        self.time_to_goal = 0
        self.next_prediction_update = 0
        self.prediction_interval = 1
        self.current_slice = 0
        self.prediction = None
        self.index_now = 0
        self.roll_time = None

    def update(self):
        super().update(packet=self.bot.packet)
        # self.refresh_prediction()
        self.update_prediction()
        self.analyze_prediction()
        if self.draw_path:
            self.draw_prediction(step=self.draw_step)

    def future(self, dt: float) -> Ball:
        """Return a Ball instance predicted dt game seconds into the future."""
        if dt <= 0:
            return self
        t = self.bot.game_time + dt
        if (
            getattr(self, "path", None) is None
            or self.prediction.slices[0].game_seconds > t
            or self.prediction.slices[self.prediction.num_slices - 1].game_seconds < t
        ):
            return None
        index = 0
        for index in range(0, self.prediction.num_slices - self.coarse, self.coarse):
            if self.prediction.slices[index + self.coarse].game_seconds > t:
                break
        while self.prediction.slices[index].game_seconds < t:
            index += 1
        phys = self.prediction.slices[index].physics
        return Ball(phys=phys)

    def update_prediction(self):
        if self.prediction is not None:
            while (
                self.prediction.slices[self.index_now + 1].game_seconds
                <= self.bot.game_time
            ):
                self.index_now += 1
            if (
                self.vel - self.prediction.slices[self.index_now].physics.velocity
            ).length() > 30:
                self.next_prediction_update = self.bot.game_time

        if self.bot.game_time >= self.next_prediction_update:
            self.next_prediction_update += self.prediction_interval
            self.prediction = self.bot.get_ball_prediction_struct()
            self.current_slice = 0
            self.index_now = 0
            self.bounces = []
            self.roll_time = None

    def analyze_prediction(self, max_ms=2):
        stop_ns = perf_counter_ns() + max_ms * 1e6
        while self.current_slice < self.prediction.num_slices:
            slice = self.prediction.slices[self.current_slice]
            if self.current_slice > 0:
                p_slice = self.prediction.slices[self.current_slice - 1]
                # See if the ball bounced:
                if len(self.bounces) < self.max_bounces:
                    v1 = Vec3(slice.physics.velocity)
                    v2 = Vec3(p_slice.physics.velocity)
                    if (v1 - v2).length() > self.bounce_threshold:
                        self.bounces.append((self.current_slice - 1, v1 - v2))
            if self.roll_time is None:
                if abs(slice.physics.velocity.z) < self.bounce_threshold / 2:
                    if slice.physics.location.z - self.radius < 30:
                        self.roll_time = self.current_slice
            self.current_slice += 1
            if perf_counter_ns() > stop_ns:
                break

    def draw_prediction(self, step=4):
        roll = self.roll_time
        if roll is None:
            roll = self.prediction.num_slices
        if roll > step:
            draw.polyline_3d(
                [
                    self.prediction.slices[i].physics.location
                    for i in range(0, roll, step)
                ]
            )
        if roll < self.prediction.num_slices - step - 1:
            draw.polyline_3d(
                [
                    self.prediction.slices[i].physics.location
                    for i in range(roll, self.prediction.num_slices, step)
                ],
                color="cyan",
            )
        if self.draw_bounces:
            for i, dv in self.bounces:
                draw.cross(self.prediction.slices[i].physics.location, color="red")


class BoostPickup(Location):
    """Boost pickup. Duh."""

    def __init__(self, location, index: int, is_big: bool):
        super().__init__(location)
        self.index = index
        self.is_big = is_big
        self.is_ready = False
        self.timer = 0


class Field:
    """Convenient access to data about the play field."""

    def __init__(self, team: int, field_info_packet: FieldInfoPacket):
        self.center = Location(0, 0, 0)
        self.fwd = Vec3(0, -1 if team else 1, 0)
        self.back: Vec3 = -self.fwd
        self.left = Vec3(-1 if team else 1, 0, 0)
        self.right: Vec3 = -self.left
        self.up = Vec3(0, 0, 1)
        self.down: Vec3 = -self.up
        self.boosts = []
        self.init_boosts(field_info_packet)
        self.init_goals()

    def init_goals(self):
        goal_width = 1786
        self.opp_goal_center = Location(5120 * self.fwd + Vec3(0, 0, 320))
        self.own_goal_center = Location(5120 * self.back + Vec3(0, 0, 320))
        self.own_left_post = Location(
            self.own_goal_center + (goal_width / 2) * self.left
        )
        self.own_right_post = Location(
            self.own_goal_center + (goal_width / 2) * self.right
        )
        self.opp_left_post = Location(
            self.opp_goal_center + (goal_width / 2) * self.right
        )
        self.opp_right_post = Location(
            self.opp_goal_center + (goal_width / 2) * self.left
        )

    def init_boosts(self, field_info_packet: FieldInfoPacket):
        for i in range(field_info_packet.num_boosts):
            boost = field_info_packet.boost_pads[i]
            self.boosts.append(BoostPickup(boost.location, i, boost.is_full_boost))
        self.big_boosts = [b for b in self.boosts if b.is_big]
        self.little_boosts = [b for b in self.boosts if not b.is_big]
        for b in self.big_boosts:
            x = b.dot(self.left)
            y = b.dot(self.fwd)
            if y < -1000:
                if x > 0:
                    self.boostBL = b
                else:
                    self.boostBR = b
            elif y > 1000:
                if x > 0:
                    self.boostFL = b
                else:
                    self.boostFR = b
            else:
                if x > 0:
                    self.boostML = b
                else:
                    self.boostMR = b

    def update(self, packet: GameTickPacket):
        """Update from game tick packet (boost pickup status)."""
        for i in range(packet.num_boost):
            self.boosts[i].is_ready = packet.game_boosts[i].is_active
            self.boosts[i].timer = packet.game_boosts[i].timer


def ball_is_rolling(phys) -> bool:
    return phys.location.z < 95 and phys.velocity.z < 1


def ball_bounced(phys1, phys2) -> bool:
    """Return whether the ball bounced between the two physics frames."""
    threshhold = 400
    v1 = Vec3(phys1.velocity)
    v2 = Vec3(phys2.velocity)
    return (v1 - v2).length() > threshhold


def ball_bounced_z(phys1, phys2) -> bool:
    v1 = Vec3(phys1.velocity)
    v2 = Vec3(phys2.velocity)
    return v1.z < 0 and v2.z > 0
