"""
Stage 4 - Compare scenarios with pandas and repeated runs.

Changes from Stage 3:
  * Records go into a pandas DataFrame.
  * summarise() turns records into percentages a coordinator understands.
  * run_replications() repeats each scenario with different seeds and
    averages them - one random run can be misleading.
  * Several "what if" scenarios are compared side by side.

New concepts: pandas DataFrames, dataclasses.replace, functions as
building blocks, why repeated random runs matter.
"""

import random
import statistics
from dataclasses import dataclass, field, replace

import pandas as pd
import simpy

DIET_SHARES = {"general": 0.55, "vegetarian": 0.25, "halal": 0.20}


@dataclass
class Config:
    name: str = "Baseline"
    volunteers: int = 2
    open_minutes: int = 180
    mean_arrival_gap: float = 1.5
    mean_service_time: float = 2.5
    max_wait: float = 20.0
    stock: dict = field(default_factory=lambda: {"general": 70, "vegetarian": 25, "halal": 15})
    seed: int = 42


class Pantry:
    def __init__(self, env, cfg):
        self.env, self.cfg = env, cfg
        self.counter = simpy.Resource(env, capacity=cfg.volunteers)
        self.stock = {d: simpy.Container(env, init=n, capacity=max(n, 1))
                      for d, n in cfg.stock.items()}
        self.records = []

    def serve(self, diet):
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
    return pd.DataFrame(pantry.records)


def summarise(cfg, df):
    pct = lambda o: 100 * (df["outcome"] == o).mean()
    served = df[df["outcome"] != "gave_up"]
    return {"scenario": cfg.name, "students": len(df),
            "suitable_%": pct("suitable"), "unsuitable_%": pct("unsuitable"),
            "no_food_%": pct("no_food"), "gave_up_%": pct("gave_up"),
            "avg_wait_min": statistics.mean(served["wait"]) if len(served) else 0}


def run_replications(cfg, reps=20):
    rows = [summarise(cfg, run(replace(cfg, seed=cfg.seed + i))) for i in range(reps)]
    return {"scenario": cfg.name,
            **pd.DataFrame(rows).drop(columns="scenario").mean().round(1).to_dict()}


if __name__ == "__main__":
    base = Config()
    matched = {"general": 60, "vegetarian": 28, "halal": 22}
    scenarios = [base,
                 replace(base, name="+1 volunteer", volunteers=3),
                 replace(base, name="Culturally matched stock", stock=matched)]
    print(pd.DataFrame([run_replications(s) for s in scenarios]).to_string(index=False))
