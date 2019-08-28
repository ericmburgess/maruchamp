"""agent.py -- Base classes for RamenBots."""
from time import perf_counter_ns

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.rendering.rendering_manager import DummyRenderer

from vitamins.game import TheBall, Car, Field
from vitamins import draw
from vitamins.util import TickStats


class RamenBot(BaseAgent):
    packet: GameTickPacket
    comp_mode = False

    def initialize_agent(self):
        draw.set_renderer(self.renderer)
        self.con = SimpleControllerState()
        self.tick = 0
        self.game_time = 0
        self.on_start()
        self.last_game_time = 0
        self.tick_rate = 120
        self.last_frame_was_bad = False
        self.stat_tick_ms = TickStats("tick", "ms", interval=1000, startup=300)
        self.stat_bad_frames = TickStats("bad frames", "%", interval=1000, startup=300)

    def _on_first_tick(self):
        """First-tick setup."""
        self.field = Field(self.team, self.get_field_info())
        self.opponent_index = 1 - self.index
        # Hacky; assumes 1v1:
        self.car = Car(self.index)
        self.opponent_car = Car(self.opponent_index)
        self.ball = TheBall(self)
        self.ball.update()
        self.team = self.packet.game_cars[self.index].team
        self._renderer = self.renderer
        # self.renderer = DummyRenderer(self.renderer)
        self.on_first_tick()

    def _on_tick(self):
        self.car.update(self.packet)
        self.opponent_car.update(self.packet)
        self.field.update(self.packet)
        self.ball.update()
        self.on_tick()

    def clear_controls(self):
        c = self.con
        c.steer = 0
        c.yaw = 0
        c.roll = 0
        c.pitch = 0
        c.throttle = 0
        c.boost = False
        c.handbrake = False
        c.jump = False

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.tick_start = perf_counter_ns()
        self.last_game_time = self.game_time
        self.game_time = packet.game_info.seconds_elapsed
        self.dt = self.game_time - self.last_game_time
        self.packet = packet
        self.renderer.begin_rendering()

        if self.tick == 0:
            self._on_first_tick()
        else:
            self._on_tick()

        self.tick += 1
        self.renderer.end_rendering()
        tick_ms = (perf_counter_ns() - self.tick_start) / 1e6
        self.stat_tick_ms.update(tick_ms)
        self.stat_bad_frames.update(100 if self.last_frame_was_bad else 0)
        return self.con

    def tick_ms(self):
        """Return the number of milliseconds used so far this tick."""
        return (perf_counter_ns() - self.self.tick_start) / 1e6

    def on_first_tick(self):
        pass

    def on_retire(self):
        pass

    def on_start(self):
        pass

    def on_tick(self):
        pass

    def on_pause_tick(self):
        pass
