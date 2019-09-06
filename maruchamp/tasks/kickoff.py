from vitamins.match.match import Match

from ramen import control
from ramen.task import Task

from maruchamp.actions.basic import FrontFlip


class FlipAtBallKickoff(Task):
    flipped: bool = False

    def score(self):
        if Match.ball.x == Match.ball.y == 0:
            if Match.ball.velocity.length() < 10:
                return 200
        return -100

    def enter(self):
        self.flipped = False

    def run(self):
        Match.agent.throttle(1)
        control.steer_to(
            Match.ball.distance_toward(Match.field.opp_goal_center, -Match.ball.radius)
        )
        Match.agent.boost(Match.agent_car.speed < 2300)
        dt = Match.agent_car.distance(Match.ball) / max(
            Match.agent_car.speed_toward(Match.ball), 1e-3
        )
        if not self.flipped and dt < 0.5:
            self.do_action(FrontFlip())
            self.flipped = True
