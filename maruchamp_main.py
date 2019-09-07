from typing import List

from vitamins import math, draw
from vitamins.geometry import Vec3
from vitamins.match.match import Match, Ball
from vitamins.match.field import BoostPickup
from vitamins.util import TickStats, perf_counter_ns

from ramen.agent import TaskAgent, Task
from ramen.action import Action
from ramen import control

from maruchamp.actions.basic import KillAngularVelocity
from maruchamp.actions import driving
from maruchamp.tasks.kickoff import FlipAtBallKickoff
from maruchamp import ideas, scores


class BallChase(Task):
    def score(self):
        return 1.0

    def enter(self):
        self.do_action(driving.DriveToLocation(target=Match.ball))


class JustDrive(Task):
    def score(self):
        return 1.0 if Match.agent_car.has_wheel_contact else 0.0

    def enter(self):
        self.do_action(driving.JustDrive())

    def monitor_action(self, action: Action):
        Match.agent.steer(Match.agent_car.right.dot(Match.field.up))


class JustWiggle(Task):
    done = False

    def score(self):
        return 0 if self.done else 1

    def enter(self):
        self.do_action(driving.WiggleTurn(Match.ball, yaw_threshold=0))

    def monitor_action(self, action: Action):
        self.done = self.action.done

    def leave(self):
        self.done = False


class BlockBall(Task):
    """Just sit in a place where the opponent is likely to hit it into us."""

    def score(self):
        s = scores.ball_on_wall_curve() * 0.6
        s += max(
            0.0,
            (400 - Match.agent_car.distance(self.across_ball_from_opponent())) / 600,
        )
        s = min(
            s,
            1 - Match.agent_car.to(Match.opponent_car).dot(Match.field.backward) / 100,
        )
        return math.clamp(s, 0, 1)

    @staticmethod
    def across_ball_from_opponent():
        return Match.ball.flat().distance_toward(Match.opponent_car.flat(), -150)

    def enter(self):
        self.do_action(driving.TrackLocation(self.across_ball_from_opponent))


class WheelsDownRoll(Task):
    """Get the wheels pointed down using roll only."""

    def score(self):
        if Match.agent_car.has_wheel_contact:
            return 0
        elif Match.time - Match.info.get("frontflip_time", 0) < 1.0:
            return 0
        else:
            in_air = math.clamp((Match.agent_car.z - 50) / 50, 0, 1)
            levelness = 1 - abs(Match.agent_car.forward.dot(Match.field.up))
            need_roll = math.clamp(
                10 * scores.ndot(Match.agent_car.up, Match.field.down), 0, 1
            )
            return min(in_air, levelness, need_roll)

    def enter(self):
        self.target_down = Match.field.down
        self.target_dot = 0.94
        self.strength = 0.5
        self.set_controls()
        self.status = "spin"

    def set_controls(self):
        # spin = Match.agent_car.down.cross(self.target_down)
        # self.to_roll = spin.dot(Match.agent_car.backward)
        # d = max(abs(self.to_roll), 1e-3) / self.strength
        # self.to_roll = math.clamp(self.to_roll / d)
        if Match.agent_car.right.dot(Match.field.up) > 0:
            self.to_roll = 1
        else:
            self.to_roll = -1

    def run(self):
        Match.agent.clear_controls()
        Match.agent.roll(self.to_roll)
        if Match.agent_car.down.dot(self.target_down) > self.target_dot:
            self.do_action(KillAngularVelocity())
            self.status = f"stop turning"


class NoseToFlatVelocity(Task):
    """Get the nose pointed level to the ground and aimed the way the car is flying
     using yaw and pitch.
     """

    def score(self):
        flat_velocity = Match.agent_car.velocity.flat()
        if Match.agent_car.has_wheel_contact or Match.agent_car.speed < 0.1:
            return 0
        elif Match.time - Match.info.get("frontflip_time", 0) < 1.0:
            return 0
        else:
            in_air = math.clamp((Match.agent_car.z - 50) / 50, 0, 1)
            return in_air * -scores.ndot(flat_velocity, Match.agent_car.forward)

    def enter(self):
        self.target_dot = 0.96
        self.target_nose = Match.agent_car.velocity.flat().normalized()
        self.strength = 0.5
        self.set_controls()
        self.status = "spin"

    def set_controls(self):
        spin = Match.agent_car.forward.cross(self.target_nose)
        self.to_yaw = spin.dot(Match.agent_car.up)
        self.to_pitch = spin.dot(Match.agent_car.left)
        d = max(abs(self.to_yaw), abs(self.to_pitch), 1e-3) / self.strength
        self.to_yaw, self.to_pitch = (
            math.clamp(self.to_yaw / d),
            math.clamp(self.to_pitch / d),
        )

    def run(self):
        Match.agent.clear_controls()
        Match.agent.yaw(self.to_yaw)
        Match.agent.pitch(self.to_pitch)
        if Match.agent_car.forward.dot(self.target_nose) > self.target_dot:
            self.do_action(KillAngularVelocity())
            self.status = f"stop turning"


