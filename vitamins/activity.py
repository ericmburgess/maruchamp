"""activityx.py -- Class to encapsulate activities or intentions."""

from vitamins.agent import RamenBot


class Activity:
    step = 0

    def __init__(self, bot: RamenBot):
        self.bot = bot
        self.start_ticks = self.bot.tick
        self.start_time = self.bot.game_time
        self.done = False
        self.result = None
        self.countdown = 0
        self.next_step(0)
        self.status = ""

    def __str__(self):
        name = type(self).__name__
        if self.status:
            return f"{name}:{self.step} [{self.status}]"
        else:
            return f"{name}:{self.step}"

    def __call__(self):
        if self.done:
            raise ActivityDone()
        if self.countdown:
            self.countdown -= 1
        else:
            self.stepfunc()

    def next_step(self, step_num=None, sleep=0):
        self.step = self.step + 1 if step_num is None else step_num
        self.countdown = max(self.countdown, sleep)
        try:
            funcname = f"step_{self.step}"
            self.stepfunc = getattr(self, funcname)
            self.step_start_tick = self.bot.tick
            self.step_start_time = self.bot.game_time
        except AttributeError:
            self.done = True
            raise UndefinedStepError(f"{funcname} is not defined.")

    def sleep(self, ticks):
        self.countdown = max(self.countdown, ticks)

    def ticks(self):
        """Return the number of ticks since the activityx started."""
        return self.bot.tick - self.start_ticks

    def game_time(self):
        """Return the number of in-game seconds since the activityx started."""
        return self.bot.game_time - self.start_time

    def step_ticks(self):
        """Return the number of ticks since the current step started."""
        return self.bot.tick - self.step_start_tick

    def step_seconds(self):
        """Return the number of game seconds since the current step started."""
        return self.bot.game_time - self.step_start_time

    def step_0(self):
        pass

    def step_1(self):
        pass

    def step_2(self):
        pass

    def step_3(self):
        pass

    def step_4(self):
        pass

    def step_5(self):
        pass

    def step_6(self):
        pass

    def step_7(self):
        pass

    def step_8(self):
        pass

    def step_9(self):
        pass

    def step_10(self):
        pass


class UndefinedStepError(Exception):
    pass


class ActivityDone(Exception):
    pass
