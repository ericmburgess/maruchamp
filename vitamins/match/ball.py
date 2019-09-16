from rlbot.utils.structures.game_data_struct import GameTickPacket, Touch

from vitamins import draw
from vitamins.geometry import Vec3
from vitamins.match.base import OrientedObject


class Ball(OrientedObject):
    """Represents a ball. Often hypothetical, e.g. the result of asking for a prediction
    of the future ball's position.
    """

    radius: float = 92.75
    latest_touch: Touch
    roll_counter: int = 0

    def __init__(self, packet: GameTickPacket = None, phys=None, time=0):
        super().__init__()
        self.position = Vec3()
        self.velocity: Vec3 = Vec3()
        self.angular_velocity = Vec3()
        self.time = time
        self.update(packet, phys)

    def update(self, packet: GameTickPacket = None, phys=None):
        if packet is not None:
            self.latest_touch = packet.game_ball.latest_touch
            phys = packet.game_ball.physics
        self.position = Vec3(phys.location)
        self.velocity = Vec3(phys.velocity)
        self.angular_velocity = Vec3(phys.angular_velocity)
        if self.z - self.radius < 2:
            self.roll_counter += 1
        else:
            self.roll_counter = 0

    def is_rolling(self) -> bool:
        """Returns True if the ball is rolling on the ground."""
        rolling = self.roll_counter > 5
        draw.point(self, color="green" if rolling else "red")
        return rolling

    def on_ground(self) -> bool:
        """Returns True if the ball is on the ground."""
        return self.z - self.radius < 1
