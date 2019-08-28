"""maruchamp.py -- MaruChamp Rocket League bot by Ramen and Vitamins"""
from vitamins.agent import RamenBot
from vitamins.activity import ActivityDone
from vitamins.game import *
from vitamins.math import *
import vitamins.util

from ramen.veggies import kickoff, misc
from ramen import control


COMP_MODE = not vitamins.util.at_home()  # True for competition mode
print = vitamins.util.comp_print if COMP_MODE else vitamins.util.dev_print


class MaruChamp(RamenBot):
    def is_hot_reload_enabled(self):
        if COMP_MODE:
            return False
        else:
            return True

    def on_start(self):
        self.state = "soccar"
        self.prev_state = None
        self.current_activity = None

    def do(self, act: type, *args, **kwargs):
        previous_activity = self.current_activity
        if previous_activity is not None and not previous_activity.done:
            print(f"Cancelling activity {previous_activity}", end="")
        self.current_activity = act(self, *args, **kwargs)
        print(f" in favor of {self.current_activity}")

    def driving_on_wall(self):
        return self.car.z > 100 and self.car.wheel_contact

    def play_soccar(self):
        """Top level strategy routine."""
        if self.state != self.prev_state:
            print(f"State transition: {self.prev_state} -> {self.state}")
        ball, me, opp, field = self.ball, self.car, self.opponent_car, self.field

        self.renderer.draw_string_2d(
            20, 40, 1, 3, f"   State: {self.state}", self.renderer.white()
        )
        self.renderer.draw_string_2d(
            20, 60, 1, 3, f"Activity: {self.current_activity}", self.renderer.white()
        )
        ongoal = "none"
        if ball.on_own_goal:
            if ball.on_opp_goal:
                ongoal = "both!?"
            else:
                ongoal = "MINE"
        elif ball.on_opp_goal:
            ongoal = "Opp"
        col = self.renderer.white()
        self.renderer.draw_string_2d(20, 280, 1, 3, f"Ball on goal: {ongoal}", col)

        # INTERRUPTS - can knock us out of a state/activity that's not done yet:

        # Interrupt: Kickoff
        if self.packet.game_info.is_kickoff_pause and "kickoff" not in self.state:
            self.state = "kickoff start"
            self.clear_controls()
            return

        # STATE TRANSITIONS

        if self.state == "kickoff start":
            self.do(kickoff.JumpKickoff)
            self.state = "kickoff execute"

        elif self.state == "kickoff execute":
            if self.current_activity is None:
                self.state = "soccar"

        elif self.state == "soccar":
            # Choose an action based on circumstances:
            pass
        else:
            print(f"Undefined state [{self.state}]")

        self.prev_state = self.state

    def on_first_tick(self):
        self.current_activity = None
        print(f"Home: {vitamins.util.at_home()}")

    def on_tick(self):
        self.clear_controls()
        if self.current_activity is not None:
            try:
                self.current_activity()
            except ActivityDone:
                print(f"Activity {self.current_activity} done.")
                self.current_activity = None
                self.clear_controls()
        self.play_soccar()
