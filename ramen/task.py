"""A `Task` encapsulates a high-level, possibly complex activity. A good synonym would
be "intention". Some examples of tasks might be:

* Grab the nearest full boost pickup
* Make an aerial hit on a flying ball
* Demo the opponent
* Remain in goal as long as the ball is against the back wall
* Stay on the opposite side of the ball to block the opponent's shot
* Get the ball on top of the car for a dribble
* Drive to a particular place on the field

That last one was also in the example list for `Action`! The distinction isn't sharply
defined, and there will be plenty of things that could make sense either as a task or an
action.

The key distinction between task and action is that every task has two parts: a `score`
method, and a `run` method. The `score` method returns a number that represents how good
the current situation is for doing that task, and the agent chooses, from moment to
moment, which task to run based on all their scores (and some other considerations; see
the `Agent` documentation for all the details). Tasks are *ongoing*--they're expected to
keep running for as long as the agent has chosen to keep it as the current task. But the
task does have a lot of influence over this, as the `score` function is evaluated
continuously, whether the task is currently running or not. If the task no longer has
the conditions it needs to effectively accomplish its intent, it should report a low
`score`. This will motivate the Agent to choose another task to take over.

Actions, on the other hand, just run when they're told to, and typically (though not
always) have a self-defined end state. For example, a half-flip action will do a
backward dodge, cancel it, and roll to put the wheels down. Then it's done, mission
accomplished.

# Scoring

At the risk of stating the obvious, having good `score` functions for your Tasks is
crucial. Here are some important things to keep in mind when writing a score function:

* One score by itself is meaningless--it's only when compared against the scores from
all the other tasks that a "best task" is chosen. So it's important to keep all your
scores on the same scale. Whether it's 0 to 1, -100 to 100, or anything else, you must
be consistent. A task with a 1 to 100 scale will always overwhelm a task that scores
itself from 0 to 1!
* The score function should be *single-minded*, that is, it's only for this task. It
does not care about whether it's a *good idea* to be doing this task right now--that's
the agent's job. The task score should reach the maximum value when the task can be
accomplished with full confidence and very little effort, and it should reach the
minimum value when the task cannot possibly be accomplished in the current situation.
* The score should depend smoothly on the game state. (todo: say more)
* A constant score can be used for a "default" task that will be executed when no other
task is appropriate. It's best to use the maximum possible value, and let the agent
adjust the weight as appropriate. Any task that is going to be a "default" should be one
that can always be done, so the maximum score makes sense here.
"""

from ramen.action import Action


class Task:
    weight: float = 1
    name: str = ""
    status: str = ""
    action: Action = None

    def score(self) -> float:
        """Return a float representing how easily and with what certainty this task can
        be carried out. Should not incorporate whether this task is the right choice at
        the moment (the Agent influences that via task weights).
        """
        return 1

    def __call__(self):
        if self.action is not None:
            if self.action.done:
                self.action = None
            else:
                self.action.run()
                self.monitor_action(self.action)
        if self.action is None:
            self.run()

    def busy(self) -> bool:
        """Return True if this task should not be interrupted."""
        return self.action is not None and self.action.busy()

    def enter(self):
        """Called once when the agent switches from another task to this one."""
        pass

    def run(self):
        pass

    def leave(self):
        """Called once when the agent switches away from this task."""
        pass

    def do_action(self, action: Action):
        """Start executing an action. Until the action completes, this task's
        `monitor_action` method will be called each tick, instead of the `run` method.
        (So normal task execution is paused, but the task can still keep an eye on
        things and cancel the action if need be.)
        """
        self.action = action

    def monitor_action(self, action: Action):
        """Called each tick instead of `run`, if the task is currently running an
        action."""
        pass

    def cancel_action(self):
        """Cancels the current action, and any sub-actions, if any. Note: setting the
        `interruptible` attribute of actions to `False` only prevents them from being
        interrupted by the agent choosing another task. This method will cancel an
        action whether or not it wants to be canceled!
        """
        self.action = None

    def __str__(self):
        s_status = f"[{self.status}]" if self.status else ""
        s_action = f"<{self.action}>" if self.action else ""
        return f"{self.name or self.__class__.__name__} {s_status} {s_action}"
