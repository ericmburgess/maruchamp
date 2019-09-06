from vitamins.math import clamp
from vitamins.geometry import Vec3
from vitamins.match.base import Location
from vitamins.match.match import Match


def ball_on_wall_curve() -> float:
    ball = Match.ball
    field = Match.field
    x_dist = field.to_side_wall - abs(ball.x) - ball.radius
    y_dist = field.to_end_wall - abs(ball.y) - ball.radius
    z_dist = ball.z - ball.radius
    return clamp(1 - max(z_dist / 500, min(x_dist, y_dist) / 500), 0, 1)


def ball_distance_advantage(max_distance: float = 1000) -> float:
    return 0.5 + clamp(
        Match.opponent_car.distance(Match.ball) - Match.agent_car.distance(Match.ball),
        -max_distance,
        max_distance,
    ) / (2 * max_distance)


def ndot(v1: Vec3, v2: Vec3) -> float:
    return 0.5 + v1.ndot(v2) / 2


def ball_rolling_on_ground() -> float:
    return clamp(
        1 - (Match.ball.z - Match.ball.radius) / 200 - abs(Match.ball.velocity.z) / 500,
        0,
        1,
    )


def good_position(spot: Location) -> float:
    """Score how good it is to be in the given location."""
    score = 0
    ball = Match.predict_ball(dt=2)
    # Wrong side of the ball?
    score -= max(0, spot.to(ball).dot(Match.field.backward) / 1000)
    # Differential distance to ball:
    score += clamp(
        Match.opponent_car.distance(Match.ball) - spot.distance(Match.ball) / 2000
    )
    return clamp(score, 0, 1)


def high_ball() -> float:
    score = 0
    score += (Match.ball.z - Match.ball.radius) / 2000
    score += Match.ball.velocity.z / 2000
    return clamp(score, 0, 1)


def rolling_into_corner() -> float:
    """Is the ball rolling into a corner (toward the goal)?"""
    ball = Match.ball
    field = Match.field
    x_dist = field.to_side_wall - abs(ball.x) - ball.radius
    score = 1
    score -= x_dist / 500
    score -= abs(ball.velocity.x) / 500
    score -= max(0, 500 - abs(ball.velocity.y)) / 500
    return clamp(score, 0, 1)
