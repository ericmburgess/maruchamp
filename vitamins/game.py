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
from vitamins.random import randint
from vitamins import draw
from vitamins import math


class Location:
    """Objects that have a location."""

    loc: Vec3
    vel: Vec3 = Vec3(0, 0, 0)

    def __init__(self, x=0, y=0, z=0):
        if x is None:
            self.loc = Vec3(0, 0, 0)
        elif hasattr(x, "loc"):
            self.loc = Vec3(x.loc.x, x.loc.y, x.loc.z)
        elif isinstance(x, Vec3):
            self.loc = x
        else:
            self.loc = Vec3(x, y, z)
        self.x = self.loc.x
        self.y = self.loc.y
        self.z = self.loc.z

    def to(self, other) -> Vec3:
        """Vector from self to other."""
        if isinstance(other, Vec3):
            return other - self.loc
        return other.loc - self.loc

    def midpoint(self, other) -> Vec3:
        return self.loc + 0.5 * self.to(other)

    def dist(self, other) -> float:
        return self.to(other).length()

    def draw_line_to(self, other, color):
        if isinstance(other, Vec3):
            loc = other
        else:
            loc = other.loc
        draw.line_3d(self.loc, loc, color)

    def nearest(self, *others):
        near = others[0]
        for other in others[:-1]:
            if self.dist(other) < self.dist(near):
                near = other
        return near


