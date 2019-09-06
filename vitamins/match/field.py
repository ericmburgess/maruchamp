"""vitamins.match.field -- classes to represent the field and boosts."""
from typing import List

from rlbot.utils.structures.game_data_struct import FieldInfoPacket, GameTickPacket

from vitamins.geometry import Vec3, Orientation
from vitamins.match.base import Location, OrientedObject


class BoostPickup(Location):
    """Boost pickup. Duh."""

    def __init__(self, location, index: int, is_big: bool):
        super().__init__(location)
        self.index = index
        self.is_big = is_big
        self.is_ready = False
        self.timer = 0


class Field(OrientedObject):
    """Represents the field of play. It is an `OrientedObject`, therefore it has `up`,
    `down`, `forward`, `backward`, `left`, and `right` directions. These are set
    according to the bot's team, so that `forward` is the direction from own goal toward
    opponent's goal, and `left` and `right` are relative to that. (`up` and `down` are
    just up and down no matter what team you're on.)

    If you use these directions in your code instead of absolute positions (e.g. instead
    of `Match.ball.y`, using `Match.ball.dot(Match.field.forward)`, then you never have
    to care about what team you're on.
    """

    to_side_wall = 4096
    to_end_wall = 5120
    to_ceiling = 2044
    goal_height = 642.775
    goal_width = 2 * 892.755
    own_goal_center: Location
    own_left_post: Location
    own_right_post: Location
    opp_goal_center: Location
    opp_left_post: Location
    opp_right_post: Location
    boosts: List[BoostPickup]
    big_boosts: List[BoostPickup]
    little_boosts: List[BoostPickup]
    boostBL: BoostPickup
    boostBR: BoostPickup
    boostML: BoostPickup
    boostMR: BoostPickup
    boostFL: BoostPickup
    boostFR: BoostPickup

    def __init__(self, team: int, field_info_packet: FieldInfoPacket):
        orientation = Orientation(Vec3(0))
        orientation.up = Vec3(0, 0, 1)
        orientation.right = Vec3(1 if team else -1, 0, 0)
        orientation.forward = Vec3(0, -1 if team else 1, 0)
        super().__init__(orientation=orientation)
        self.boosts = []
        self._init_boosts(field_info_packet)
        self._init_goals()

    @property
    def center(self) -> Location:
        """Returns the `Location` at the center of the field. In most cases you can just
        use `field` instead of `field.center`, but it might make the code more self-
        explanatory.
        """
        return Location(position=self.position)

    def _init_goals(self):
        goal_width = 1786
        self.opp_goal_center = Location(5120 * self.forward)
        self.own_goal_center = Location(5120 * self.backward)
        self.own_left_post = self.own_goal_center + (goal_width / 2) * self.left
        self.own_right_post = self.own_goal_center + (goal_width / 2) * self.right
        self.opp_left_post = self.opp_goal_center + (goal_width / 2) * self.right
        self.opp_right_post = self.opp_goal_center + (goal_width / 2) * self.left

    def _init_boosts(self, field_info_packet: FieldInfoPacket):
        for i in range(field_info_packet.num_boosts):
            boost = field_info_packet.boost_pads[i]
            self.boosts.append(BoostPickup(boost.location, i, boost.is_full_boost))
        self.big_boosts = [b for b in self.boosts if b.is_big]
        self.little_boosts = [b for b in self.boosts if not b.is_big]
        for b in self.big_boosts:
            x = b.dot(self.left)
            y = b.dot(self.forward)
            if y < -1000:
                if x > 0:
                    self.boostBL = b
                else:
                    self.boostBR = b
            elif y > 1000:
                if x > 0:
                    self.boostFL = b
                else:
                    self.boostFR = b
            else:
                if x > 0:
                    self.boostML = b
                else:
                    self.boostMR = b

    def update(self, packet: GameTickPacket):
        """Update from match tick packet (to refresh the boost pickup status)."""
        for i in range(packet.num_boost):
            self.boosts[i].is_ready = packet.game_boosts[i].is_active
            self.boosts[i].timer = packet.game_boosts[i].timer

    def is_near_wall(self, pos: Location, dist=500):
        """Return True if the location is close to a wall."""
        return (
            abs(pos.x) + dist > self.to_side_wall
            or abs(pos.y) + dist > self.to_end_wall
        )
