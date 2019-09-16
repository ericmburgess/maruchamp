"""ramen.control -- routines for controlling the car."""
from typing import Tuple

from vitamins import draw
from vitamins.math import *
from vitamins.match.base import Location

from vitamins.match.match import Match


BOOST_ACCEL = 991.557
COAST_ACCEL = -525.0
BRAKE_ACCEL = -3500.0
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
) -> Tuple[float, float, float, float]:
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
        return 0, 0, speed, boost
    elapsed, moved = 0, 0
    while True:
        accel_lerp = 1 / 2
        if speed < MAX_CAR_SPEED and boost > 0:
            boost = max(0, boost - BOOST_USAGE_PER_SEC * dt)
            accel = forward_accel_curve(speed) + BOOST_ACCEL
        elif throttle < 0.01 and boost == 0:
            accel = COAST_ACCEL
        else:
            accel = forward_accel_curve(speed) * throttle
        moved += (speed + accel * dt * accel_lerp) * dt
        speed = clamp(0, speed + accel * dt, MAX_CAR_SPEED)
        if speed == 0:
            elapsed = 1e9
            break
        elapsed += dt
        if elapsed > t > 0:
            break
        if moved > distance > 0:
            break
        if elapsed > 10:
            break
    return elapsed, moved, speed, boost


class Path:
    waypoints: [Location]

    def __init__(self):
        self.waypoints = []

    def __len__(self):
        return len(self.waypoints)

    def __getitem__(self, item):
        return self.waypoints[item]

    def append(self, point: Location, target_speed: float = 1410):
        point.target_speed = target_speed
        self.waypoints.append(point)

    def insert(self, index: int, point: Location, target_speed: float = 1410):
        point.target_speed = target_speed
        self.waypoints.insert(index, point)

    def prepend(self, point: Location, target_speed: float = 1410):
        self.insert(0, point, target_speed)

    def length(self, start_index=0, end_index=None) -> float:
        if len(self) < 2:
            return 0
        if end_index is None:
            end_index = len(self)
        distance = 0
        for i in range(start_index + 1, end_index):
            distance += self.waypoints[i - 1].dist(self.waypoints[i])
        return distance


def maintain_forward_speed(desired_speed: float, boost_available: float = 0) -> bool:
    """Apply throttle, boost, and/or brakes as needed to reach and maintain the given
    forward speed. Return True while working on it, False if it becomes impossible.
    """
    car = Match.agent_car
    desired_speed = min(desired_speed, MAX_CAR_SPEED)
    dt = 0.30  # We'll set controls to reach desired speed in `dt` seconds if possible
    desired_accel = (desired_speed - car.forward_speed) / dt
    full_throttle_accel = forward_accel_curve(car.forward_speed)
    boost_needed = (desired_speed - MAX_CAR_SPEED) * BOOST_USAGE_PER_SEC / BOOST_ACCEL
    if boost_needed > boost_available:
        return False
    accel_threshold = 10.0
    Match.agent.boost(False)
    if desired_accel < 0 and car.forward_speed > desired_speed:
        Match.agent.throttle(-1)
    elif desired_accel < BRAKE_ACCEL * 0.6:
        Match.agent.throttle(-1)
    elif desired_accel < -accel_threshold:
        Match.agent.throttle(0)
    elif desired_accel < accel_threshold:
        Match.agent.throttle(0.02)
    elif desired_accel <= full_throttle_accel:
        Match.agent.throttle(desired_accel / full_throttle_accel)
    else:
        if car.forward_speed == MAX_CAR_SPEED:
            Match.agent.boost(True)
        elif boost_available > boost_needed + BOOST_USAGE_PER_SEC * dt:
            Match.agent.boost(True)
        else:
            Match.agent.throttle(1)
            Match.agent.boost(False)


def steer_to(target: Location, no_handbrake=False):
    draw.cross(target, color="purple")
    halt_sec = 0.15  # How long (estimated) it takes to halt a turn
    err = Match.agent_car.yaw_to(target)
    dyaw = Match.agent_car.yaw_rate
    if abs(err) < 0.01:
        steer = 0
    elif abs(err) < 0.05:
        steer = copysign(0.2, err)
    else:
        steer = copysign(1, err)
        if dyaw != 0:
            if 0 < err / dyaw < halt_sec:
                steer = -steer
            if err / dyaw > 2 * halt_sec and not no_handbrake:
                Match.agent.handbrake(True)
            else:
                Match.agent.handbrake(False)
    Match.agent.steer(steer)
    # if Match.agent_car.velocity.dot(Match.agent_car.forward) < 0:
    #     Match.agent.steer(-Match.agent.controls.steer)
