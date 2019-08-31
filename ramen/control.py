"""ramen.control -- routines for controlling the car."""
from vitamins.agent import RamenBot
from vitamins import draw
from vitamins.geometry import Vec3
from vitamins.math import *
from vitamins.game import Location, Car, Ball


BOOST_ACCEL = 991.557
BOOST_USAGE_PER_SEC = 33.3
MAX_CAR_SPEED = 2300.0
forward_accel_curve = Lerp(
    [0.0, 1400.0, 1410.0, 2300.0], [1600.0, 160.0, 0.0, 0.0], clamp=True
)


def simulate_drive_forward(
    speed: float,
    throttle: float = 1,
    distance: float = 0,
    t: float = 0,
    boost: float = 0,
    dt=0.01,
) -> (float, float, float):
    """Simulate driving straight forward with constant throttle. Returns the final
    state after either a specified distance is covered, or time elapsed.
    Args:
        speed: initial speed
        throttle: throttle (held constant during drive)
        distance: end distance
        t: drive time in game seconds
        boost: how much boost to use--will boost when speed < maximum
        dt: time step in game seconds
    Returns: (elapsed time, distance covered, final speed, remaining boost)
    """
    if distance < 0 or t < 0:
        raise ValueError(f"Distance ({distance}) and time ({t}) must be non-negative!")
    if distance == t == 0:
        return (0, 0, speed, boost)
    elapsed, moved = 0, 0
    while True:
        accel_lerp = 1 / 2
        if speed < MAX_CAR_SPEED and boost > 0:
            boost = max(0, boost - BOOST_USAGE_PER_SEC * dt)
            accel = forward_accel_curve(speed) + BOOST_ACCEL
        else:
            accel = forward_accel_curve(speed) * throttle
        moved += (speed + accel * dt * accel_lerp) * dt
        speed = clamp(0, speed + accel * dt, MAX_CAR_SPEED)
        elapsed += dt
        if elapsed > t > 0:
            break
        if moved > distance > 0:
            break
    return (elapsed, moved, speed, boost)


class Waypoint(Location):
    """A point along a path."""

    speed: float
    time: float

    def __init__(self, point: Location, speed: float = None, time: float = None):
        super().__init__(point.flat())
        self.speed = speed
        self.time = time


class Path:
    waypoints: [Waypoint]

    def __init__(self):
        self.waypoints = []

    def __len__(self):
        return len(self.waypoints)

    def __getitem__(self, item):
        return self.waypoints[item]

    def append(self, point: Location, target_speed: float = 1410):
        self.waypoints.append(Waypoint(point, target_speed))

    def prepend(self, point: Location, target_speed: float = 1410):
        self.waypoints.insert(0, Waypoint(point, target_speed))

    def insert(self, index: int, point: Location, target_speed: float = 1410):
        self.waypoints.insert(index, Waypoint(point, target_speed))

    def length(self, start_index=0, end_index=None) -> float:
        if len(self) < 2:
            return 0
        if end_index is None:
            end_index = len(self)
        distance = 0
        for i in range(start_index + 1, end_index):
            distance += self.waypoints[i - 1].dist(self.waypoints[i])
        return distance


# todo: make the later nodes have speed 2300 so the boost happens that way
def make_strike_path(
    car: Car,
    target: Vec3,
    target_dir: Vec3,
    segment_len: float = 200,
    segment_angle: float = pi / 8,
    lead_segments: int = 5,
):
    pos = target.flat()
    dir = target_dir.normalized()
    # Follow-through:
    path = Path()
    path.append(pos + dir * 200)
    # Add the lead-in segments which must be straight in the target direction:
    for i in range(lead_segments):
        pos -= segment_len * dir
        path.prepend(pos)
    # Now start curving until it's a gentle start for the car:
    fcar = (car.position + car.vel * 0).flat()
    yaw = fcar.to(pos).yaw_to(dir)
    print(f"Starting yaw is {yaw}")
    while abs(yaw) > segment_angle:
        yaw = -copysign(segment_angle, yaw)
        x, y = dir.x, dir.y
        dir.x = x * cos(yaw) - y * sin(yaw)
        dir.y = x * sin(yaw) + y * cos(yaw)
        pos -= segment_len * dir
        path.prepend(pos)
        yaw = fcar.to(pos).yaw_to(dir)
        if len(path) > 15:
            break
    return path


def make_destination_path(
    target: Vec3, target_dir: Vec3, segment_len: float = 200, lead_segments: int = 5
):
    pos = target.flat()
    dir = target_dir.normalized()
    path = Path()
    # Add the lead-in segments which must be straight in the target direction:
    for i in range(lead_segments):
        pos -= segment_len * dir
        path.prepend(pos)
    return path


