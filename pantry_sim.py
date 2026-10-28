"""
Campus FoodBank Simulator (final version - Stage 8, simplified).

A SimPy model of a free, walk-in campus food bank, based on the
Swinburne Student Union FoodBank (open 10am-1pm on weekdays).

Why: food insecurity among Australian university students rose from 42%
to 53% between 2022 and 2024, with international students at higher risk
(Kent et al., 2025), and students report a lack of culturally appropriate
food at campus pantries (Leung et al., 2025). The model asks: how many
students leave with food that suits their diet, not just any food?

All operating numbers are illustrative assumptions, not real data.

Run:   python pantry_sim.py                    (reads scenarios.csv)
       python pantry_sim.py my.csv --reps 50
"""

import argparse
import csv
import random
import statistics
from collections import Counter
from dataclasses import dataclass, field, replace

import simpy

# Share of students needing each diet (ASSUMPTION).
DIET_SHARES = {"general": 0.55, "vegetarian": 0.25, "halal": 0.20}
OUTCOMES = ("suitable", "unsuitable", "no_food", "gave_up")


@dataclass
class Config:
    """Settings for one scenario. Times are in minutes."""

    name: str = "Baseline"
    volunteers: int = 2
    stock: dict = field(default_factory=lambda: {"general": 70, "vegetarian": 25, "halal": 15})
    open_minutes: float = 180       # 10am-1pm
    arrival_gap: float = 1.5        # average minutes between students
    service_time: float = 2.5       # average minutes to pack a parcel
    max_wait: float = 20            # students give up after this long
    seed: int = 42

    def validate(self):
        """Raise ValueError if a setting makes no sense; return self."""
        if self.volunteers < 1:
            raise ValueError(f"{self.name}: need at least 1 volunteer")
        if set(self.stock) != set(DIET_SHARES):
            raise ValueError(f"{self.name}: stock needs {list(DIET_SHARES)}")
        if min(self.stock.values()) < 0:
            raise ValueError(f"{self.name}: stock cannot be negative")
        return self


def choose_parcel(stock, diet):
    """Return (outcome, diet to take stock from, or None).

    The core rule, kept free of SimPy so it is easy to test and change.
    """
    if stock[diet] > 0:
        return "suitable", diet
    if diet != "general" and stock["general"] > 0:
        return "unsuitable", "general"      # food, but not what they need
    return "no_food", None


def run(cfg):
    """Simulate one session. Return a list of (diet, wait, outcome)."""
    rng = random.Random(cfg.seed)
    env = simpy.Environment()
    volunteers = simpy.Resource(env, capacity=cfg.volunteers)
    stock = dict(cfg.stock)                 # copy, so cfg is not changed
    records = []

    def student(diet):
        arrived = env.now
        with volunteers.request() as turn:
            # Wait for a volunteer OR give up - whichever happens first.
            result = yield turn | env.timeout(cfg.max_wait)
            wait = env.now - arrived
            if turn not in result:
                outcome = "gave_up"
            else:
                yield env.timeout(rng.expovariate(1 / cfg.service_time))
                outcome, take = choose_parcel(stock, diet)
                if take:
                    stock[take] -= 1
        records.append((diet, wait, outcome))

    def arrivals():
        while True:
            yield env.timeout(rng.expovariate(1 / cfg.arrival_gap))
            if env.now >= cfg.open_minutes:
                return                      # doors closed
            diet = rng.choices(list(DIET_SHARES), weights=DIET_SHARES.values())[0]
            env.process(student(diet))

    env.process(arrivals())
    env.run()                               # ends when the last student leaves
    return records


def summarise(records):
    """Percentage of students per outcome, plus average wait of those served."""
    total = len(records) or 1
    counts = Counter(outcome for _, _, outcome in records)
    row = {f"{o}_%": 100 * counts[o] / total for o in OUTCOMES}
    waits = [w for _, w, o in records if o != "gave_up"]
    row["wait_min"] = statistics.fmean(waits) if waits else 0.0
    return row


def replicate(cfg, reps=20):
    """Run a scenario `reps` times (seeds seed, seed+1, ...) and average.

    Also returns a 95% confidence interval for suitable %, so we can tell
    a real difference from random noise.
    """
    rows = [summarise(run(replace(cfg, seed=cfg.seed + i))) for i in range(reps)]
    result = {"scenario": cfg.name, "volunteers": cfg.volunteers}
    for key in rows[0]:
        result[key] = round(statistics.fmean(r[key] for r in rows), 1)
    suitable = [r["suitable_%"] for r in rows]
    result["ci95"] = round(1.96 * statistics.stdev(suitable) / reps ** 0.5, 1) if reps > 1 else 0.0
    return result


def load_scenarios(path):
    """Read scenarios from CSV: name, volunteers, general, vegetarian, halal."""
    scenarios = []
    with open(path, newline="", encoding="utf-8") as f:
        for line, row in enumerate(csv.DictReader(f), start=2):
            try:
                stock = {diet: int(row[diet]) for diet in DIET_SHARES}
                cfg = Config(row["name"], int(row["volunteers"]), stock)
                scenarios.append(cfg.validate())
            except (KeyError, ValueError, TypeError) as err:
                raise ValueError(f"{path} line {line}: {err}") from err
    if not scenarios:
        raise ValueError(f"{path} has no scenarios")
    return scenarios


def save_results(results, path):
    """Write result rows to a CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)


def main(argv=None):
    """Read scenarios, run each one, print a table and save a CSV."""
    parser = argparse.ArgumentParser(description="Campus FoodBank simulator")
    parser.add_argument("scenarios", nargs="?", default="scenarios.csv")
    parser.add_argument("--reps", type=int, default=20, help="runs per scenario")
    parser.add_argument("--out", default="results.csv", help="output CSV")
    args = parser.parse_args(argv)

    try:
        scenarios = load_scenarios(args.scenarios)
    except (OSError, ValueError) as err:
        raise SystemExit(f"Input error: {err}")

    results = [replicate(cfg, args.reps) for cfg in scenarios]
    print(f"{'Scenario':<26}{'Suitable %':>14}{'Unsuitable %':>14}{'No food %':>11}{'Wait min':>10}")
    for r in results:
        suitable = f"{r['suitable_%']} ±{r['ci95']}"
        print(f"{r['scenario']:<26}{suitable:>14}{r['unsuitable_%']:>14}{r['no_food_%']:>11}{r['wait_min']:>10}")
    save_results(results, args.out)
    print(f"\nSaved {args.out}. Inputs are illustrative assumptions, not real data.")
    return results


if __name__ == "__main__":
    main()
