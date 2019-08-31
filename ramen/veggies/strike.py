"""veggies.misc -- assorted activities."""

from vitamins.activity import Activity
from vitamins.game import Car, Location
from ramen import control
from vitamins.geometry import Orientation, Vec3, Line
from vitamins.math import *
from vitamins import draw


class DeadBallHit(Activity):
    """Hit a non-moving grounded ball toward the opponent's goal."""

    def step_0(self):
        ball_to_goal = self.bot.ball.to(self.bot.field.opp_goal_center).flat()
        strike_from = self.bot.ball.position - ball_to_goal * 1000
        self.line = Line(self.bot.ball, ball_to_goal)
        self.next_step()

    def step_1(self):
        draw.line(self.line, color="red", bump_color="pink")
        h = Vec3(z=20)
        offset = self.line.offset(self.bot.car)
        draw.line_3d(
            self.bot.car.position + h, self.bot.car.position + offset + h, "cyan"
        )
