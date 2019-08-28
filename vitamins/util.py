"""vitamins.util -- utility routines."""
from time import perf_counter
from platform import node
from hashlib import md5


def at_home():
    """Return True in my home dev environment, False everywhere else."""
    return md5(node().encode("utf-8")).hexdigest() in [
        "98718bd98a3e2a41f760bc8f28810190"
    ]


def dev_print(*args, **kwargs):
    print(*args, **kwargs)


def comp_print(*args, **kwargs):
    pass


def perf_counter_ns_for_36():
    return int(perf_counter() * 1e9)


try:
    from time import perf_counter_ns
except ImportError:
    perf_counter_ns = perf_counter_ns_for_36


class TickStats:
    def __init__(self, name: str, unit: str = "", interval=100, startup=0):
        self.name = name
        self.unit = unit
        self.interval = interval
        self.total_interval = 0
        self.total_all = 0
        self.tick = 0
        self.startup = startup  # number of initial samples to ignore

    def update(self, tick_ms):
        if self.startup > 0:
            self.startup -= 1
            return
        self.total_interval += tick_ms
        self.total_all += tick_ms
        self.tick += 1
        if self.tick % self.interval == 0:
            out = f"Avg {self.name}: {self.total_all/self.tick:.2f}{self.unit}, "
            out += f"last {self.interval}: "
            out += f"{self.total_interval/self.interval:.2f}{self.unit}"
            print(out)
            self.total_interval = 0
