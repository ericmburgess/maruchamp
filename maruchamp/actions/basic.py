from vitamins.match.match import Match
from ramen.action import Action


class Idle(Action):
    def step_0(self):
        Match.agent.clear_controls()
        self.step(1)

    def step_1(self):
        pass


class FrontFlip(Action):
    def step_0(self):
        if Match.agent_car.has_wheel_contact:
            self.step(1)

    def step_1(self):
        Match.agent.jump()
        if not Match.agent_car.has_wheel_contact:
            Match.agent.jump(False)
            self.step(2, ms=200)

    def step_2(self):
        Match.agent.pitch(-1)
        self.step(3, ms=24)

    def step_3(self):
        Match.agent.pitch(-1)
        Match.agent.jump()
        self.step(4, ms=24)

    def step_4(self):
        Match.info["frontflip_time"] = Match.time
        self.done = True


class KillAngularVelocity(Action):
    def step_0(self):
        d = max(
            abs(Match.agent_car.yaw_rate),
            abs(Match.agent_car.roll_rate),
            abs(Match.agent_car.pitch_rate),
        )
        if d > 0.1:
            d = max(d, 0.5)
            Match.agent.yaw(-Match.agent_car.yaw_rate / d)
            Match.agent.roll(-Match.agent_car.roll_rate / d)
            Match.agent.pitch(-Match.agent_car.pitch_rate / d)
        else:
            self.done = True
