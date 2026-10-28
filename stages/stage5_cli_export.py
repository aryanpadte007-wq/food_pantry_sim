"""
Stage 5 - Command-line options, CSV + chart export.

A small SimPy model of a student-run campus food bank, modelled on the
Swinburne Student Union (SSU) FoodBank, a free walk-in service open
10am-1pm on weekdays (180 minutes, as used below).

Why this matters:
    Australian research reports food insecurity among university students,
    and a 2025 study of international students (Leung et al., Health
    Promotion Journal of Australia) found a lack of culturally appropriate
    food and inefficient pantry operations were key barriers. This program
    lets a food bank coordinator test simple choices - volunteers, stock and
    culturally suitable stock - and see how many students get a parcel
    that meets their needs.

What it is NOT:
    A real forecasting tool. All numbers below are illustrative assumptions
    and should be replaced with real pantry data before drawing conclusions.

Run:
    python pantry_sim.py                 # compare built-in scenarios
    python pantry_sim.py --volunteers 3  # run one custom scenario
"""

import argparse
import random
import statistics
from dataclasses import dataclass, replace

import pandas as pd
import simpy

# Dietary groups a student may need. Shares are ASSUMPTIONS for illustration.
DIET_SHARES = {"general": 0.55, "vegetarian": 0.25, "halal": 0.20}


@dataclass
class Config:
    """All settings for one simulation run (times are in minutes)."""

    name: str = "Baseline"
    volunteers: int = 2            # people serving at the counter
    open_minutes: int = 180        # pantry open for 3 hours
    mean_arrival_gap: float = 1.5  # average minutes between student arrivals
    mean_service_time: float = 2.5  # average minutes to pack one parcel
    max_wait: float = 20.0         # students give up after waiting this long
    stock: dict = None             # starting parcels per diet group
    seed: int = 42

    def __post_init__(self):
        if self.stock is None:
            self.stock = {"general": 70, "vegetarian": 25, "halal": 15}


class Pantry:
    """The pantry: a counter (volunteers) plus food stock per diet group."""

    def __init__(self, env, cfg):
        self.env = env
        self.cfg = cfg
        self.counter = simpy.Resource(env, capacity=cfg.volunteers)
        # One SimPy Container per diet group, so each can run out separately.
        self.stock = {
            diet: simpy.Container(env, init=amount, capacity=max(amount, 1))
            for diet, amount in cfg.stock.items()
        }
        self.records = []  # one dict per student, filled during the run

    def serve(self, diet):
        """Pack a parcel. Returns the outcome as a short string."""
        yield self.env.timeout(random.expovariate(1 / self.cfg.mean_service_time))
        if self.stock[diet].level > 0:
            yield self.stock[diet].get(1)
            return "suitable"
        if diet != "general" and self.stock["general"].level > 0:
            # Something was given, but it may not meet their dietary need.
            yield self.stock["general"].get(1)
            return "unsuitable"
        return "no_food"


def pick_diet():
    """Randomly choose a diet group using DIET_SHARES."""
    return random.choices(list(DIET_SHARES), weights=DIET_SHARES.values())[0]


def student(env, sid, pantry):
    """One student: arrive, queue (or give up), get a parcel, leave."""
    arrived = env.now
    diet = pick_diet()
    with pantry.counter.request() as req:
        # Wait for a volunteer OR run out of patience - whichever comes first.
        result = yield req | env.timeout(pantry.cfg.max_wait)
        waited = env.now - arrived
        if req not in result:
            outcome = "gave_up"
        else:
            outcome = yield env.process(pantry.serve(diet))
    pantry.records.append(
        {"student": sid, "diet": diet, "wait": round(waited, 2), "outcome": outcome}
    )


def arrivals(env, pantry):
    """Generate students until closing time."""
    sid = 0
    while env.now < pantry.cfg.open_minutes:
        yield env.timeout(random.expovariate(1 / pantry.cfg.mean_arrival_gap))
        sid += 1
        env.process(student(env, sid, pantry))


def run(cfg):
    """Run one scenario and return a DataFrame of student records."""
    random.seed(cfg.seed)
    env = simpy.Environment()
    pantry = Pantry(env, cfg)
    env.process(arrivals(env, pantry))
    # Let students already in the queue finish after the doors close.
    env.run(until=cfg.open_minutes + cfg.max_wait + 30)
    return pd.DataFrame(pantry.records)


def summarise(cfg, df):
    """Turn raw records into the key numbers a coordinator cares about."""
    total = len(df)
    share = lambda o: round(100 * (df["outcome"] == o).sum() / total, 1) if total else 0.0
    served = df[df["outcome"] != "gave_up"]
    return {
        "scenario": cfg.name,
        "volunteers": cfg.volunteers,
        "students": total,
        "suitable_%": share("suitable"),
        "unsuitable_%": share("unsuitable"),
        "no_food_%": share("no_food"),
        "gave_up_%": share("gave_up"),
        "avg_wait_min": round(statistics.mean(served["wait"]), 1) if len(served) else 0.0,
    }


def run_replications(cfg, reps=20):
    """Repeat a scenario with different seeds and average the results.

    One random run can be lucky or unlucky; averaging gives a fairer view.
    """
    rows = [summarise(cfg, run(replace(cfg, seed=cfg.seed + i))) for i in range(reps)]
    avg = pd.DataFrame(rows).drop(columns="scenario").mean().round(1).to_dict()
    return {"scenario": cfg.name, **avg}


def default_scenarios():
    """A few 'what if' settings a pantry coordinator might test."""
    base = Config()
    return [
        base,
        replace(base, name="+1 volunteer", volunteers=3),
        replace(base, name="Same stock, culturally matched",
                stock={"general": 60, "vegetarian": 28, "halal": 22}),
        replace(base, name="+1 volunteer & matched stock", volunteers=3,
                stock={"general": 60, "vegetarian": 28, "halal": 22}),
    ]


def plot(results, path="results.png"):
    """Save a stacked bar chart of outcomes per scenario."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cols = ["suitable_%", "unsuitable_%", "no_food_%", "gave_up_%"]
    ax = results.set_index("scenario")[cols].plot(
        kind="barh", stacked=True, figsize=(9, 4),
        color=["#2a9d8f", "#e9c46a", "#e76f51", "#8d99ae"])
    ax.set_xlabel("% of students")
    ax.set_title("Pantry outcomes by scenario (average of runs)")
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()
    return path


def parse_args(argv=None):
    """Read command-line options for a custom scenario."""
    p = argparse.ArgumentParser(description="Campus food pantry simulator")
    p.add_argument("--volunteers", type=int, help="run one custom scenario")
    p.add_argument("--minutes", type=int, default=180, help="opening time")
    p.add_argument("--reps", type=int, default=20, help="runs per scenario")
    p.add_argument("--csv", default="results.csv", help="where to save results")
    return p.parse_args(argv)


def main(argv=None):
    """Entry point: run scenarios, print a table, save CSV and chart."""
    args = parse_args(argv)
    if args.volunteers is not None:
        if args.volunteers < 1:
            raise SystemExit("Need at least 1 volunteer.")
        scenarios = [Config(name="Custom", volunteers=args.volunteers,
                            open_minutes=args.minutes)]
    else:
        scenarios = [replace(s, open_minutes=args.minutes) for s in default_scenarios()]

    results = pd.DataFrame([run_replications(s, args.reps) for s in scenarios])
    print(results.to_string(index=False))
    results.to_csv(args.csv, index=False)
    print(f"\nSaved {args.csv} and {plot(results)}")
    print("Note: inputs are illustrative assumptions, not real pantry data.")
    return results


if __name__ == "__main__":
    main()
