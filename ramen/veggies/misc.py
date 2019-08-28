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


class JustDrive(Activity):
    def step_0(self):
        self.bot.con.throttle = 1
        self.bot.con.steer = 0
