"""vitamins.match.car -- Class representing a single rocket car."""
from rlbot.utils.structures.game_data_struct import GameTickPacket, PlayerInfo

from vitamins.match.base import OrientedObject
from vitamins.match.hitbox import Hitbox
from vitamins.geometry import Vec3, Orientation


class Car(OrientedObject):
    """Represents a rocket car."""

    def __init__(self, index: int, packet: GameTickPacket):
        super().__init__()
        self.index = index
        self.car_info: PlayerInfo = packet.game_cars[index]
        self.hitbox = Hitbox(self, self.car_info.hitbox.width)
        self.update(packet)

    @property
    def name(self) -> str:
        return self.car_info.name

    @property
    def team(self) -> int:
        return self.car_info.team

    @property
    def boost(self) -> float:
        return self.car_info.boost

    @property
    def has_wheel_contact(self) -> bool:
        return self.car_info.has_wheel_contact

    @property
    def is_supersonic(self) -> bool:
        return self.car_info.is_supersonic

    @property
    def is_bot(self) -> bool:
        return self.car_info.is_bot

    def update(self, packet: GameTickPacket):
        self.car_info = packet.game_cars[self.index]
        physics = self.car_info.physics
        self.position = Vec3(physics.location)
        self.velocity = Vec3(physics.velocity)
        self.angular_velocity = Vec3(physics.angular_velocity)
        self.orientation = Orientation(physics.rotation)
