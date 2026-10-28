"""
Campus Food Pantry Simulator (Stage 7 - refactored for efficiency and reuse).

A small SimPy model of a student-run campus food bank, modelled on the
Swinburne Student Union (SSU) FoodBank, a free walk-in service open
10am-1pm on weekdays (180 minutes, as used below).

Why this matters:
    Food insecurity among Australian university students rose from 42% to
    53% between 2022 and 2024, with international students at higher risk
    (Kent et al., 2025). A study of international students (Leung et al.,
    2025) found a lack of culturally appropriate food and inefficient
    pantry operations were key barriers. This program lets a food bank
    coordinator test simple choices - volunteers, stock and culturally
    suitable stock - and see how many students get a parcel that meets
    their needs.

Not a forecasting tool or a voice for any community: every number is an
illustrative assumption to be replaced with real, consented data.

Reuse: import Config, choose_parcel, run, summarise, compare or
load_scenarios on their own.

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
from collections import Counter
from dataclasses import dataclass, field, fields, replace

import simpy

log = logging.getLogger("pantry")

# Dietary groups and the share of students needing each (ASSUMPTIONS).
DIET_SHARES = {"general": 0.55, "vegetarian": 0.25, "halal": 0.20}
DIETS = tuple(DIET_SHARES)
WEIGHTS = tuple(DIET_SHARES.values())
OUTCOMES = ("suitable", "unsuitable", "no_food", "gave_up")


@dataclass(frozen=True)
class Record:
    """What happened to one student."""

    diet: str
    wait: float
    outcome: str


@dataclass
class Config:
    """All settings for one simulation run (times are in minutes)."""

    name: str = "Baseline"
    volunteers: int = 2             # people serving at the counter
    open_minutes: float = 180       # SSU FoodBank 10am-1pm = 3 hours
    mean_arrival_gap: float = 1.5   # average minutes between arrivals
    mean_service_time: float = 2.5  # average minutes to pack one parcel
    max_wait: float = 20.0          # students give up after this long
    stock: dict = field(default_factory=lambda: {"general": 70, "vegetarian": 25, "halal": 15})
    seed: int = 42

    def validate(self):
        """Raise ValueError if a setting makes no sense; return self."""
        if self.volunteers < 1:
            raise ValueError(f"{self.name}: need at least 1 volunteer")
        if min(self.open_minutes, self.mean_arrival_gap,
               self.mean_service_time, self.max_wait) <= 0:
            raise ValueError(f"{self.name}: times must be positive")
        if set(self.stock) != set(DIETS):
            raise ValueError(f"{self.name}: stock needs {sorted(DIETS)}")
        if any(n < 0 for n in self.stock.values()):
            raise ValueError(f"{self.name}: stock cannot be negative")
        return self


def choose_parcel(stock, diet):
    """Decide which stock to use for a student. Pure function, no SimPy.

    Returns (outcome, diet_to_take_from) - the second is None if nothing
    can be given. Kept separate so the rule is easy to test and change.
    """
    if stock[diet] > 0:
        return "suitable", diet
    if diet != "general" and stock["general"] > 0:
        return "unsuitable", "general"   # food, but not what they need
    return "no_food", None


def run(cfg):
    """Run one simulation and return a list of Record objects."""
    rng = random.Random(cfg.seed)        # own generator: no global state
    env = simpy.Environment()
    counter = simpy.Resource(env, capacity=cfg.volunteers)
    stock = dict(cfg.stock)              # copy so cfg is never changed
    records = []

    def student(diet):
        """One student: arrive, queue (or give up), get a parcel, leave."""
        arrived = env.now
        with counter.request() as req:
            # Wait for a volunteer OR run out of patience, whichever is first.
            result = yield req | env.timeout(cfg.max_wait)
            waited = env.now - arrived
            if req in result:
                yield env.timeout(rng.expovariate(1 / cfg.mean_service_time))
                outcome, take = choose_parcel(stock, diet)
                if take:
                    stock[take] -= 1
            else:
                outcome = "gave_up"
        log.debug("t=%6.1f %-10s %-10s waited %.1f", env.now, diet, outcome, waited)
        records.append(Record(diet, waited, outcome))

    def arrivals():
        """Create students until closing time."""
        while True:
            yield env.timeout(rng.expovariate(1 / cfg.mean_arrival_gap))
            if env.now >= cfg.open_minutes:
                return                    # doors closed
            diet = rng.choices(DIETS, weights=WEIGHTS)[0]
            env.process(student(diet))

    env.process(arrivals())
    env.run()                             # stops by itself once the queue clears
    return records


def summarise(records):
    """Turn records into the percentages a coordinator cares about."""
    total = len(records)
    counts = Counter(r.outcome for r in records)
    row = {"students": total}
    for outcome in OUTCOMES:
        row[f"{outcome}_%"] = 100 * counts[outcome] / total if total else 0.0
    waits = [r.wait for r in records if r.outcome != "gave_up"]
    row["avg_wait_min"] = statistics.fmean(waits) if waits else 0.0
    return row


def run_replications(cfg, reps=20):
    """Repeat a scenario with seeds seed, seed+1, ... and average the results.

    Returns the mean of each measure plus a 95% confidence interval on
    suitable %, so we can judge whether a difference is real or noise.
    """
    rows = [summarise(run(replace(cfg, seed=cfg.seed + i))) for i in range(reps)]
    out = {"scenario": cfg.name, "volunteers": cfg.volunteers}
    for key in rows[0]:
        out[key] = round(statistics.fmean(r[key] for r in rows), 1)
    suitable = [r["suitable_%"] for r in rows]
    spread = statistics.stdev(suitable) if reps > 1 else 0.0
    out["suitable_ci95"] = round(1.96 * spread / reps ** 0.5, 1)
    return out


def compare(scenarios, reps=20):
    """Run several scenarios and return one result dict per scenario."""
    return [run_replications(cfg, reps) for cfg in scenarios]


MATCHED_STOCK = {"general": 60, "vegetarian": 28, "halal": 22}  # same 110 parcels


def default_scenarios():
    """A few 'what if' settings a coordinator might test."""
    base = Config()
    changes = [
        {},
        {"name": "+1 volunteer", "volunteers": 3},
        {"name": "Culturally matched stock", "stock": MATCHED_STOCK},
        {"name": "+1 volunteer & matched", "volunteers": 3, "stock": MATCHED_STOCK},
    ]
    return [replace(base, **change) for change in changes]


def load_scenarios(path):
    """Read scenarios from a CSV file (one row per scenario).

    Required columns: name, general, vegetarian, halal.
    Any other Config field (e.g. volunteers, max_wait) may be added as a
    column; missing ones use the Config default.
    """
    types = {f.name: f.type for f in fields(Config) if f.name not in ("name", "stock")}
    convert = {"int": int, "float": float, int: int, float: float}
    scenarios = []
    with open(path, newline="", encoding="utf-8") as f:
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            try:
                settings = {k: convert[types[k]](v) for k, v in row.items()
                            if k in types and v not in ("", None)}
                stock = {d: int(row[d]) for d in DIETS}
                cfg = Config(name=row["name"].strip(), stock=stock, **settings)
                scenarios.append(cfg.validate())
            except (KeyError, ValueError, TypeError) as err:
                raise ValueError(f"{path} line {line_no}: {err}") from err
    if not scenarios:
        raise ValueError(f"{path} has no scenarios")
    return scenarios


def save_csv(results, path):
    """Write a list of result dicts to a CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    return path


