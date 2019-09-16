from typing import Callable

from vitamins import draw, math
from vitamins.match.base import Location
from vitamins.match.match import Match

from ramen.action import Action
from ramen.control import steer_to

from maruchamp import ideas
from maruchamp.actions.basic import FrontFlip


class JustDrive(Action):
    interruptible = True

    def step_0(self):
        Match.agent.throttle(1)
        Match.agent.steer(0)


class DriveToLocation(Action):
    interruptible = True

    def __init__(
        self, target: Location = None, target_func: Callable[[], Location] = None
    ):
        super().__init__()
        self.target = target
        self.target_func = target_func

    def before(self):
        if self.target_func is not None:
            self.target = self.target_func()
        draw.line_3d(Match.agent_car, self.target, "white")

    def step_0(self):
        # Decide if we want to reverse and half flip:
        if (
            abs(Match.agent_car.yaw_to(self.target)) > 7 * math.pi / 8
            and Match.agent_car.forward_speed < 200
        ):
            self.step(2)
        else:
            self.step(1)

    def step_1(self):
        yaw = Match.agent_car.yaw_to(self.target)
        if Match.agent_car.velocity.length() < 750:
            if abs(yaw > math.pi / 4):
                if Match.agent_car.up.dot(Match.field.up) > 0.99:
                    # do a wiggle turn until we get closer to our target heading:
                    self.do_action(
                        WiggleTurn(
                            target=self.target,
                            target_func=self.target_func,
                            yaw_threshold=0.3,
                            handbrake_threshold=0.5,
                        )
                    )

        Match.agent.clear_controls()
        Match.agent.throttle(1)
        steer_to(self.target)
        if yaw < 0.01:
            spd = Match.agent_car.speed_toward(self.target)
            dist = Match.agent_car.distance(self.target)
            if spd <= 0 or dist / spd > 4:
                if Match.agent_car.boost > 30:
                    if (
                        Match.agent_car.velocity.ndot(Match.agent_car.to(self.target))
                        > 0.98
                    ):
                        if Match.agent_car.has_wheel_contact:
                            Match.agent.boost(Match.agent_car.speed < 2300)
                elif ideas.ready_to_front_flip(self.target):
                    if Match.agent_car.forward_speed > 1000:
                        self.do_action(FrontFlip())
        # Decide if we want to reverse and half flip:
        if (
            abs(Match.agent_car.yaw_to(self.target)) > math.pi / 2
            and Match.agent_car.velocity.dot(Match.agent_car.forward) < 500
        ):
            self.step(2)
        else:
            self.step(1)

    def step_2(self):
        Match.agent.clear_controls()
        Match.agent.throttle(-1)
        steer_to(self.target)
        if ideas.ready_to_half_flip(self.target):
            self.do_action(HalfFlip())
            self.step(0)
        # Decide if we want to reverse and half flip:
        if (
            abs(Match.agent_car.yaw_to(self.target)) > math.pi / 2
            and Match.agent_car.velocity.dot(Match.agent_car.forward) < 500
        ):
            self.step(2)
        else:
            self.step(1)


class TrackLocation(Action):
    interruptible = True
    """Try to stay on a location we're already near."""

    def __init__(self, target_func: Callable[[], Location]):
        super().__init__()
        self.target_func = target_func

    def step_0(self):
        target = self.target_func()
        draw.cross(target, 20, 7, "orange")
        dist = Match.agent_car.distance(target)
        # spd = Match.agent_car.speed_toward(target)
        # todo: attain velocity to reach target in 1/2 second from now
        if Match.agent_car.to(target).dot(Match.agent_car.forward) > 0:
            Match.agent.throttle(dist / 50)
        else:
            Match.agent.throttle(-dist / 50)
        steer_to(target, no_handbrake=True)


class WiggleTurn(Action):
    interruptible = True
    speed_threshold: float = 1

    def __init__(
        self,
        target: Location = None,
        target_func: Callable[[], Location] = None,
        yaw_threshold: float = 0.1,
        handbrake_threshold: float = 0.2,
    ):
        super().__init__()
        self.target = target
        self.target_func = target_func
        self.yaw_threshold = yaw_threshold
        self.handbrake_threshold = handbrake_threshold
        self.throttle = 1

    def before(self):
        if self.target_func is not None:
            self.target = self.target_func()
        draw.line_3d(Match.agent_car, self.target, "white")

    def step_0(self):
        Match.agent.clear_controls()
        if Match.agent_car.forward_speed > self.speed_threshold:
            self.throttle = -1
        elif Match.agent_car.forward_speed < -self.speed_threshold:
            self.throttle = 1
        Match.agent.throttle(self.throttle)
        yaw = Match.agent_car.yaw_to(self.target)
        if abs(yaw) < self.yaw_threshold:
            self.done = True
        else:
            Match.agent.steer(math.copysign(1, yaw * Match.agent_car.forward_speed))
            Match.agent.steer(math.copysign(1, yaw * self.throttle))
        Match.agent.handbrake(yaw > self.handbrake_threshold)
        # print(
        #     f"throttle: {Match.agent.controls.throttle}, speed: {Match.agent_car.forward_speed}"
        # )


class HalfFlip(Action):
    def before(self):
        if self.current_step > 1 and Match.agent_car.has_wheel_contact:
            self.done = True

    def step_0(self):
        Match.agent.clear_controls()
        Match.agent.throttle(-1)
        if Match.agent_car.has_wheel_contact:
            if Match.agent_car.velocity.ndot(Match.agent_car.backward) > 0.95:
                if Match.agent_car.velocity.dot(Match.agent_car.backward) > 500:
                    self.step(1)

    def step_1(self):
        Match.agent.jump()
        if not Match.agent_car.has_wheel_contact:
            Match.agent.jump(False)
            self.step(2, ms=200)

    def step_2(self):
        Match.agent.pitch(1)
        self.step(3, ms=24)

    def step_3(self):
        Match.agent.pitch(1)
        Match.agent.jump()
        self.step(4, ms=200)

    def step_4(self):
        Match.agent.clear_controls()
        Match.agent.pitch(-1)
        Match.agent.roll(1)
        Match.agent.throttle(1)
        if abs(Match.agent_car.up.ndot(Match.field.up)) > 0.95:
            Match.agent.clear_controls()
            self.done = True
