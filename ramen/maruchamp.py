"""maruchamp.py -- MaruChamp Rocket League bot by Ramen and Vitamins"""
from math import copysign

from vitamins.agent import RamenBot
from vitamins.activity import ActivityDone
from vitamins.game import *
from vitamins.math import *
import vitamins.util

from ramen.veggies import kickoff, misc
from ramen import control


COMP_MODE = True  # True for competition mode
print = vitamins.util.comp_print if COMP_MODE else vitamins.util.dev_print


class MaruChamp(RamenBot):
    comp_mode = COMP_MODE

    def is_hot_reload_enabled(self):
        return True

    def on_start(self):
        self.state = "soccar"
        self.prev_state = None
        self.current_activity = None
        self.level_out_rolldir = None

    def do(self, act: type, *args, **kwargs):
        previous_activity = self.current_activity
        if previous_activity is not None and not previous_activity.done:
            print(f"Cancelling activity {previous_activity}")
        self.current_activity = act(self, *args, **kwargs)
        print(f"Beginning activity {self.current_activity}")

    def level_out(self):
        car = self.car
        field = self.field
        if car.loc.z > 100 and not car.wheel_contact:
            if car.up.dot(field.up) > 0.95:
                # Don't worry about it.
                self.con.roll = 0
                self.con.pitch = 0
                self.level_out_rolldir = None
                return
            rdot = car.right.dot(field.up)
            pdot = car.fwd.dot(field.down)
            if self.level_out_rolldir is None:
                self.level_out_rolldir = copysign(1, rdot)
                if self.level_out_rolldir == 0:
                    # break symmetry
                    self.level_out_rolldir = 1
            else:
                self.con.roll = self.level_out_rolldir
                self.con.pitch = 0
                if car.up.dot(field.up) > 0 and abs(rdot) < 0.2:
                    self.level_out_rolldir = 0
                    if abs(pdot) > 0.2:
                        self.con.pitch = copysign(1, pdot)
                    else:
                        self.con.yaw = self.con.steer
        else:
            self.level_out_rolldir = None

    def driving_on_wall(self):
        return self.car.loc.z > 100 and self.car.wheel_contact

    def attack_pos(self, dist=500):
        field, ball, car = self.field, self.ball, self.car
        if ball.vel.dot(field.fwd) > 0:
            if ball.vel.cross(ball.to(field.opp_goal_center)).dot(field.up) < 0:
                target = self.field.opp_right_post
            else:
                target = self.field.opp_left_post
        else:
            if self.ball.loc.dot(self.field.right) > 0:
                target = self.field.opp_right_post
            else:
                target = self.field.opp_left_post
        draw.cross(target.loc, color="lime")
        dt = self.car.time_to(self.ball)
        fball = ball.future(dt) or ball
        return (fball.loc + target.to(self.ball).rescale(dist)).flat()

    def defend_pos(self):
        dt = self.car.time_to(self.ball)
        loc = self.field.own_goal_center.midpoint(self.ball).flat()
        d = self.ball.dist(loc)
        if d > 3000:
            loc = self.ball.loc + self.ball.to(self.field.own_goal_center).rescale(3000)
        return loc.flat()

    def hang_back_pos(self):
        return self.field.center.midpoint(self.ball)

    def strike_pos(self):
        if self.car.to(self.ball).dot(self.field.fwd) < 0:
            return self.defend_pos()
        t = clamp(self.ball.dist(self.field.own_goal_center) / 2000, 0, 1)
        v = self.attack_pos() - self.defend_pos()
        pos = self.defend_pos() + t * v
        # if abs(self.ball.vel.z) < 100:
        #     d = clamp(self.car.dist(pos), 0, 1000)
        #     v = (self.ball.loc - pos).rescale(d)
        #     pos = self.ball.loc - v
        return pos

    def play_soccar(self):
        """Top level strategy routine."""
        if self.state != self.prev_state:
            print(f"State transition: {self.prev_state} -> {self.state}")
        ball, me, opp, field = self.ball, self.car, self.opponent_car, self.field

        rel_ball_dist = opp.dist(ball) - me.dist(ball)
        time_adv = opp.time_to(ball) - me.time_to(ball)

        self.renderer.draw_string_2d(
            20, 40, 1, 3, f"   State: {self.state}", self.renderer.white()
        )
        self.renderer.draw_string_2d(
            20, 60, 1, 3, f"Activity: {self.current_activity}", self.renderer.white()
        )
        if rel_ball_dist > 0:
            col = self.renderer.lime()
        else:
            col = self.renderer.red()
        self.renderer.draw_string_2d(
            20, 220, 1, 3, f"Distance-to-ball advantage: {rel_ball_dist:.0f}", col
        )
        if time_adv > 0:
            col = self.renderer.lime()
        else:
            col = self.renderer.red()
        self.renderer.draw_string_2d(
            20, 240, 1, 3, f"Time-to-ball advantage: {time_adv:.1f}", col
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

        draw.cross(self.defend_pos(), color="blue")
        draw.cross(self.attack_pos(), color="red")
        draw.cross(self.strike_pos(), color="yellow")

        # INTERRUPTS - can knock us out of a state/activity that's not done yet:

        # Interrupt: Kickoff
        if self.packet.game_info.is_kickoff_pause and "kickoff" not in self.state:
            self.state = "kickoff start"
            self.clear_controls()
            return

        # Interrupt: Follow through
        if False and (
            abs(me.yaw_to(ball)) < 0.4
            and me.to(ball).ndot(ball.to(field.opp_goal_center)) > 0.8
        ):
            if me.dist(ball) < 500 and ball.is_rolling():
                control.turn_toward(ball)
                self.con.throttle = 1
                self.con.boost = 1
                return

        # STATE TRANSITIONS

        if self.state == "kickoff start":
            self.do(kickoff.JumpKickoff)
            self.state = "kickoff execute"

        elif self.state == "hang back":
            self.do(misc.Follow, self.hang_back_pos, use_boost=False)
            self.state = "hanging back"

        elif self.state == "hanging back":
            if ball.future(1).dist_to_corner() > 1500:
                self.state = "soccar"

        elif self.state == "strike position":
            if me.dist(self.strike_pos()) < me.dist(ball):
                self.state = "strike ball"
            if time_adv < -3:
                self.state = "start defending"
            if ball.future(2).dist_to_corner() < 1500:
                if ball.loc.dot(field.fwd) > 1:
                    self.state = "hang back"

        elif self.state == "start defending":
            self.do(misc.Follow, self.defend_pos)
            self.state = "defend position"

        elif self.state == "defend position":
            if time_adv > 2:
                self.state = "strike ball"

        elif self.state == "strike ball":
            self.do(misc.BallChase)
            self.count = 0
            self.state = "striking ball"

        elif self.state == "striking ball":
            if me.spd_to(ball) < 0:
                self.count += 1
                if self.count > 120:
                    self.state = "soccar"
            else:
                self.count = 0

        elif self.state == "kickoff execute":
            if self.current_activity is None:
                self.state = "soccar"

        elif self.state == "soccar":
            # Choose an action based on circumstances:
            self.state = "strike position"
            self.do(misc.Follow, self.strike_pos)

        elif self.state == "front flip":
            self.t0 = self.game_time
            self.flip_prev_activity, self.current_activity = self.current_activity, None
            self.flip_prev_state = self.prev_state
            self.state = "front flipping"

        elif self.state == "front flipping":
            dt = self.game_time - self.t0
            dt *= 2
            if dt < 0.2:
                self.con.jump = True
                self.con.pitch = -1
            elif dt < 0.3:
                self.clear_controls()
                self.con.pitch = -1
            elif dt < 0.4:
                self.con.jump = True
                self.con.pitch = -1
            else:
                self.con.pitch = 0
                self.con.jump = False
                self.state = self.flip_prev_state
                self.current_activity = self.flip_prev_activity

        elif self.state == "forever":
            pass

        else:
            print(f"Undefined state [{self.state}]")

        self.prev_state = self.state

    def on_first_tick(self):
        self.current_activity = None

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
        # Special cases:
        # todo: incorporate these properly

        if "kickoff" not in self.state and "flip" not in self.state:
            # If we're in the air, put the wheels down and steer with yaw:
            self.level_out()

            # Hop off the wall:
            if self.driving_on_wall() and self.car.vel.z < 100:
                self.con.jump = self.tick % 30 < 15

            # don't fly:
            if not self.car.wheel_contact and self.car.fwd.dot(self.field.up) > 0:
                self.con.boost = False