def print_table(results):
    """Print result dicts as an aligned text table."""
    cols = list(results[0])
    widths = {c: max(len(c), *(len(str(r[c])) for r in results)) for c in cols}
    print("  ".join(c.rjust(widths[c]) for c in cols))
    for r in results:
        print("  ".join(str(r[c]).rjust(widths[c]) for c in cols))


def plot(results, path="results.png"):
    """Save a stacked bar chart of outcomes per scenario."""
    import matplotlib
    matplotlib.use("Agg")                # draw to file, no window needed
    import matplotlib.pyplot as plt

    names = [r["scenario"] for r in results]
    colours = ["#2a9d8f", "#e9c46a", "#e76f51", "#8d99ae"]
    fig, ax = plt.subplots(figsize=(9, 4))
    left = [0.0] * len(results)
    for outcome, colour in zip(OUTCOMES, colours):
        values = [r[f"{outcome}_%"] for r in results]
        ax.barh(names, values, left=left, color=colour, label=outcome)
        left = [a + b for a, b in zip(left, values)]
    ax.set_xlabel("% of students")
    ax.set_title("FoodBank outcomes by scenario (average of runs)")
    ax.invert_yaxis()
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def parse_args(argv=None):
    """Read command-line options."""
    p = argparse.ArgumentParser(description="Campus food pantry simulator")
    p.add_argument("--scenarios", help="CSV file of scenarios to compare")
    p.add_argument("--volunteers", type=int, help="run one custom scenario")
    p.add_argument("--minutes", type=float, default=180, help="opening time")
    p.add_argument("--reps", type=int, default=20, help="runs per scenario")
    p.add_argument("--csv", default="results.csv", help="output CSV path")
    p.add_argument("--verbose", action="store_true", help="log every student")
    return p.parse_args(argv)


def pick_scenarios(args):
    """Choose scenarios from the command-line options."""
    if args.scenarios:
        scenarios = load_scenarios(args.scenarios)
    elif args.volunteers is not None:
        scenarios = [Config(name="Custom", volunteers=args.volunteers)]
    else:
        scenarios = default_scenarios()
    return [replace(s, open_minutes=args.minutes).validate() for s in scenarios]


def main(argv=None):
    """Entry point: pick scenarios, run them, print, save CSV and chart."""
    args = parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    log.setLevel(logging.DEBUG if args.verbose else logging.WARNING)
    try:
        scenarios = pick_scenarios(args)
    except (OSError, ValueError) as err:
        raise SystemExit(f"Input error: {err}")

    start = time.perf_counter()
    results = compare(scenarios, args.reps)
    elapsed = time.perf_counter() - start

    print_table(results)
    print(f"\nSaved {save_csv(results, args.csv)} and {plot(results)}")
    print(f"{len(scenarios) * args.reps} runs in {elapsed:.2f}s")
    print("Note: inputs are illustrative assumptions, not real pantry data.")
    return results


if __name__ == "__main__":
    main()
