from vitamins.activity import Activity

from ramen import control


class DumbKickoff(Activity):
    def step_0(self):
        self.bot.con.throttle = 1
        control.turn_toward(self.bot, self.bot.ball)
        self.bot.con.boost = self.bot.car.spd < 2300
        if self.bot.ball.spd > 50:
            self.done = True


class JumpKickoff(Activity):
    def step_0(self):
        self.bot.con.throttle = 1
        control.turn_toward(self.bot, self.bot.ball)
        self.bot.con.boost = self.bot.car.spd < 2300
        if self.bot.car.dist(self.bot.ball) < 400:
            self.bot.con.jump = True
        if self.bot.ball.spd > 50:
            self.bot.clear_controls()
            self.done = True


class FlipKickoff(Activity):
    def step_0(self):
        self.bot.con.throttle = 1
        self.bot.con.boost = True
        control.turn_toward(self.bot, self.bot.ball)
        self.status = f"{self.bot.car.yaw_to(self.bot.ball):.2f}"
        if self.bot.car.yaw_to(self.bot.ball) < 0.01:
            self.bot.con.steer = 0
            self.next_step()

    def step_1(self):
        self.status = f"{self.bot.car.yaw_to(self.bot.ball):.2f}"
        if self.bot.car.spd > 1800:
            self.bot.con.boost = False
            self.bot.con.yaw = 0
            self.bot.con.steer = 0
            self.bot.con.roll = 0
            self.bot.con.jump = True
            self.next_step()

    def step_2(self):
        if self.bot.car.vel.z > 10:
            self.bot.con.jump = False
            self.bot.con.pitch = -1
            self.next_step(sleep=15)

    def step_3(self):
        self.bot.con.jump = True
        if self.bot.car.spd > 2000:
            self.bot.con.pitch = 0
            self.bot.con.jump = False
            self.next_step()

    def step_4(self):
        control.turn_toward(self.bot, self.bot.ball)
        if self.bot.ball.spd > 50:
            self.done = True