class PushBallToGoal(Task):
    dt = 0

    def score(self):
        future_ball = Match.predict_ball(self.dt)
        ideal_direction = ideas.desired_ball_direction(future_ball)
        touch_direction = -Match.ball.velocity.perp(ideal_direction)
        final_direction = (ideal_direction + touch_direction / 100).normalized()
        final_direction = touch_direction.normalized()
        return math.clamp(
            min(
                scores.ndot(Match.agent_car.to(Match.ball), final_direction),
                scores.ball_rolling_on_ground(),
                1 - max(0.0, (Match.agent_car.dot(Match.field.forward) - 4500) / 600),
                1 - Match.agent_car.to(Match.ball).dot(Match.field.backward) / 300,
            ),
            0,
            1,
        )

    def enter(self):
        self.dt = 0

    def leave(self):
        self.dt = 0

    @staticmethod
    def ball_offset(ball: Ball, direction: Vec3) -> Vec3:
        """Where we should be driving to. At the ball if it's going where we want it to,
        off to the side if we need to steer it.
        """
        right = Match.field.up.cross(Match.agent_car.to(ball).flat()).normalized()
        offset = -500 * right * right.dot(direction)
        draw.cross(ball + offset, color="yellow")
        return offset

    def run(self):
        future_ball = Match.predict_ball(self.dt)
        ideal_direction = ideas.desired_ball_direction(future_ball)
        touch_direction = -Match.ball.velocity.perp(
            Match.ball.to(Match.field.opp_goal_center)
        )
        final_direction = (ideal_direction + touch_direction / 100).normalized()
        final_direction = touch_direction.normalized()
        future_ball.position -= future_ball.radius * final_direction
        if Match.agent_car.to(future_ball).dot(Match.agent_car.right) > 0.2:
            box_location = "FUR"
        elif Match.agent_car.to(future_ball).dot(Match.agent_car.right) < -0.2:
            box_location = "FUL"
        else:
            box_location = "FU"
        distance = Match.agent_car.hitbox(box_location).distance(future_ball.flat())
        speed_to = max(1.0, Match.agent_car.speed)
        self.dt = min(5, distance / speed_to)
        control.steer_to(future_ball)
        Match.agent.throttle(1)
        # todo: this is experimental
        Match.agent.boost(False)
        if Match.agent_car.distance(Match.ball) < 250:
            if Match.agent_car.speed < Match.ball.speed + 20:
                if Match.agent_car.yaw_to(future_ball) < math.pi / 8:
                    if Match.agent_car.to(Match.ball).dot(final_direction) > -0.2:
                        Match.agent.boost()
        # todo: VERY experimental!
        Match.agent.boost(
            Match.agent_car.yaw_to(future_ball) < 0.1
            and Match.agent_car.to(Match.ball).dot(Match.field.forward) < 0
            # and Match.agent_car.to(Match.ball).ndot(final_direction) > 0.99
        )
        yaw = Match.ball.velocity.yaw_to(ideal_direction)
        if Match.agent_car.distance(Match.ball) < 150:
            Match.agent.controls.steer = math.clamp(Match.agent.controls.steer - yaw)
        self.status = f"dt={self.dt:.2f}"


class GetNearestBigBoost(Task):
    def score(self):
        s = 0.3 + 0.4 * scores.high_ball()
        self.boost_pickup: BoostPickup = Match.agent_car.nearest(Match.field.big_boosts)
        if self.boost_pickup.is_ready:
            s -= Match.agent_car.distance(self.boost_pickup) / 3000
            s -= (
                (
                    1
                    - Match.agent_car.velocity.ndot(
                        Match.agent_car.to(self.boost_pickup)
                    )
                )
                * Match.agent_car.speed
                / 2000
            )
            s += max(scores.good_position(self.boost_pickup), 0.5) / 2
        else:
            s = 0
        return math.clamp(min(s, 1 - Match.agent_car.boost / 100), 0, 1)

    def run(self):
        self.do_action(driving.DriveToLocation(target=self.boost_pickup))

    def monitor_action(self, action: Action):
        Match.agent.boost()
        if not self.boost_pickup.is_ready:
            self.cancel_action()


