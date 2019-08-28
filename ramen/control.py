"""ramen.control -- routines for controlling the car."""
from vitamins.agent import RamenBot
from vitamins import draw
from vitamins.math import *


def turn_toward(bot: RamenBot, target_loc):
    draw.cross(target_loc, color="purple")
    yaw_err = bot.car.yaw_to(target_loc)
    yaw_rate = bot.car.avel.z
    if yaw_err * yaw_rate < 0.1:
        # Turning in the right direction.
        bot.con.steer = copysign(1, -yaw_err)
        bot.con.handbrake = True
        if abs(yaw_err) < 0.4:
            bot.con.steer *= 0.4
            bot.con.handbrake = False
    else:
        # Turning in the wrong direction!
        bot.con.handbrake = False
        if abs(yaw_rate) > 0.1:
            bot.con.steer = copysign(1, -yaw_rate)
        else:
            bot.con.steer = 0
    # to_target = target_loc - bot.car.loc
    # dot = to_target.ndot(bot.car.right)
    # if dot > 0:
    #     bot.con.steer = 1
    # elif dot < 0:
    #     bot.con.steer = -1
    # if abs(dot) < 0.2:
    #     bot.con.steer *= 0.2
    #     bot.con.handbrake = False
    # if abs(dot) < 0.01:
    #     bot.con.steer = 0
    #     bot.con.handbrake = False