def steer_to(bot: RamenBot, target: Vec3, no_handbrake=False):
    draw.cross(target, color="purple")
    halt_sec = 0.15  # How long (estimated) it takes to halt a turn
    err = bot.car.yaw_to(target)
    dyaw = bot.car.avel.z
    if abs(err) < 0.01:
        bot.con.steer = 0
    elif abs(err) < 0.05:
        bot.con.steer = copysign(0.2, err)
    else:
        bot.con.steer = copysign(1, err)
        if dyaw != 0:
            if 0 < err / dyaw < halt_sec:
                bot.con.steer = -bot.con.steer
            if err / dyaw > 2 * halt_sec and not no_handbrake:
                bot.con.handbrake = True
            else:
                bot.con.handbrake = False
    if bot.car.spd < 0:
        bot.con.steer = -bot.con.steer


def desired_ball_direction(bot: RamenBot, ball: Ball) -> Vec3:
    """Returns a normalized vector pointing the way we want the ball to go. On offense
    it'll be into the opponent's goal; on defense, it'll be away from ours."""
    car, field = bot.car, bot.field
    t = clamp(field.own_goal_center.to(ball).dot(field.fwd) / 2000, 0, 1)
    away_from_own_goal = field.left if ball.dot(field.left) > 0 else field.right
    toward_opp_goal = ball.to(field.opp_goal_center).normalized()
    dir = away_from_own_goal.lerp(toward_opp_goal, t)
    draw.line_3d(ball, ball + dir * 500, "red")
    return dir


def steer_to_future_ball(bot: RamenBot, dt: float = 0) -> float:
    """Steer to where the ball will be `dt` seconds in the future. Return a new value
    of dt in case we need to adjust.
    """
    car, ball = bot.car, bot.ball
    fball = ball.future(dt) or ball
    distance = car.box.location("FU").dist(fball) - fball.radius
    speed_to = max(1, car.spd_to(fball.position))
    new_dt = distance / speed_to
    steer_to(bot, fball)
    return new_dt


def ball_offset(bot: RamenBot, ball: Ball, desired_dir: Vec3) -> Vec3:
    """Where we should be driving to. At the ball if it's going where we want it to,
    off to the side if we need to steer it.
    """
    car, field = bot.car, bot.field
    right = field.up.cross(car.to(ball).flat()).normalized()
    offset = -500 * right * right.dot(desired_dir)
    draw.cross(ball + offset, color="yellow")
    return offset


def steer_ball_into_goal(bot: RamenBot, dt: float = 0) -> float:
    """Steer to where the ball will be `dt` seconds in the future. Return a new value
    of dt in case we need to adjust. Adjustments to nudge the ball toward the goal.
    """
    car, ball = bot.car, bot.ball
    fball = ball.future(dt) or ball
    dir = desired_ball_direction(bot, fball)
    offset = Vec3(0)
    offset = ball_offset(bot, ball, dir)
    ball_right = bot.field.up.cross(fball.vel.flat().normalized())
    goal_side = fball.to(bot.field.opp_goal_center).ndot(ball_right)
    # Adjust future ball position to hit the right point on the ball:
    fball.position += offset
    # draw.cross(fball, color="yellow")
    # Take into account which corner we'll touch it with:
    if car.to(fball).dot(car.right) > 0.2:
        box_location = "FUR"
    elif car.to(fball).dot(car.right) < -0.2:
        box_location = "FUL"
    else:
        box_location = "FU"
    distance = car.box.location(box_location).dist(fball)
    speed_to = max(1, car.spd_to(fball))
    new_dt = distance / speed_to
    steer_to(bot, fball)
    return new_dt


# todo: this is a mess, fix or delete. not used anywhere.
class FlatInterceptor:
    """Manages intercepting a moving point efficiently (by aiming toward the future
    position). This class assumes everything happens on the ground, and it also assumes
    the car is sort of heading the right way already. Assumes the target moves with
    constant velocity.
    """

    def __init__(self, bot, dt=0):
        self.bot: RamenBot = bot
        # seconds in the future to aim for; zero for soonest possible.
        self.dt: float = dt

    def find_soonest_intercept_time(self, target_pos: Vec3, target_vel: Vec3) -> float:
        car = self.bot.car
        # Use distance and relative speed to get a lower bound:
        distance = car.dist(target_pos)
        speed_to = max(1, car.spd_to(ball))
        dt = distance / speed_to

    def intercept(self):
        pass