class StraightShotRollingBall(Task):
    """If the ball is rolling at us and we're pointed toward it, and the direction
    isn't awful, then just ponk it."""

    def score(self):
        score = scores.ndot(Match.ball.velocity, Match.agent_car.backward)
        score -= (
            0.025
            * max(0, abs(Match.agent_car.yaw_to(Match.ball)) - math.pi / 4)
            / (math.pi / 4)
        )
        score = min(score, scores.ball_rolling_on_ground())
        score = min(
            score, scores.ndot(Match.agent_car.to(Match.ball), Match.field.forward)
        )
        score = min(
            score,
            2 * scores.ndot(Match.agent_car.to(Match.ball), Match.agent_car.forward)
            - 1,
        )
        score = 0 if not Match.agent_car.has_wheel_contact else score
        return score

    def run(self):
        Match.agent.throttle(1)
        Match.agent.boost(True)
        # todo: see the future
        control.steer_to(Match.ball)


class Reposition(Task):
    def score(self):
        s = 0.1 + 0.6 * scores.high_ball()
        return math.clamp(s, 0, 1)

    def midpoint(self):
        fball = Match.predict_ball(1)
        if fball.dot(Match.field.forward) > 0:
            self.status = "attack"
            return fball.flat().distance_toward(
                Match.field.opp_goal_center.flat(), -600
            )
        else:
            self.status = "defend"
            return fball.flat().distance_toward(Match.field.own_goal_center.flat(), 900)

    def run(self):
        self.do_action(driving.DriveToLocation(target_func=self.midpoint))

    def leave(self):
        self.status = ""


class BounceShot(Task):
    boost_threshold: float = 0.2
    bounce = None

    def score(self):
        self.bounce = (
            self.bounce
            if self.bounce is not None
            else Match.current_prediction.next_bounce(Match.time)
        )
        if not 0 < self.bounce.time - Match.time < 4:
            self.bounce = None
            return 0.0

        draw.cross(self.bounce, 20, 7, color="red")
        dt = self.bounce.time - Match.time
        self.status = f"Time to bounce: {self.bounce.time - Match.time:.2f}s"
        yaw = Match.agent_car.yaw_to(self.bounce)
        yaw_factor = math.clamp(1 - abs(yaw), 0, 1)
        ftime, fdist, fspeed, fboost = control.simulate_drive_forward(
            speed=Match.agent_car.forward_speed,
            throttle=1,
            boost=Match.agent_car.boost,
            distance=Match.agent_car.distance(self.bounce),
        )
        if ftime > dt:
            # Try the next one:
            self.bounce = Match.current_prediction.next_bounce(self.bounce.time)
            return 0
        else:
            time_factor = 1 - ftime / dt
            return min(yaw_factor, time_factor)

    def leave(self):
        self.bounce = None

    def run(self):
        Match.agent.clear_controls()
        control.steer_to(self.bounce)
        dt = self.bounce.time - Match.time
        ftime, fdist, fspeed, fboost = control.simulate_drive_forward(
            speed=Match.agent_car.forward_speed,
            throttle=0,
            boost=0,
            distance=Match.agent_car.distance(self.bounce),
        )
        if ftime < dt:
            # Even coasting we'll get there too early, hit the brakes:
            Match.agent.throttle(-1)
            return
        ftime, fdist, fspeed, fboost = control.simulate_drive_forward(
            speed=Match.agent_car.forward_speed,
            throttle=1,
            boost=0,
            distance=Match.agent_car.distance(self.bounce),
        )
        if ftime < dt:
            # Full throttle is too fast, coast a sec:
            Match.agent.throttle(0)
            return
        elif ftime > dt + self.boost_threshold:
            # Full throttle isn't fast enough, use boost:
            Match.agent.boost(True)
        else:
            # Full throttle is about right:
            Match.agent.throttle(1)


class GitYeeted(Task):
    """Demo the opponent."""

    def score(self):
        if Match.current_prediction.on_goal[Match.agent.team]:
            return 0
        elif not Match.agent_car.has_wheel_contact or Match.agent_car.z > 50:
            return 0
        else:
            yaw = Match.agent_car.yaw_to(Match.opponent_car)
            yaw_factor = math.clamp(1 - abs(yaw), 0, 1)
            boost_needed = (2300 - Match.agent_car.speed) * 33.3 / 900
            boost_factor = math.clamp((Match.agent_car.boost - boost_needed) / 20, 0, 1)
            dist_factor = math.clamp(
                1 - Match.agent_car.distance(Match.opponent_car) / 2000, 0, 1
            )
            evasion_factor = math.clamp(Match.opponent_car.speed / 1500, 0, 1)
            on_goal_factor = (
                3 if Match.current_prediction.on_goal[1 - Match.agent.team] else 1
            )
            speed_factor = math.clamp(
                (Match.agent_car.forward_speed - 1400) / 100, 0, 1
            )
            return math.clamp(
                on_goal_factor
                * min(
                    yaw_factor, boost_factor, dist_factor, evasion_factor, speed_factor
                ),
                0,
                1,
            )

    def run(self):
        Match.agent.throttle(1)
        Match.agent.boost(True)
        dt = (
            Match.agent_car.distance(Match.opponent_car) - Match.agent_car.hitbox.length
        ) / Match.agent_car.speed_toward(Match.opponent_car)
        target = Match.opponent_car + Match.opponent_car.velocity * dt
        control.steer_to(target)
        draw.line_3d(
            Match.agent_car, target, color="red" if Match.tick % 30 < 15 else "yellow"
        )


