"""veggies.misc -- assorted activities."""

from vitamins.activity import Activity
from vitamins.game import Car, Location
from ramen import control
from vitamins.math import *


class Idle(Activity):
    def step_0(self):
        self.bot.clear_controls()
        self.next_step()

    def step_1(self):
        pass


def should_front_flip(bot, car: Car, target: Location) -> bool:
    should = True
    if "kickoff" in bot.state or "flip" in bot.state:
        should = False
    elif car.spd < 800:
        should = False
    elif car.spd > 2200:
        should = False
    elif car.dist(target) < 3000:
        should = False
    elif car.boost > 70:
        should = False
    elif abs(car.yaw_to(target)) > 0.5:
        should = False
    elif car.vel.ndot(car.to(target)) < 0.8:
        should = False
    return should


class BallChase(Activity):
    def step_0(self):
        self.dt = 0
        self.next_step()

    def step_1(self):
        self.bot.con.jump = False
        car, ball = self.bot.car, self.bot.ball
        future_ball = ball.future(self.dt)
        if future_ball is None:
            future_ball = ball
            self.dt = 1
        else:
            z = future_ball.loc.z - future_ball.radius
            if z > 20:
                tjump = z / 300
                if tjump < 1:
                    if (car.loc + self.dt * car.vel).dist(future_ball.loc) < 300:
                        self.bot.con.jump = self.dt < tjump
        rel_spd = car.spd_to(future_ball)
        if rel_spd > 0:
            self.dt = car.dist(ball) / car.spd_to(ball)
            # ball = ball.future(min(self.dt, 3) * 1.2)
        self.bot.con.throttle = 1
        offset = (
            copysign(1, future_ball.loc.dot(self.bot.field.right))
            * self.bot.field.right
        ) * self.bot.field.right
        if future_ball.loc.dot(self.bot.field.fwd) < 0:
            offset = -offset
        target_loc = future_ball.loc + offset * ball.radius
        pow = False
        if car.yaw_to(target_loc) < 0.2 and car.dist(target_loc) < 300:
            pow = ball.is_rolling()
        if should_front_flip(self.bot, car, target_loc) or pow:
            self.bot.state = "front flip"
            self.bot.flip_yaw = car.yaw_to(target_loc)
        control.turn_toward(self.bot, target_loc)
        self.bot.con.boost = self.bot.car.spd < 2250
        self.status = f"dt:{self.dt:.2f}, relspd:{rel_spd:.2f}"


class DriveToLocation(Activity):
    def __init__(self, bot, target, use_boost=True, forever=False):
        super().__init__(bot)
        self.target = target
        self.use_boost = use_boost
        self.forever = forever

    def step_0(self):
        car = self.bot.car
        self.bot.con.throttle = 1
        control.turn_toward(self.bot, self.target.loc)
        self.bot.con.boost = self.use_boost and self.bot.car.spd < 1800
        self.status = f"{car.dist(self.target):.0f}"
        if car.dist(self.target) < 500:
            # avoid circling
            self.bot.con.boost = False
            self.bot.con.throttle = self.bot.car.spd < 500
        if car.dist(self.target) < 200 and not self.forever:
            self.done = True
        if should_front_flip(self.bot, car, self.target):
            self.bot.state = "front flip"
            self.bot.flip_yaw = car.yaw_to(self.target)
        car.draw_line_to(self.target, "green")


class Follow(Activity):
    def __init__(self, bot, target_func, use_boost=True):
        """Follow a dynamic location.
        target_func should return a Vec3 or Location.
        """
        super().__init__(bot)
        self.target_func = target_func
        self.use_boost = use_boost

    def step_0(self):
        car = self.bot.car
        target = self.target_func()
        self.bot.con.throttle = 1
        control.turn_toward(self.bot, target)
        self.bot.con.boost = self.use_boost and self.bot.car.spd < 1800
        self.status = f"{car.dist(target):.0f}"
        if car.dist(target) < 500:
            # avoid circling
            self.bot.con.boost = False
            self.bot.con.throttle = self.bot.car.spd < 500
        if should_front_flip(self.bot, car, target):
            self.bot.state = "front flip"
            self.bot.flip_yaw = car.yaw_to(target)
        car.draw_line_to(target, "red")


class StrikeAt(Activity):
    def __init__(self, bot, target_func):
        """Follow a dynamic location and try to hit it fast.
        target_func should return a Vec3 or Location.
        """
        super().__init__(bot)
        self.target_func = target_func

    def step_0(self):
        car = self.bot.car
        target = self.target_func()
        self.bot.con.throttle = 1
        control.turn_toward(self.bot, target)
        self.bot.con.boost = False
        if car.yaw_to(target) < 0.1:
            if car.boost > 30 or car.dist(target) < 500:
                if car.spd < 2300:
                    self.bot.con.boost = True
        self.status = f"{car.dist(target):.0f}"
        car.draw_line_to(target, "red")


class JustDrive(Activity):
    def step_0(self):
        self.bot.con.throttle = 1
        self.bot.con.steer = 0
