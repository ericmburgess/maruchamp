from vitamins.activity import Activity, ActivityDone
from ramen.veggies import misc

from ramen import control


class DumbKickoff(Activity):
    def step_0(self):
        self.bot.con.throttle = 1
        control.steer_to(self.bot, self.bot.ball)
        self.bot.con.boost = self.bot.car.spd < 2300
        if self.bot.ball.spd > 50:
            self.done = True


class JumpKickoff(Activity):
    def step_0(self):
        self.bot.con.throttle = 1
        control.steer_to(self.bot, self.bot.ball)
        self.bot.con.boost = self.bot.car.spd < 2300
        if self.bot.car.dist(self.bot.ball) < 400:
            self.bot.con.jump = True
        if self.bot.ball.spd > 50:
            self.bot.clear_controls()
            self.done = True


class FlipIntoBallKickoff(Activity):
    def step_0(self):
        self.bot.con.throttle = 1
        control.steer_to(self.bot, self.bot.ball)
        self.bot.con.boost = self.bot.car.spd < 2300
        if self.bot.car.dist(self.bot.ball) < 700:
            self.flip = misc.FrontFlip(self.bot)
            self.next_step()

    def step_1(self):
        try:
            self.flip()
        except ActivityDone:
            self.done = True
