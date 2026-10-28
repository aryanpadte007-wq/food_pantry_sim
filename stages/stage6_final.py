"""
Campus Food Pantry Simulator (final version - Stage 6).

A small SimPy model of a student-run campus food bank, modelled on the
Swinburne Student Union (SSU) FoodBank, a free walk-in service open
10am-1pm on weekdays (180 minutes, as used below).

Why this matters:
    Food insecurity among Australian university students rose from 42% to
    53% between 2022 and 2024, with international students at higher risk
    (Kent et al., 2025). A study of international students (Leung et al.,
    2025) found a lack of culturally appropriate food and inefficient
    pantry operations were key barriers. This program
    lets a food bank coordinator test simple choices - volunteers, stock and
    culturally suitable stock - and see how many students get a parcel
    that meets their needs.

What it is NOT:
    A forecasting tool, or a voice for any community. Every number is an
    illustrative assumption to be replaced with real, consented data.

Run:
    python pantry_sim.py                          # built-in scenarios
    python pantry_sim.py --scenarios scenarios.csv
    python pantry_sim.py --volunteers 3 --verbose
"""

import argparse
import csv
import logging
import random
import statistics
import time
from dataclasses import dataclass, field, replace

import pandas as pd
import simpy

log = logging.getLogger("pantry")

# Dietary groups and the share of students needing each (ASSUMPTIONS).
DIET_SHARES = {"general": 0.55, "vegetarian": 0.25, "halal": 0.20}
OUTCOMES = ("suitable", "unsuitable", "no_food", "gave_up")


def default_stock():
    """Starting parcels per diet group (a fresh dict for every Config)."""
    return {"general": 70, "vegetarian": 25, "halal": 15}


@dataclass
class Config:
    """All settings for one simulation run (times are in minutes)."""

    name: str = "Baseline"
    volunteers: int = 2             # people serving at the counter
    open_minutes: int = 180         # SSU FoodBank 10am-1pm = 3 hours
    mean_arrival_gap: float = 1.5   # average minutes between arrivals
    mean_service_time: float = 2.5  # average minutes to pack one parcel
    max_wait: float = 20.0          # students give up after this long
    stock: dict = field(default_factory=default_stock)
    seed: int = 42

    def validate(self):
        """Raise ValueError if a setting makes no sense."""
        if self.volunteers < 1:
            raise ValueError(f"{self.name}: need at least 1 volunteer")
        if min(self.open_minutes, self.mean_arrival_gap,
               self.mean_service_time, self.max_wait) <= 0:
            raise ValueError(f"{self.name}: times must be positive")
        if set(self.stock) != set(DIET_SHARES):
            raise ValueError(f"{self.name}: stock needs {sorted(DIET_SHARES)}")
        if any(n < 0 for n in self.stock.values()):
            raise ValueError(f"{self.name}: stock cannot be negative")
        return self


class Pantry:
    """The pantry: a counter (volunteers) plus food stock per diet group."""

    def __init__(self, env, cfg):
        self.env = env
        self.cfg = cfg
        self.counter = simpy.Resource(env, capacity=cfg.volunteers)
        # One Container per diet group, so each can run out separately.
        self.stock = {
            diet: simpy.Container(env, init=amount, capacity=max(amount, 1))
            for diet, amount in cfg.stock.items()
        }
        self.records = []  # one dict per student

    def serve(self, diet):
        """Pack a parcel and return how well it met the student's need."""
        yield self.env.timeout(random.expovariate(1 / self.cfg.mean_service_time))
        if self.stock[diet].level > 0:
            yield self.stock[diet].get(1)
            return "suitable"
        if diet != "general" and self.stock["general"].level > 0:
            yield self.stock["general"].get(1)  # food, but not what they need
            return "unsuitable"
        return "no_food"


def pick_diet():
    """Randomly choose a diet group using DIET_SHARES as weights."""
    return random.choices(list(DIET_SHARES), weights=DIET_SHARES.values())[0]


def student(env, sid, pantry):
    """One student: arrive, queue (or give up), get a parcel, leave."""
    arrived = env.now
    diet = pick_diet()
    with pantry.counter.request() as req:
        # Wait for a volunteer OR run out of patience, whichever is first.
        result = yield req | env.timeout(pantry.cfg.max_wait)
        waited = env.now - arrived
        if req in result:
            outcome = yield env.process(pantry.serve(diet))
        else:
            outcome = "gave_up"
    log.debug("t=%6.1f student %3d %-10s %-10s waited %.1f",
              env.now, sid, diet, outcome, waited)
    pantry.records.append(
        {"student": sid, "diet": diet, "wait": round(waited, 2), "outcome": outcome})


def arrivals(env, pantry):
    """Generate students until closing time."""
    sid = 0
    while True:
        yield env.timeout(random.expovariate(1 / pantry.cfg.mean_arrival_gap))
        if env.now >= pantry.cfg.open_minutes:
            break  # doors closed - this student arrived too late
        sid += 1
        env.process(student(env, sid, pantry))