class PhysicalObject(Location):
    """GameObjects that also have velocity, angular velocity, and orientation."""

    def __init__(
        self,
        location: Vec3 = None,
        velocity: Vec3 = None,
        avelocity: Vec3 = None,
        orientation: Orientation = None,
    ):
        super().__init__(location)
        self.vel = velocity
        self.avel = avelocity
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
        self.loc = Vec3(phys.location)
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
        loc1 = self.loc + self.vel / 2 * yaw_time
        avg_spd = (2000 + self.spd) / 2
        return loc1.dist(target) / avg_spd

    def reset(self, bot, phys=None):
        """Update the real car to match current values, or given physics."""
        if phys is None:
            phys = Physics(
                location=Vector3(x=self.loc.x, y=self.loc.y, z=self.loc.z),
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
            self.loc = Vec3(phys.location)
            self.vel = Vec3(phys.velocity)
            self.avel = Vec3(phys.angular_velocity)
            self.spd = self.vel.length()

    def reset(self, bot, phys=None):
        """Update the real ball to match current values, or given physics."""
        if phys is None:
            phys = Physics(
                location=Vector3(x=self.loc.x, y=self.loc.y, z=self.loc.z),
                velocity=Vector3(x=self.vel.x, y=self.vel.y, z=self.vel.z),
                angular_velocity=Vector3(x=self.avel.x, y=self.avel.y, z=self.avel.z),
            )
        game_state = GameState(ball=BallState(physics=phys))
        bot.set_game_state(game_state)

    def is_rolling(self):
        return self.loc.z < 95 and abs(self.vel.z) < 1

    def dist_to_corner(self):
        loc = Vec3(self.loc).flat()
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

    def __init__(self, bot, packet=None, phys=None):
        self.bot = bot
        self.bounces = []
        self.draw_path = True
        self.draw_step = 4
        self.draw_bounces = True
        self.draw_seconds = True
        self.on_opp_goal = False  # on a path to score!
        self.on_own_goal = False  # on a path to score...
        self.time_to_goal = 0
        self.next_ground_ball = None

    def update(self):
        super().update(packet=self.bot.packet)
        self.refresh_prediction()

    def future(self, dt: float) -> Ball:
        """Return a Ball instance predicted dt game seconds into the future."""
        if dt <= 0:
            return self
        t = self.bot.game_time + dt
        if (
            getattr(self, "path", None) is None
            or self.path.slices[0].game_seconds > t
            or self.path.slices[self.path.num_slices - 1].game_seconds < t
        ):
            return None
        index = 0
        for index in range(0, self.path.num_slices - self.coarse, self.coarse):
            if self.path.slices[index + self.coarse].game_seconds > t:
                break
        while self.path.slices[index].game_seconds < t:
            index += 1
        phys = self.path.slices[index].physics
        return Ball(phys=phys)

    def next_bounce(self) -> Ball:
        if self.bounces:
            return self.bounces[0]
        else:
            return None

    def next_ground(self) -> Ball:
        """Next time the ball touches the ground."""
        return self.next_ground_ball

    def refresh_prediction(self):
        self.path = self.bot.get_ball_prediction_struct()
        roll_frames = 0
        locations = [self.path.slices[0].physics.location]
        breaks = []
        bounces = []
        seconds = []
        self.next_ground_ball = None
        phys_now = self.path.slices[0].physics
        t_now = self.path.slices[0].game_seconds
        self.time_to_goal = 1e9
        self.on_opp_goal = False
        self.on_own_goal = False
        for i in range(1, self.path.num_slices):
            slice = self.path.slices[i]
            loc = slice.physics.location
            phys_now, phys_prev = slice.physics, phys_now
            t_now, t_prev = slice.game_seconds, t_now
            if ball_bounced_z(phys_prev, phys_now):
                bounces.append(i)
            locations.append(loc)
            if self.next_ground_ball is None and loc.z - self.radius < 5:
                self.next_ground_ball = Ball(phys=phys_now)
                self.next_ground_ball.time = t_now
                draw.cross(self.next_ground_ball.loc, color="white")
            # todo: make this use the goal info instead of hard coding:
            y_fwd = Vec3(loc).dot(self.bot.field.fwd)
            if y_fwd > 5150:
                self.on_opp_goal = True
                self.time_to_goal = min(self.time_to_goal, t_now)
            elif y_fwd < -5150:
                self.on_own_goal = True
                self.time_to_goal = min(self.time_to_goal, t_now)
            if ball_is_rolling(slice.physics):
                roll_frames += 1
                if roll_frames == 3:
                    breaks.append(loc)
            else:
                roll_frames = 0
            if int(t_now) > int(t_prev):
                seconds.append(phys_now.location)

        if self.draw_path:
            self.bot.renderer.draw_polyline_3d(
                locations[:: self.draw_step], self.bot.renderer.white()
            )
            for i in range(1, self.path_thickness):
                for loc in locations:
                    loc.z += 1
                self.bot.renderer.draw_polyline_3d(
                    locations[:: self.draw_step], self.bot.renderer.white()
                )

        if self.draw_rolling_transitions:
            color = self.bot.renderer.blue()
            for loc in breaks:
                self.bot.renderer.draw_rect_3d(loc, 10, 10, 1, color, True)

        color = self.bot.renderer.red()
        self.bounces = []
        for i in bounces[: self.max_bounces]:
            phys = self.path.slices[i].physics
            ball = Ball(phys=phys)
            ball.time = self.path.slices[i].game_seconds
            self.bounces.append(ball)
            if self.draw_bounces:
                loc = Vec3(phys.location)
                loc.z = 0
                self.bot.renderer.draw_rect_3d(loc, 10, 10, 1, color, True)

        if self.draw_seconds:
            color = self.bot.renderer.yellow()
            for loc in seconds:
                self.bot.renderer.draw_rect_3d(loc, 7, 7, 1, color, True)


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
            self.own_goal_center.loc + (goal_width / 2) * self.left
        )
        self.own_right_post = Location(
            self.own_goal_center.loc + (goal_width / 2) * self.right
        )
        self.opp_left_post = Location(
            self.opp_goal_center.loc + (goal_width / 2) * self.right
        )
        self.opp_right_post = Location(
            self.opp_goal_center.loc + (goal_width / 2) * self.left
        )

    def init_boosts(self, field_info_packet: FieldInfoPacket):
        for i in range(field_info_packet.num_boosts):
            boost = field_info_packet.boost_pads[i]
            self.boosts.append(BoostPickup(boost.location, i, boost.is_full_boost))
        self.big_boosts = [b for b in self.boosts if b.is_big]
        self.little_boosts = [b for b in self.boosts if not b.is_big]
        for b in self.big_boosts:
            x = b.loc.dot(self.left)
            y = b.loc.dot(self.fwd)
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
