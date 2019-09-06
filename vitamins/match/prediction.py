"""vitamins.match.prediction -- routines for predicting the future."""
from typing import List

from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction

from vitamins.match.ball import Ball
from vitamins.geometry import Vec3
from vitamins.util import perf_counter_ns
from vitamins import draw
from vitamins.math import clamp


class BallPredictor:
    game_time: float = 0
    valid: bool = True  # Whether the prediction is still accurate
    prediction: BallPrediction = None
    prediction_interval: float = 3.0
    accuracy_threshold_velocity: float = 30
    max_bounces: int = 5
    bounce_threshold: float = 300

    def __init__(self, prediction: BallPrediction):
        self.prediction = prediction
        self.slices_analyzed = 0
        self.index_now = 0
        self.bounces = []
        self.roll_time: float = None
        self.on_goal: List[bool] = [False, False]

    @property
    def age(self):
        return self.game_time - self.prediction.slices[0].game_seconds

    @property
    def ready(self):
        return self.slices_analyzed == self.prediction.num_slices

    def update(self, packet: GameTickPacket):
        self.game_time = packet.game_info.seconds_elapsed
        if not self.ready:
            self.analyze()
        if self.valid:
            self.check_prediction(packet)

    def check_prediction(self, packet: GameTickPacket):
        """Check the predicted ball against the actual current one."""
        actual_ball_velocity = Vec3(packet.game_ball.physics.velocity)
        # Advance to the current game time in our prediction structure:
        while self.prediction.slices[self.index_now + 1].game_seconds <= self.game_time:
            self.index_now += 1
            if self.index_now >= self.prediction.num_slices:
                self.valid = False
                return
        # Make sure we're still close to the reality:
        self.valid = (
            actual_ball_velocity
            - self.prediction.slices[self.index_now].physics.velocity
        ).length() < self.accuracy_threshold_velocity

    def analyze(self, max_ms: float = 2):
        stop_ns = perf_counter_ns() + max_ms * 1e6
        while self.slices_analyzed < self.prediction.num_slices:
            current_slice = self.prediction.slices[self.slices_analyzed]

            # Detect bouncing ball:
            if self.slices_analyzed > 0:
                previous_slice = self.prediction.slices[self.slices_analyzed - 1]
                if len(self.bounces) < self.max_bounces:
                    v1 = Vec3(current_slice.physics.velocity)
                    v2 = Vec3(previous_slice.physics.velocity)
                    if (v1 - v2).length() > self.bounce_threshold:
                        self.bounces.append((self.slices_analyzed - 1, v1 - v2))

            # Detect rolling ball:
            if self.roll_time is None:
                if abs(current_slice.physics.velocity.z) < self.bounce_threshold / 2:
                    if current_slice.physics.location.z - Ball.radius < 30:
                        self.roll_time = self.slices_analyzed

            # Detect ball on goal:
            if current_slice.physics.location.y < -5120:
                self.on_goal[0] = True
            elif current_slice.physics.location.y > 5120:
                self.on_goal[1] = True

            self.slices_analyzed += 1
            if perf_counter_ns() > stop_ns:
                return

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
        while self.prediction.slices[index].game_seconds <= t:
            index += 1
        phys = self.prediction.slices[index].physics
        return Ball(phys=phys, time=self.prediction.slices[index].game_seconds)

    def next_bounce(self, game_time: float, min_dv: float = 500) -> Ball:
        """Return the first bounce after the specified match time."""
        # If there is no bounce in the prediction (should be super rare), then just
        # just return the last moment in the prediction:
        bounce_slice, bounce_dv = self.prediction.num_slices - 1, 0.0
        for i, dv in self.bounces:
            if (
                self.prediction.slices[i].game_seconds > game_time
                and abs(dv.z) >= min_dv
            ):
                bounce_slice, bounce_dv = i, dv
        b = Ball(
            phys=self.prediction.slices[bounce_slice].physics,
            time=self.prediction.slices[bounce_slice].game_seconds,
        )
        b.dv = bounce_dv
        return b

    def draw_path(self, path_color="white", roll_color="cyan", step=4):
        roll = self.roll_time or self.prediction.num_slices
        if roll > step:
            draw.polyline_3d(
                [
                    self.prediction.slices[i].physics.location
                    for i in range(0, roll, step)
                ],
                color=path_color,
            )
        if roll < self.prediction.num_slices - step - 1:
            draw.polyline_3d(
                [
                    self.prediction.slices[i].physics.location
                    for i in range(roll, self.prediction.num_slices, step)
                ],
                color=roll_color,
            )

    def draw_bounces(self, color="red"):
        for i, dv in self.bounces:
            draw.cross(self.prediction.slices[i].physics.location, color=color)