def run(cfg):
    """Run one scenario and return a DataFrame of student records."""
    random.seed(cfg.seed)
    env = simpy.Environment()
    pantry = Pantry(env, cfg)
    env.process(arrivals(env, pantry))
    env.run(until=cfg.open_minutes + cfg.max_wait + 30)  # let the queue clear
    return pd.DataFrame(pantry.records, columns=["student", "diet", "wait", "outcome"])


def summarise(df):
    """Turn raw records into the percentages a coordinator cares about."""
    total = len(df)
    row = {"students": total}
    for outcome in OUTCOMES:
        row[f"{outcome}_%"] = 100 * (df["outcome"] == outcome).sum() / total if total else 0.0
    served = df[df["outcome"] != "gave_up"]
    row["avg_wait_min"] = served["wait"].mean() if len(served) else 0.0
    return row


def run_replications(cfg, reps=20):
    """Repeat a scenario with different seeds; return mean and 95% CI.

    One random run can be lucky or unlucky. Averaging many runs, and
    showing a confidence interval, tells us how much to trust a difference.
    """
    rows = [summarise(run(replace(cfg, seed=cfg.seed + i))) for i in range(reps)]
    table = pd.DataFrame(rows)
    out = {"scenario": cfg.name, "volunteers": cfg.volunteers}
    out.update(table.mean().round(1).to_dict())
    suitable = table["suitable_%"].tolist()
    half_width = 1.96 * statistics.stdev(suitable) / reps ** 0.5 if reps > 1 else 0.0
    out["suitable_ci95"] = round(half_width, 1)
    return out


def default_scenarios():
    """A few 'what if' settings a pantry coordinator might test."""
    base = Config()
    matched = {"general": 60, "vegetarian": 28, "halal": 22}  # same 110 parcels
    return [
        base,
        replace(base, name="+1 volunteer", volunteers=3),
        replace(base, name="Culturally matched stock", stock=matched),
        replace(base, name="+1 volunteer & matched", volunteers=3, stock=matched),
    ]


def load_scenarios(path):
    """Read scenarios from a CSV file (one row per scenario).

    Columns: name, volunteers, general, vegetarian, halal.
    Any missing optional setting falls back to the Config default.
    """
    scenarios = []
    with open(path, newline="", encoding="utf-8") as f:
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            try:
                cfg = Config(
                    name=row["name"].strip(),
                    volunteers=int(row["volunteers"]),
                    stock={d: int(row[d]) for d in DIET_SHARES},
                )
                scenarios.append(cfg.validate())
            except (KeyError, ValueError) as err:
                raise ValueError(f"{path} line {line_no}: {err}") from err
    if not scenarios:
        raise ValueError(f"{path} has no scenarios")
    return scenarios


def plot(results, path="results.png"):
    """Save a stacked bar chart of outcomes per scenario."""
    import matplotlib
    matplotlib.use("Agg")  # draw to file, no window needed
    import matplotlib.pyplot as plt

    cols = [f"{o}_%" for o in OUTCOMES]
    ax = results.set_index("scenario")[cols].plot(
        kind="barh", stacked=True, figsize=(9, 4),
        color=["#2a9d8f", "#e9c46a", "#e76f51", "#8d99ae"])
    ax.set_xlabel("% of students")
    ax.set_title("FoodBank outcomes by scenario (average of runs)")
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()
    return path


def parse_args(argv=None):
    """Read command-line options."""
    p = argparse.ArgumentParser(description="Campus food pantry simulator")
    p.add_argument("--scenarios", help="CSV file of scenarios to compare")
    p.add_argument("--volunteers", type=int, help="run one custom scenario")
    p.add_argument("--minutes", type=int, default=180, help="opening time")
    p.add_argument("--reps", type=int, default=20, help="runs per scenario")
    p.add_argument("--csv", default="results.csv", help="output CSV path")
    p.add_argument("--verbose", action="store_true", help="log every student")
    return p.parse_args(argv)


def main(argv=None):
    """Entry point: pick scenarios, run them, print, save CSV and chart."""
    args = parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    log.setLevel(logging.DEBUG if args.verbose else logging.WARNING)  # ours only
    try:
        if args.scenarios:
            scenarios = load_scenarios(args.scenarios)
        elif args.volunteers is not None:
            scenarios = [Config(name="Custom", volunteers=args.volunteers)]
        else:
            scenarios = default_scenarios()
        scenarios = [replace(s, open_minutes=args.minutes).validate() for s in scenarios]
    except (OSError, ValueError) as err:
        raise SystemExit(f"Input error: {err}")

    start = time.perf_counter()
    results = pd.DataFrame([run_replications(s, args.reps) for s in scenarios])
    elapsed = time.perf_counter() - start

    print(results.to_string(index=False))
    results.to_csv(args.csv, index=False)
    print(f"\nSaved {args.csv} and {plot(results)}")
    print(f"{len(scenarios) * args.reps} runs in {elapsed:.2f}s")
    print("Note: inputs are illustrative assumptions, not real pantry data.")
    return results


if __name__ == "__main__":
    main()
