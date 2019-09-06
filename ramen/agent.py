"""ramen.agent -- Base class for Agents."""
from functools import wraps
from operator import methodcaller
from typing import Callable, List, Tuple

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from vitamins import draw
from vitamins.geometry import Vec3
from vitamins.match.match import Match
from vitamins.match.car import Car
from vitamins.match.ball import Ball
from vitamins.match.field import Field
from vitamins.math import clamp, copysign

from ramen.task import Task


class Agent(BaseAgent):
    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.controls = SimpleControllerState()
        self.tick: int = 0
        self._was_kickoff = False

    def clear_controls(self):
        self.controls.yaw = 0
        self.controls.roll = 0
        self.controls.pitch = 0
        self.controls.steer = 0
        self.controls.throttle = 0
        self.controls.boost = False
        self.controls.handbrake = False
        self.controls.jump = False
        self.controls.use_item = False

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.renderer.begin_rendering()

        if self.tick == 0:
            # First tick setup:
            Match.initialize(self, packet)
            self.first_tick()

        Match.update(packet)

        # Call kickoff_begin at the start of a kickoff:
        if packet.game_info.is_kickoff_pause:
            if not self._was_kickoff:
                self.clear_controls()
                self.kickoff_begin()
                self._was_kickoff = True
        else:
            self._was_kickoff = False

        self.every_tick()

        self.tick += 1
        self.renderer.end_rendering()
        return self.controls

    def every_tick(self):
        pass

    def kickoff_begin(self):
        pass

    def first_tick(self):
        pass

    def steer(self, value: float):
        self.controls.steer = clamp(value)

    def throttle(self, value: float):
        self.controls.throttle = clamp(value)

    def yaw(self, value: float):
        self.controls.yaw = clamp(value)

    def pitch(self, value: float):
        self.controls.pitch = clamp(value)

    def roll(self, value: float):
        self.controls.roll = clamp(value)

    def jump(self, value: bool = True):
        self.controls.jump = value

    def boost(self, value: bool = True):
        self.controls.boost = value

    def handbrake(self, value: bool = True):
        self.controls.handbrake = value

    def use_item(self, value: bool = True):
        self.controls.use_item = value

    # todo: take this out of here:
    def steer_to(self, target: Vec3, no_handbrake=False):
        halt_sec = 0.15  # How long (estimated) it takes to halt a turn
        car = Match.agent_car
        if car.forward_speed >= 0:
            err = car.yaw_to(target)
        else:
            err = -car.yaw_to(target + 2 * target.to(car))
        if abs(err) < 0.01:
            steer = 0
        elif abs(err) < 0.05:
            steer = copysign(0.2, err)
        else:
            steer = copysign(1, err)
            if car.yaw_rate != 0:
                if 0 < err / car.yaw_rate < halt_sec:
                    steer = -steer
                if err / car.yaw_rate > 2 * halt_sec and not no_handbrake:
                    self.handbrake()
                else:
                    self.handbrake(False)
        self.steer(steer)


class TaskAgent(Agent):
    tasks: List[Tuple[Task, float]]
    task_switch_threshold: float = 0.05

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.tasks = []
        self.current_task = None
        self.current_score: float = -1
        self.current_weight: float = 0

    def add_task(self, task: Task, weight: float = 1):
        self.tasks.append((task, weight))

    def switch_task(self, new_task: Task):
        if self.current_task is not None:
            self.current_task.leave()
            self.current_task.action = None
        new_task.enter()
        self.current_task = new_task
        self.clear_controls()

    @staticmethod
    def weighted_score(pair: Tuple[Task, float]) -> float:
        task, weight = pair
        try:
            result = task.score() * weight
        except TypeError as exc:
            print(f"Tried {task} score {task.score()} * {weight}: {exc}")
            return 0
        return result

    def kickoff_begin(self):
        self.current_task = None
        self.current_score = -1

    def every_tick(self):
        if self.current_task is not None and self.current_task.busy():
            # Task can't be interrupted right now:
            self.current_task()
        else:
            if self.tasks:
                self.tasks.sort(key=self.weighted_score, reverse=True)
                if (
                    self.weighted_score(self.tasks[0])
                    >= self.current_score + self.task_switch_threshold
                ):
                    self.switch_task(self.tasks[0][0])
                    self.current_weight = self.tasks[0][1]
                if self.current_task is not None:
                    self.current_task()
                    self.current_score = self.current_task.score() * self.current_weight


class SimpleAgent1v1(Agent):
    play: Callable[[Car, Car, Ball, Field, float], None]

    def every_tick(self):
        self.clear_controls()
        self.play(
            Match.agent_car, Match.opponents[0], Match.ball, Match.field, Match.time
        )

    def first_tick(self):
        self.setup()

    def setup(self):
        pass


def state(func):
    """Function decorator for state methods."""

    @wraps(func)
    def func_wrapper(self):
        if self.current_state == func:
            return func(self)
        else:
            self.current_state = func

    return func_wrapper


class StateMachineAgent(Agent):
    current_state = None
    previous_state = None
    default_state = "none"
    clear_controls_on_state_transition = True

    def every_tick(self):
        if self.current_state is None:
            if hasattr(self, self.default_state):
                getattr(self, self.default_state)()
        else:
            if self.current_state != self.previous_state:
                new_state = self.current_state.__name__
                if self.clear_controls_on_state_transition:
                    self.clear_controls()
                if self.previous_state is None:
                    pass
                    print(f"Initial state: {new_state}")
                else:
                    prev_state = self.previous_state.__name__
                    print(f"State transition: {prev_state} -> {new_state}")
                    self.leave_state(prev_state)
                self.previous_state = self.current_state
                self.enter_state(new_state)
            self.current_state(self)

    def enter_state(self, state_name: str):
        func_name = f"{state_name}_enter"
        if hasattr(self, func_name):
            getattr(self, func_name)()

    def leave_state(self, state_name: str):
        func_name = f"{state_name}_leave"
        if hasattr(self, func_name):
            getattr(self, func_name)()
