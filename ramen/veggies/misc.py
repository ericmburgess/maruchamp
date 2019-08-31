"""veggies.misc -- assorted activities."""

from vitamins.activity import Activity
from vitamins.game import Car, Location
from ramen import control
from vitamins.geometry import Orientation, Vec3
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
