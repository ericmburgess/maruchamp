"""vitamins.match.prediction -- routines for predicting the future."""
from typing import Callable, List

from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction

from vitamins.match.ball import Ball
from vitamins.geometry import Vec3
from vitamins import draw
from vitamins.math import clamp


class BallPredictor:
    ready: bool = True
    valid: bool = True
    max_bounces: int = 5
    bounce_threshold: float = 300
    on_goal: List[bool] = [False, False]

    def __init__(self, prediction_function: Callable[[], BallPrediction]):
        self.prediction_function = prediction_function

    def update(self, packet: GameTickPacket):
        self.game_time = packet.game_info.seconds_elapsed
        self.prediction = self.prediction_function()

    def predict(self, dt: float) -> Ball:
        """Return a Ball instance predicted `dt` match seconds into the future."""
        coarse_scan = 16  # step size for initial scan of slices
        t = clamp(
            self.game_time + dt,
            self.prediction.slices[0].game_seconds,
            self.prediction.slices[self.prediction.num_slices - 1].game_seconds,
        )
        index = 0
        for index in range(0, self.prediction.num_slices - coarse_scan, coarse_scan):
            if self.prediction.slices[index + coarse_scan].game_seconds > t:
                break
        while (
            index + 1 < self.prediction.num_slices
            and self.prediction.slices[index].game_seconds <= t
        ):
            index += 1
        phys = self.prediction.slices[index].physics
        return Ball(phys=phys, time=self.prediction.slices[index].game_seconds)

    def next_bounce(self, game_time: float = 0) -> Ball:
        """Return the first bounce after the specified match time. If there is no bounce
        in the predicted ball path, return the last predicted moment.
        """
        # Todo: this is worth optimizing (tested)
        for i in range(1, self.prediction.num_slices):
            dv = Vec3(self.prediction.slices[i].physics.velocity) - Vec3(
                self.prediction.slices[i - 1].physics.velocity
            )
            if i + 1 == self.prediction.num_slices or (
                self.prediction.slices[i].game_seconds > game_time
                and dv.length() > self.bounce_threshold
            ):
                ball = Ball(
                    phys=self.prediction.slices[i].physics,
                    time=self.prediction.slices[i].game_seconds,
                )
                ball.dv = dv
                return ball

    def next_ground(self, game_time: float = 0, z: float = 0) -> Ball:
        """Return the first time the ball will touch the ground after the specified
        game time. If it will not touch during the prediction period, just return the
        last predicted moment. If `z` is given, returns the first time when the z level
        of the ball is lower than `z`.
        """
        # Todo: this is worth optimizing (tested)
        for i in range(self.prediction.num_slices):
            if i + 1 == self.prediction.num_slices or (
                self.prediction.slices[i].physics.location.z - Ball.radius - z < 10
                and self.prediction.slices[i].game_seconds > game_time
            ):
                return Ball(
                    phys=self.prediction.slices[i].physics,
                    time=self.prediction.slices[i].game_seconds,
                )

    def draw_path(self, path_color="white", step=4):
        draw.polyline_3d(
            [
                self.prediction.slices[i].physics.location
                for i in range(0, self.prediction.num_slices, step)
            ],
            color=path_color,
        )
