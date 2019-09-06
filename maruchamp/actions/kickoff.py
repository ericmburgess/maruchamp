from vitamins.match.match import Match

from ramen.action import Action
from ramen import control

from maruchamp.actions.basic import FrontFlip


class DumbKickoff(Action):
    def step_0(self):
        Match.agent.throttle(1)
        control.steer_to(Match.ball)
        Match.agent.boost(Match.agent_car.speed < 2300)
        if Match.ball.speed > 50:
            self.done = True


class JumpKickoff(Action):
    def step_0(self):
        Match.agent.throttle(1)
        control.steer_to(Match.ball)
        Match.agent.boost(Match.agent_car.speed < 2300)
        if Match.agent_car.distance(Match.ball) < 400:
            Match.agent.jump()
        if Match.ball.speed > 50:
            Match.agent.clear_controls()
            self.done = True


class FlipIntoBallKickoff(Action):
    def step_0(self):
        Match.agent.throttle(1)
        control.steer_to(Match.ball)
        Match.agent.boost(Match.agent_car.speed < 2300)
        if Match.agent_car.distance(Match.ball) < 700:
            self.do_action(FrontFlip(), done=True)
