"""
Stage 3 - Food stock and culturally appropriate food.

Changes from Stage 2:
  * Each student has a dietary need (general / vegetarian / halal).
  * Stock is held in one simpy.Container per diet group.
  * Outcomes are now: suitable, unsuitable (got general food instead),
    no_food (all stock gone), gave_up.

Why: research on international students in Australia (Leung et al., 2025)
found a lack of culturally appropriate food is a key barrier. This stage
makes that visible in the model. Diet shares are ASSUMPTIONS.

New concepts: simpy.Container, dictionaries, random.choices with weights,
sub-processes that return a value.
"""

import random
from collections import Counter
from dataclasses import dataclass, field

import simpy

DIET_SHARES = {"general": 0.55, "vegetarian": 0.25, "halal": 0.20}


@dataclass
class Config:
    volunteers: int = 2
    open_minutes: int = 180
    mean_arrival_gap: float = 1.5
    mean_service_time: float = 2.5
    max_wait: float = 20.0
    stock: dict = field(default_factory=lambda: {"general": 70, "vegetarian": 25, "halal": 15})
    seed: int = 42


class Pantry:
    def __init__(self, env, cfg):
        self.env = env
        self.cfg = cfg
        self.counter = simpy.Resource(env, capacity=cfg.volunteers)
        self.stock = {d: simpy.Container(env, init=n, capacity=max(n, 1))
                      for d, n in cfg.stock.items()}
        self.records = []

    def serve(self, diet):
        """Pack a parcel and report whether it met the student's need."""
        yield self.env.timeout(random.expovariate(1 / self.cfg.mean_service_time))
        if self.stock[diet].level > 0:
            yield self.stock[diet].get(1)
            return "suitable"
        if diet != "general" and self.stock["general"].level > 0:
            yield self.stock["general"].get(1)
            return "unsuitable"
        return "no_food"


def student(env, sid, pantry):
    arrived = env.now
    diet = random.choices(list(DIET_SHARES), weights=DIET_SHARES.values())[0]
    with pantry.counter.request() as req:
        result = yield req | env.timeout(pantry.cfg.max_wait)
        waited = env.now - arrived
        outcome = (yield env.process(pantry.serve(diet))) if req in result else "gave_up"
    pantry.records.append({"student": sid, "diet": diet, "wait": waited, "outcome": outcome})


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
    recs = run(Config())
    print("Overall:", dict(Counter(r["outcome"] for r in recs)))
    for diet in DIET_SHARES:
        print(f"  {diet:<11}", dict(Counter(r["outcome"] for r in recs if r["diet"] == diet)))
