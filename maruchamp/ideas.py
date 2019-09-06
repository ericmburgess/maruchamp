from vitamins import draw
from vitamins.math import clamp, pi
from vitamins.match.match import Match, Ball
from vitamins.match.base import Location
from vitamins.geometry import Vec3


def desired_ball_direction(ball: Ball = None) -> Vec3:
    """Returns a normalized vector pointing the way we want the ball to go. On offense
    it'll be into the opponent's goal; on defense, it'll be away from ours."""
    if ball is None:
        ball = Match.ball
    t = clamp(
        Match.field.own_goal_center.to(ball).dot(Match.field.forward) / 2000, 0, 1
    )
    away_from_own_goal = (
        Match.field.left if ball.dot(Match.field.left) > 0 else Match.field.right
    )
    toward_opp_goal = ball.to(Match.field.opp_goal_center).normalized()
    direction = away_from_own_goal.lerp(toward_opp_goal, t)
    # draw.line_3d(ball, ball + direction * 500, "red")
    return direction


def ready_to_front_flip(target: Location) -> bool:
    return (
        Match.agent_car.has_wheel_contact
        and Match.agent_car.angular_velocity.length() < 0.1
        and Match.agent_car.yaw_to(target) < 0.1
        and Match.agent_car.velocity.ndot(Match.agent_car.to(target)) > 0.9
        and Match.agent_car.z < 50
    )


def ready_to_half_flip(target: Location) -> bool:
    return (
        Match.agent_car.has_wheel_contact
        and Match.agent_car.angular_velocity.length() < 0.1
        and pi - abs(Match.agent_car.yaw_to(target)) < 0.3
        and Match.agent_car.velocity.ndot(Match.agent_car.to(target)) > 0.9
        and Match.agent_car.z < 50
        and Match.agent_car.up.dot(Match.field.up) > 0.96
    )
