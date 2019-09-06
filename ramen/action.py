"""An `Action` is a small, self-contained unit of activity, such as:

    * A kickoff
    * A front (or other) flip
    * Pointing the wheels down while in midair

It also may be an ongoing activity, such as:

    * Chasing the ball
    * Driving to a particular place on the field

The major distinction between an `Action` and a `Task` is that actions do not have
score functions. Therefore the agent never executes them directly--they are run only
when invoked by a task (or another action).

By default, actions are not interruptible. Until the action completes, the agent will
not be able to switch off of the Task that started it. This is what we want for e.g. a
half-flip, because stopping that in the middle will leave our car upside-down and/or
pointed the wrong way. However, it doesn't (probably) make sense for a "ball chase"
action. Any action that *should* be interrupted when the agent wants to switch away
from it should have its `interruptible` attribute set to `True`.
"""


from vitamins.match.match import Match


class Action:
    current_step = 0
    interruptible: bool = False
    done = False
    countdown: int = 0
    tick: 0
    wake_time: float = 0
    sub_action: "Action" = None
    done_after_sub_action = False
    first_step = None

    def __init__(self):
        self.stepfunc = self.step_0
        self.status = ""
        if self.first_step is not None:
            self.step(self.first_step)

    def __str__(self):
        name = type(self).__name__
        sub = f" -> {self.sub_action}" if self.sub_action else ""
        if self.done:
            return f"{name}: DONE"
        elif self.status:
            return f"{name}:{self.current_step} [{self.status}] {sub}"
        else:
            return f"{name}:{self.current_step} {sub}"

    def run(self):
        """Run the current step."""
        if not self.done:
            if self.sub_action is not None:
                self.before()
                self.sub_action.run()
                self.after()
                if self.sub_action.done:
                    self.sub_action = None
                    self.done = self.done or self.done_after_sub_action
            elif Match.time < self.wake_time:
                self.when_paused()
            elif self.countdown:
                self.when_paused()
                self.countdown -= 1
            else:
                self.before()
                self.stepfunc()
                self.after()
            # If we were marked done, run the when_done event:
            if self.done:
                self.when_done()

    def step(self, step_name, ticks: int = 0, ms: int = 0):
        """Moves execution to the given step. Calling this does not end execution of the
        current step (if there are more statements below the call to `step`, they will
        be executed), and execution of the next step does not happen until the next game
        tick. In the language of state machines, this is how state transitions are made.

        If `ticks` is specified and positive, then execution is suspended for that many
        ticks before picking up at the new step. o

        If `ms` is specified and positive, then execution is suspended until that many
        in-game milliseconds have elapsed. If `ms` is less than the duration of a single
        frame (16.67ms at 60fps, 8.33ms at 120fps), there will be no pause in execution.

        During ticks in which normal execution is suspended, the `when_paused` method is
        called instead of the current step method.
        """
        self.current_step = step_name
        self.sleep(max(ticks, 0), max(ms, 0))
        self.stepfunc = getattr(self, f"step_{step_name}", None)
        if self.stepfunc is None:
            self.done = True
            raise UndefinedStepError(f"{step_name} is not defined.")

    def busy(self):
        """Return True if this action should not be interrupted. Even if this action
        is marked as interruptible, it may have a sub-action (or sub-sub-...-action)
        which is not interruptible. This method will return True if any action in the
        chain is not interruptible.
        """
        return (not self.interruptible and not self.done) or (
            self.sub_action is not None and self.sub_action.busy()
        )

    def do_action(self, sub_action: "Action", step=None, done=False):
        """Start doing another action. Execution will pick up where it left off once
        the new action is complete. The `before` and `after` methods will continue to
        run for this action while the sub-action is in progress.

        If `step` is given, execution of this action will resume at that step after
        the sub-action is done.

        If `done` is True, this action will be done as soon as the sub-action finishes.
        """
        if self.sub_action is None:
            self.sub_action = sub_action
            self.done_after_sub_action = done
            if step is not None:
                self.step(step)
        else:
            raise ActivityError("Can't start a sub-action, one is alredy in progress.")

    def sleep(self, ticks=0, ms=0):
        """Pause execution for a specified number of ticks or milliseconds. The
        `when_paused` method will be called each tick in place of normal execution.
        """
        self.countdown = max(self.countdown, ticks)
        if ms > 0:
            self.countdown = 0
            self.wake_time = Match.time + ms / 1e3

    def wake(self):
        """Cancel any pause in progress."""
        self.countdown = 0
        self.wake_time = 0.0

    def before(self):
        """This will be called every tick before the current step (or sub-action) is
        executed."""

    def after(self):
        """This will be called every tick after the current step (or sub-action) is
        executed."""

    def when_paused(self):
        """This will be called instead of the current step when `self.step` has been
        invoked with a wait which hasn't finished yet."""

    def when_done(self):
        """Called only once, at the end of the tick in which `self.done` is set to True.
        """

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


class ActivityError(Exception):
    pass
