"""ramen.activities -- assorted activities."""

from vitamins.activity import Activity, ActivityDone
from vitamins.agent import RamenBot
from vitamins.game import Car, Location
from ramen import control
from vitamins.geometry import Orientation, Vec3, Line
from vitamins.math import *
from vitamins import draw


class FrontFlip(Activity):
    def step_0(self):
        if self.bot.car.wheel_contact:
            self.next_step()

    def step_1(self):
        self.bot.con.jump = True
        if not self.bot.car.wheel_contact:
            self.bot.con.jump = False
            self.next_step(ms=200)

    def step_2(self):
        self.bot.con.pitch = -1
        self.next_step(ms=24)

    def step_3(self):
        self.bot.con.pitch = -1
        self.bot.con.jump = True
        self.next_step(ms=24)

    def step_4(self):
        self.done = True


class FollowTimedPath(Activity):
    """Visit a series of timed locations."""

    def __init__(self, bot: RamenBot, path: control.Path, cut=0.5):
        super().__init__(bot)
        self.path = path
        self.cut = cut
        self.index = 0
        self.mark = self.bot.game_time

    def step_0(self):
        self.bot.con.throttle = 1
        if self.bot.game_time - self.mark > 15:
            self.done = True
        point = self.path[self.index].flat()
        time_to_next = self.bot.car.flat().dist(point) / max(
            1e-3, self.bot.car.spd_to(point)
        )
        draw.path(self.path[max(0, self.index - 1) :], "red", "yellow")
        if abs(self.bot.car.avel.z) < 0.01 and abs(self.bot.car.yaw_to(point)) < 0.01:
            draw.line_flat(self.bot.car, point, "green")
        else:
            control.steer_to(self.bot, point)
        if time_to_next < self.cut:
            self.index += 1
            if self.index >= len(self.path):
                self.done = True


class FollowPath(Activity):
    """Visit a series of locations."""

    def __init__(self, bot: RamenBot, path: control.Path, cut=0.5):
        super().__init__(bot)
        self.path = path
        self.cut = cut
        self.index = 0
        self.mark = self.bot.game_time
        self.flipped = False

    def step_0(self):
        if self.bot.game_time - self.mark > 15:
            self.done = True
        point = self.path[self.index].flat()
        time_to_next = self.bot.car.flat().dist(point) / max(
            1e-3, self.bot.car.spd_to(point)
        )
        if time_to_next > 3.5 and not self.flipped:
            if self.bot.car.fwd.ndot(self.bot.car.to(point)) > 0.999:
                if self.bot.car.spd > 1100:
                    # do a front flip
                    self.bot.clear_controls()
                    self.flip = FrontFlip(self.bot)
                    # self.flipped = True
                    self.next_step()
        draw.path(self.path[max(0, self.index - 1) :], "red", "yellow")
        control.steer_to(self.bot, point)
        self.bot.con.throttle = 1
        draw.text_3d(point, 1, f"{time_to_next:.2f}", "white")
        if time_to_next < self.cut:
            self.index += 1
            self.flipped = False
            if self.index >= len(self.path):
                self.done = True

    def step_1(self):
        self.flip()
        if self.flip.done:
            self.bot.clear_controls()
            self.next_step(0)

    def step_2(self):
        self.bot.clear_controls()
        self.done = True


