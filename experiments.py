"""
Experiments: how results change with demand, and how fast the model runs.

Run:  python experiments.py
"""

import statistics
import time
from dataclasses import replace

import pantry_sim as ps

MATCHED = {"general": 60, "vegetarian": 28, "halal": 22}   # same 110 parcels


def sensitivity(gaps=(3.0, 2.0, 1.5, 1.2, 1.0)):
    """Suitable % for baseline vs matched stock as the pantry gets busier."""
    print("Gap (min)  Baseline %   Matched %")
    for gap in gaps:
        base = ps.Config(arrival_gap=gap)
        b = ps.replicate(base)
        m = ps.replicate(replace(base, stock=MATCHED))
        print(f"{gap:>9}  {b['suitable_%']:>6} ±{b['ci95']:<4} {m['suitable_%']:>6} ±{m['ci95']}")


def paired_difference(reps=20):
    """Compare the two stock mixes seed by seed (same arrivals each time)."""
    diffs = []
    for i in range(reps):
        cfg = ps.Config(seed=42 + i)
        base = ps.summarise(ps.run(cfg))["suitable_%"]
        matched = ps.summarise(ps.run(replace(cfg, stock=MATCHED)))["suitable_%"]
        diffs.append(matched - base)
    mean = sum(diffs) / reps
    ci = 1.96 * statistics.stdev(diffs) / reps ** 0.5
    wins = sum(d > 0 for d in diffs)
    print(f"\nMatched minus baseline: {mean:.1f} ± {ci:.1f} points; matched better in {wins}/{reps} runs")


def timing(rep_counts=(10, 100, 200)):
    """Time how long replications take."""
    print("\nReps  Seconds  ms/run")
    for reps in rep_counts:
        start = time.perf_counter()
        ps.replicate(ps.Config(), reps)
        secs = time.perf_counter() - start
        print(f"{reps:>4}  {secs:>7.3f}  {1000 * secs / reps:>6.2f}")


if __name__ == "__main__":
    sensitivity()
    paired_difference()
    timing()
