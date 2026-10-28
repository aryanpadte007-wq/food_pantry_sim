"""
Stage 2 - Settings in one place + basic statistics.

Changes from Stage 1:
  * A Config dataclass holds every setting, so scenarios are easy to change.
  * A Pantry class keeps the counter and a list of records.
  * Students give up if they wait longer than max_wait.
  * We report average wait and % who gave up instead of printing every event.

New concepts: dataclasses, classes, lists of dicts, the `|` (either-or) event.
"""

import random
import statistics
from dataclasses import dataclass

import simpy


@dataclass
class Config:
    """Settings for one run (minutes)."""
    volunteers: int = 1
    open_minutes: int = 180
    mean_arrival_gap: float = 1.5
    mean_service_time: float = 2.5
    max_wait: float = 20.0
    seed: int = 42


class Pantry:
    """Counter (volunteers) plus a list of what happened to each student."""

    def __init__(self, env, cfg):
        self.env = env
        self.cfg = cfg
        self.counter = simpy.Resource(env, capacity=cfg.volunteers)
        self.records = []


def student(env, sid, pantry):
    arrived = env.now
    with pantry.counter.request() as req:
        result = yield req | env.timeout(pantry.cfg.max_wait)
        waited = env.now - arrived
        if req in result:
            yield env.timeout(random.expovariate(1 / pantry.cfg.mean_service_time))
            outcome = "served"
        else:
            outcome = "gave_up"
    pantry.records.append({"student": sid, "wait": waited, "outcome": outcome})


def arrivals(env, pantry):
    sid = 0
    while env.now < pantry.cfg.open_minutes:
        yield env.timeout(random.expovariate(1 / pantry.cfg.mean_arrival_gap))
        sid += 1
        env.process(student(env, sid, pantry))


def run(cfg):
    random.seed(cfg.seed)
    env = simpy.Environment()
    pantry = Pantry(env, cfg)
    env.process(arrivals(env, pantry))
    env.run(until=cfg.open_minutes + cfg.max_wait + 30)
    return pantry.records


if __name__ == "__main__":
    for v in (1, 2, 3):
        recs = run(Config(volunteers=v))
        gave_up = sum(r["outcome"] == "gave_up" for r in recs)
        avg_wait = statistics.mean(r["wait"] for r in recs)
        print(f"{v} volunteer(s): {len(recs)} students, "
              f"avg wait {avg_wait:.1f} min, gave up {100*gave_up/len(recs):.1f}%")