class FollowStrikePath(Activity):
    """Visit a series of locations."""

    def __init__(self, bot: RamenBot, path: control.Path, cut=0.5):
        super().__init__(bot)
        self.path = path
        self.cut = cut
        self.index = 0
        self.mark = self.bot.game_time
        self.flipped = False

    def step_0(self):
        if self.bot.game_time - self.mark > 15:
            self.done = True
        point = self.path[self.index].flat()
        time_to_next = self.bot.car.flat().dist(point) / max(
            1e-3, self.bot.car.spd_to(point)
        )
        if time_to_next > 3 and not self.flipped:
            if self.bot.car.fwd.ndot(self.bot.car.to(point)) > 0.999:
                if self.bot.car.spd > 1100:
                    # do a front flip
                    self.bot.clear_controls()
                    self.flip = FrontFlip(self.bot)
                    self.flipped = True
                    self.next_step()
        draw.path(self.path[max(0, self.index - 1) :], "red", "yellow")
        control.steer_to(self.bot, point)
        self.bot.con.throttle = 1
        draw.text_3d(point, 1, f"{time_to_next:.2f}", "white")
        if time_to_next < self.cut:
            self.index += 1
            self.flipped = False
            if self.index >= len(self.path):
                self.done = True
        # boost through the impact:
        self.bot.con.boost = len(self.path) - self.index < 5
        # frontflip hit it:
        time_to_impact = (
            self.bot.car.box.location("FU").dist(self.bot.ball) - self.bot.ball.radius
        ) / self.bot.car.spd
        if time_to_impact < 0.10:
            self.bot.con.jump = True
            self.bot.con.pitch = 1
            self.next_step(2, ms=100)

    def step_1(self):
        self.flip()
        if self.flip.done:
            self.bot.clear_controls()
            self.next_step(0)

    def step_2(self):
        self.bot.clear_controls()
        self.done = True


class GetOnLine(Activity):
    """Drive to join the line before the specified position. The Line is inherently
    directed; by default assumes we want to get on the line in that direction."""

    def __init__(self, bot: RamenBot, line: Line, pos: Location, reverse: bool = False):
        super().__init__(bot)
        self.line = line
        self.target_pos = self.line.nearest_point(pos)
        self.reverse = reverse

    def step_0(self):
        if self.bot.car.fwd.dot(self.bot.car.to(self.target_pos)) > 0:
            # The target is in front of us.
            if self.bot.car.fwd.dot(self.line.dir) > 0:
                # We're pointed along the line direction:
                pass


class BounceHit(Activity):
    """Hit a bouncing ball as directly as possible."""

    def step_0(self):
        self.bounce_time = self.bot.game_time
        self.offset = 0
        self.next_step()

    def step_1(self):
        self.bounce = self.bot.ball.next_bounce(self.bounce_time)
        if self.bounce is None:
            print(len(self.bot.ball.bounces))
            self.done = True
        else:
            self.bounce_time = self.bounce.time
            self.offset = None
            self.next_step()

    def step_2(self):
        # Start lining up on the bounce, and looking to bail out if it's too far.
        self.bot.con.throttle = 1
        control.steer_to(self.bot, self.bounce.flat())
        speed_needed = self.bot.car.dist(self.bounce.flat()) / max(
            1e-3, self.bounce.time - self.bot.game_time
        )
        if speed_needed > 2300:
            # Can't reach it, try the next one:
            print("too far")
            self.next_step(1)
        if self.bot.car.fwd.ndot(self.bot.car.to(self.bounce)) > 0.99:
            # getting close to on line, think about the angle:
            if self.offset is None:
                angle = self.bot.car.to(self.bounce).yaw_to(
                    self.bot.field.opp_goal_center
                )
                offset_length = angle * 30
                self.offset = self.bot.car.left * offset_length
                print(f"offset: {offset_length}")
                self.bounce.position += self.offset
        if self.bot.car.fwd.ndot(self.bot.car.to(self.bounce)) > 0.999:
            if abs(self.bot.car.avel.z) < 0.01:
                # We're solidly on line, now worry about the timing:
                self.bot.clear_controls()
                self.next_step()
        # Make sure it's still gonna be there:
        fball = self.bot.ball.future(self.bounce.time - self.bot.game_time)
        if fball is None or fball.dist(self.bounce) > 80:
            print("abort! someone hit it first!")
            self.done = True

    def step_3(self):
        dist = self.bot.car.box.location("FU").dist(self.bounce) - self.bounce.radius
        if dist < 0:
            print(dist)
            self.done = True
            return
        dt, d, spd, boost = control.simulate_drive_forward(
            self.bot.car.spd, 1, distance=dist, boost=self.bot.car.boost
        )
        time_to_bounce = self.bounce.time - self.bot.game_time
        diff = dt - time_to_bounce
        draw.text_3d(self.bounce, 1, f"{diff:+.2f}")
        if diff > 0.5:
            self.next_step(1)
        elif diff < 0:
            # We're ahead of ourselves, slow down:
            self.bot.con.throttle = 0
            draw.line_flat(self.bot.car, self.bounce, "red")
        else:
            # We're on track!
            self.bot.con.throttle = 1
            self.bot.con.boost = self.bot.car.spd < 2299
            draw.line_flat(self.bot.car, self.bounce, "green")
        if dt < 0.1:
            self.bot.con.jump = True
            self.bot.con.pitch = 1
            self.next_step(ms=100)

    def step_4(self):
        self.bot.clear_controls()
        self.done = True


