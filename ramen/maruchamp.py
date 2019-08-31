"""maruchamp.py -- MaruChamp Rocket League bot by Ramen and Vitamins"""
from vitamins.agent import RamenBot
from vitamins.activity import ActivityDone
from vitamins.game import *
from vitamins.math import *
import vitamins.util

from ramen.veggies import kickoff, misc
from ramen import control, activities


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
        self.last_kickoff = 0

    def do(self, act: type, *args, **kwargs):
        previous_activity = self.current_activity
        self.current_activity = act(self, *args, **kwargs)
        if previous_activity is not None and not previous_activity.done:
            print(f"Cancelling activity {previous_activity}", end="")
            print(f" in favor of {self.current_activity}")
        else:
            print(f"Starting activity {self.current_activity}")

    def driving_on_wall(self):
        return self.car.z > 100 and self.car.wheel_contact

    def wrap(self):
        """Wrap at map edges to opposite side. Avoids wall interaction."""
        width = 6000
        height = 8000
        wrap = False
        loc = self.car.loc
        if loc.x > width / 2 and self.car.vel.x > 0:
            loc.x -= width
            wrap = True
        if loc.x < -width / 2 and self.car.vel.x < 0:
            loc.x += width
            wrap = True
        if loc.y > height / 2 and self.car.vel.y > 0:
            loc.y -= height
            wrap = True
        if loc.y < -height / 2 and self.car.vel.y < 0:
            loc.y += height
            wrap = True
        if wrap:
            self.car.reset(self)

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
            self.clear_controls()
            self.do(kickoff.FlipIntoBallKickoff)
            self.state = "kickoff execute"

        elif self.state == "kickoff execute":
            if self.current_activity is None:
                self.last_kickoff = self.game_time
                self.state = "soccar"

        elif self.state == "soccar":
            # Choose an action based on circumstances:
            nb = ball.next_bounce(self.game_time)
            if (
                ball.vel.length() > 0
                and ball.vel.ndot(field.back) > 0.2
                and me.to(ball).dot(field.back) > 200
                and me.dot(field.back) < 4000
            ):
                self.state = "go to post"
                if ball.dot(field.left) > 0:
                    dir = 1
                else:
                    dir = -1
                self.do(activities.DefendAtPost, dir)
            elif (
                nb is not None
                and me.to(nb).dot(field.fwd) > 0.5
                and nb.time - self.game_time > 3
                and nb.dot(field.fwd) < 2000
            ):
                self.state = "hit bounce"
                self.do(activities.BounceHit)
            else:
                self.chase()

        elif self.state == "go to post":
            if self.current_activity is None:
                self.clear_controls()
                if me.vel.dot(me.fwd) > 0:
                    self.con.throttle = -1
                else:
                    self.clear_controls()
                    self.state = "defend post"

        elif self.state == "defend post":
            self.state = "soccar"

        elif self.state == "hit bounce":
            if self.current_activity is None:
                self.state = "soccar"

        else:
            print(f"Undefined state [{self.state}]")

        self.prev_state = self.state

    def on_first_tick(self):
        self.current_activity = None
        self.chase = activities.BallChase(self)
        print(f"Home: {vitamins.util.at_home()}")

    def on_tick(self):
        if self.current_activity is not None:
            try:
                self.current_activity()
            except ActivityDone:
                print(f"Activity {self.current_activity} done.")
                self.current_activity = None
                self.clear_controls()
        self.play_soccar()
        if not "kickoff" in self.state:
            if self.driving_on_wall():
                self.clear_controls()
                self.con.steer = self.car.right.dot(self.field.down)
                self.con.throttle = 1
