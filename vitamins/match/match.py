"""vitamins.match.match -- Class for representing the current match."""
from typing import List

from rlbot.agents.base_agent import BaseAgent
from rlbot.utils.structures.game_data_struct import GameTickPacket

from vitamins import draw
from vitamins.match.ball import Ball
from vitamins.match.car import Car
from vitamins.match.field import Field
from vitamins.match.prediction import BallPredictor


class MatchAgent(BaseAgent):
    """This class exists only to make the autocomplete work right in PyCharm."""

    def clear_controls(self):
        pass

    def steer(self, value: float):
        pass

    def throttle(self, value: float):
        pass

    def yaw(self, value: float):
        pass

    def pitch(self, value: float):
        pass

    def roll(self, value: float):
        pass

    def jump(self, value: bool = True):
        pass

    def boost(self, value: bool = True):
        pass

    def handbrake(self, value: bool = True):
        pass

    def use_item(self, value: bool = True):
        pass


class Match:
    agent: MatchAgent = None
    time: float = 0
    tick: int = 0
    current_prediction: BallPredictor = None
    agent_car: Car = None
    opponent_car: Car = None
    field: Field = None
    ball: Ball = None
    cars: List[Car] = []
    teammates: List[Car] = []
    opponents: List[Car] = []
    info: dict = {}  # Place to store misc. stuff

    @classmethod
    def initialize(cls, agent: MatchAgent, packet: GameTickPacket):
        cls.agent = agent
        draw.set_renderer(agent.renderer)
        cls.field = Field(agent.team, agent.get_field_info())
        cls.cars = [Car(index=i, packet=packet) for i in range(packet.num_cars)]
        cls.agent_car = cls.cars[cls.agent.index]
        cls.teammates = [car for car in cls.cars if car.team == cls.agent.team]
        cls.opponents = [car for car in cls.cars if car.team != cls.agent.team]
        if cls.opponents:
            cls.opponent_car = cls.opponents[0]
        cls.ball = Ball(packet=packet)
        cls.current_prediction = BallPredictor(agent.get_ball_prediction_struct)
        cls.update(packet)

    @classmethod
    def update(cls, packet: GameTickPacket):
        cls.packet = packet
        cls.time = packet.game_info.seconds_elapsed
        cls.tick += 1
        for car in cls.cars:
            car.update(packet=packet)
        cls.ball.update(packet=packet)
        cls.field.update(packet=packet)
        cls.current_prediction.update(packet=packet)

    @classmethod
    def predict_ball(cls, dt: float = 0) -> Ball:
        if cls.current_prediction is None:
            return cls.ball
        else:
            return cls.current_prediction.predict(dt)

    @classmethod
    def draw_prediction(cls, step: int = 4):
        cls.current_prediction.draw_path(step=step)
        draw.cross(cls.current_prediction.next_bounce(), color="red")

    @classmethod
    def objects_1v1(cls):
        return cls.agent_car, cls.opponents[0], cls.ball, cls.field, cls.predict_ball