class BounceApproachHit(Activity):
    """Hit a bouncing ball toward the opponent's goal by approaching carefully."""

    def step_0(self):
        bounces = self.bot.ball.get_bounces()
        if len(bounces) > 1:
            fball = bounces[1]
        else:
            return
        dir = fball.to(self.bot.field.opp_goal_center).flat().normalized()
        if abs(fball.x) > 2000:
            dir.x = -dir.x
        path = control.make_strike_path(self.bot.car, fball - dir * 2500, dir)
        self.move = FollowTimedPath(self.bot, path, cut=0.25)
        self.next_step()

    def step_1(self):
        self.move()
        if self.move.done:
            self.done = True


class BallChase(Activity):
    def step_0(self):
        self.bot.con.throttle = 1
        control.steer_to(self.bot, self.bot.ball)
        if self.bot.car.yaw_to(self.bot.ball) < 0.2:
            self.next_step()

    def step_1(self):
        self.bot.con.throttle = 1
        dist = (
            self.bot.car.box.location("FU").dist(self.bot.ball.flat())
            - self.bot.ball.radius
        )
        dt = dist / self.bot.car.spd_to(self.bot.ball.flat())
        fball = self.bot.ball.future(dt)
        if fball is not None:
            dist = self.bot.car.box.location("FU").dist(fball.flat()) - fball.radius
            dt = dist / self.bot.car.spd_to(fball.flat())
            if fball.dot(self.bot.field.fwd):
                fball.position += self.bot.field.opp_goal_center.to(fball).rescale(80)
            else:
                fball.position -= self.bot.field.own_goal_center.to(fball).rescale(80)
            control.steer_to(self.bot, fball.flat())
            if dt > 3 and self.bot.car.spd > 800 and self.bot.car.avel.length() < 0.1:
                self.flip = FrontFlip(self.bot)
                self.next_step()
            draw.cross(fball.flat(), color="yellow")
            if (
                0.2 < dt < 1.0
                and abs(fball.z - (130 + 300 * dt)) < 50
                and self.bot.car.wheel_contact
                and False  # todo: make this work better
            ):
                self.bot.con.jump = True
            else:
                self.bot.con.jump = False
        else:
            self.bot.con.steer = 0
            self.next_step(0)

    def step_2(self):
        self.flip()
        if self.flip.done:
            self.bot.clear_controls()
            self.next_step(1)


class ChaseSmarter(Activity):
    dt: float = 0
    flip = None

    def step_0(self):
        if self.bot.tick % 60 == 0:
            self.dt = 0
        self.bot.con.throttle = 1
        self.dt = control.steer_ball_into_goal(self.bot, self.dt)
        fball = self.bot.ball.future(self.dt) or self.bot.ball
        # Slow down instead of driving under:
        if fball.z - fball.radius > 20 and self.dt < 2:
            self.bot.con.throttle = 0
            if self.dt < 1:
                self.bot.con.throttle = -1
        if self.bot.con.throttle == 1:
            if self.bot.car.yaw_to(fball) < 0.1 and 3.5 < self.dt:
                if self.bot.car.avel.length() < 0.01:
                    if 800 < self.bot.car.spd < 2000:
                        if self.bot.car.dist(self.bot.ball) > 500:
                            print(f"flipping, dt={self.dt}")
                            self.flip = FrontFlip(self.bot)
                        self.next_step("flip")

    def step_flip(self):
        if self.flip is None or self.flip.done:
            self.bot.clear_controls()
            self.next_step(0)
        else:
            self.flip()