class MaruChamp(TaskAgent):
    debug_strs = []

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.setup_tasks()
        self.debug_strs.append(
            "         wall curve: {round(100*scores.ball_on_wall_curve()):3}"
        )
        self.debug_strs.append(
            "       ball rolling: {round(100*scores.ball_rolling_on_ground()):3}"
        )
        self.debug_strs.append(
            "      good position: {round(100*scores.good_position(Match.agent_car)):3}"
        )
        self.debug_strs.append(
            "rolling into corner: {round(100*scores.rolling_into_corner()):3}"
        )
        self.debug_strs.append("          high ball: {round(100*scores.high_ball()):3}")
        self.debug_strs.append(
            "        next bounce: {Match.current_prediction.next_bounce(Match.time).time:.2f}"
        )
        self.start_stats()
        self.score_size: int = 1
        self.score_history: List[float] = [0.0] * self.score_size
        self.score_interval: float = 0.25
        self.last_score_time: float = 0

    def start_stats(self):
        interval = 1000
        self.stat_tick_ms = TickStats("tick", "ms", interval=interval, startup=300)

    def setup_tasks(self):
        self.add_task(FlipAtBallKickoff())
        self.add_task(WheelsDownRoll(), 0.8)
        self.add_task(NoseToFlatVelocity())
        self.add_task(PushBallToGoal())
        self.add_task(BlockBall(), 0.8)
        self.add_task(GetNearestBigBoost())
        self.add_task(StraightShotRollingBall())
        self.add_task(Reposition())
        self.add_task(GitYeeted())
        # self.add_task(BounceShot())
        # self.add_task(JustDrive(), 10)
        # self.add_task(JustWiggle(), 10)
        # self.add_task(BallChase(), 10)

    def draw_task_graph(self):
        if Match.time > self.last_score_time + self.score_interval:
            self.last_score_time = Match.time
            score = math.clamp(self.current_score * self.current_weight, 0, 1)
            self.score_history = self.score_history[1:] + [score]
        x, y = 50, 200
        width = 10
        height = 200
        draw.rect_2d(x, y, width, height, color="blue")
        draw.rect_2d(x, y, width, 2, color="white")
        draw.rect_2d(x, y + int(height / 2), width, 2, color="white")
        draw.rect_2d(x, y + height, width, 2, color="white")
        color = "cyan"
        bar_width = int(width / self.score_size)
        for i in range(self.score_size):
            bar_height = int(height * self.score_history[i])
            draw.rect_2d(
                x + i * bar_width,
                y + height - bar_height,
                bar_width,
                bar_height,
                filled=True,
                color=color,
            )
        task_y = y
        task_x = x + width + 5
        dy = 20
        for pair in self.tasks[:33]:
            score = round(100 * math.clamp(self.weighted_score(pair), 0, 1))
            ylevel = (100 - score) * height / 100
            task_y = max(task_y, y + ylevel)
            if pair[0] is self.current_task:
                if self.current_task.busy():
                    color = "pink"
                else:
                    color = "cyan"
            else:
                color = "white"
            draw.text(task_x, task_y, 1, f"--[{score:3}]--{pair[0]}", color=color)
            task_y += dy

    def debug(self):
        # Match.draw_prediction()
        # draw.text(50, 30, 1, f"{self.current_task}", "blue")
        if any(Match.current_prediction.on_goal):
            if Match.current_prediction.on_goal[self.team]:
                color = "red"
            else:
                color = "green"
            draw.rect_2d(50, 30, 140, 20, True, color)
            draw.text(50, 30, 1, "!! ON GOAL !!", "white")
        x, y = 50, 80
        dy = 20
        for s in self.debug_strs:
            draw.text(x, y, 1, eval(f'f"{s}"'), "white")
            y += dy
        y += dy
        self.draw_task_graph()

    def every_tick(self):
        self.tick_start = perf_counter_ns()
        # self.clear_controls()
        if len(self.tasks) == 1:
            self.setup_tasks()
        super().every_tick()
        self.debug()
        tick_ms = (perf_counter_ns() - self.tick_start) / 1e6
        self.stat_tick_ms.update(tick_ms)

    def boost(self, value: bool = True):
        value = value and Match.agent_car.speed < 2300
        super().boost(value)