class DeadBallHit(Activity):
    """Hit a non-moving grounded ball toward the opponent's goal."""

    def step_0(self):
        path = control.make_strike_path(
            self.bot.car,
            self.bot.ball,
            self.bot.ball.to(self.bot.field.opp_goal_center),
            segment_angle=pi / 8,
            segment_len=300,
        )
        self.move = FollowPath(self.bot, path, cut=0.25)
        self.next_step()

    def step_1(self):
        try:
            self.move()
        except ActivityDone:
            self.done = True


class CutShot(Activity):
    """Cut-in shot on a rolling ball."""

    flip = None
    ball_dir = None

    def shoot_from(self) -> Vec3:
        ball, car, field = self.bot.ball, self.bot.car, self.bot.field
        if ball.dot(field.fwd) > -2000:
            # offensive
            from_ball = field.opp_goal_center.to(ball).flat().rescale(500)
            from_ball += ball.vel.flat() * 0.5
        else:
            # defensive
            from_ball = ball.to(field.own_goal_center).flat().rescale(500)
        return ball.position + from_ball

    def step_0(self):
        bot, ball, car, field = self.bot, self.bot.ball, self.bot.car, self.bot.field
        if self.ball_dir is None:
            self.ball_dir = ball.vel.normalized()
        if ball.vel.normalized().dot(self.ball_dir) < 0.98:
            self.done = True
        bot.con.throttle = 1
        target = self.shoot_from()
        control.steer_to(bot, target)
        if car.dist(target) < 50:
            self.next_step()
        elif car.yaw_to(target) < 0.1:
            # pick up speed if needed
            if car.boost > 50:
                bot.con.boost = car.spd < 2250
            else:
                spd_to = max(1, car.rel_vel(ball).dot(car.to(target).normalized()))
                time_to = car.dist(target) / spd_to
                if time_to > 4 and 800 < car.spd < 2100:
                    self.prev_step = 0
                    self.next_step("flip")

    def step_1(self):
        bot, ball, car, field = self.bot, self.bot.ball, self.bot.car, self.bot.field
        if ball.vel.normalized().dot(self.ball_dir) < 0.98:
            self.done = True
        bot.con.throttle = 1
        control.steer_to(bot, ball)
        if car.yaw_to(ball) < 0.1:
            self.next_step()

    def step_2(self):
        bot, ball, car, field = self.bot, self.bot.ball, self.bot.car, self.bot.field
        if ball.vel.normalized().dot(self.ball_dir) < 0.98:
            self.done = True
        bot.con.throttle = 1
        control.steer_to(bot, ball)
        bot.con.boost = car.spd < 2250
        if car.spd_to(ball) < 0:
            self.done = True

    def step_flip(self):
        if self.flip is None:
            self.flip = FrontFlip(self.bot)
        self.flip()
        if self.flip.done:
            self.flip = None
            self.bot.clear_controls()
            self.next_step(self.prev_step)


class DefendAtPost(Activity):
    def __init__(self, bot: RamenBot, dir: float):
        super().__init__(bot)
        target = (
            self.bot.field.own_goal_center.flat()
            + self.bot.field.fwd * 150
            + dir * 1000 * self.bot.field.left
        )
        self.path = control.make_destination_path(
            target, dir * self.bot.field.left, segment_len=300
        )
        self.move = FollowPath(self.bot, self.path)

    def step_0(self):
        try:
            self.move()
        except ActivityDone:
            self.done = True
