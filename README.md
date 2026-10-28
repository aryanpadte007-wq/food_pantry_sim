# Campus Food Pantry Simulator (SimPy)

A small discrete-event simulation of a student-run campus food bank, modelled on the
Swinburne Student Union (SSU) FoodBank (free, walk-in, open 10am–1pm on weekdays).
It tests simple "what if" choices — number of volunteers, how much stock, and how much
**culturally appropriate** stock (vegetarian, halal) — and reports how many students
leave with a parcel that actually meets their dietary needs.

## Why this project
- Swinburne students already rely on free food services: the SSU runs a FoodBank, free weekday breakfast and a Wednesday BBQ to help with the cost of living.
- A 2025 study of international students at an Australian university (Leung et al.) found a lack of culturally appropriate food, inefficient pantry operations and stigma were key barriers.
- Food insecurity among Australian university students rose from 42% (2022) to 53% (2024), and international students had higher odds (Kent et al., 2025).
- 1 in 3 Australian households were food insecure in the past year (Foodbank Hunger Report 2025).
- Full evidence table, with every model setting marked as evidence or assumption: `docs/EVIDENCE.md`.
- This program does **not** speak for any community. It is a learning model; every number is an illustrative assumption.

## Install
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
python pantry_sim.py                     # compare the scenarios in scenarios.csv
python pantry_sim.py my_scenarios.csv    # your own scenarios
python pantry_sim.py --reps 100          # more runs = narrower confidence intervals
python experiments.py                    # demand sensitivity, paired comparison, timing
python -m pytest -q                      # run the 16 tests
```
Output: a table in the terminal and `results.csv`.

Each row of `scenarios.csv` is one "what if": `name, volunteers, general, vegetarian, halal`
(the last three are parcels of each diet type).

## Project layout
| Path | Purpose |
|---|---|
| `pantry_sim.py` | Final program |
| `scenarios.csv` | Example input file |
| `experiments.py` | Demand sensitivity and performance timing |
| `tests/` | pytest unit tests |
| `stages/` | Each build stage as a runnable file |
| `docs/DESIGN.md` | Decomposition, pseudocode, flowchart |
| `docs/REFLECTION.md` | Social/cultural impact, ethics, tools used |
| `docs/EVIDENCE.md` | Every claim and setting linked to a source |
| `docs/QA.md` | 37 likely demo/marker questions with answers |
| `PUSH_GUIDE.md`, `push_with_prs.sh` | Push to GitHub with one PR per stage |
| `docs/*.html` | pydoc API documentation |

## How the project was built (stages/)
| Stage | File | What was added |
|---|---|---|
| 1 | `stage1_basic_queue.py` | Students arrive randomly and queue for one volunteer (SimPy basics) |
| 2 | `stage2_config_and_stats.py` | `Config` dataclass, `Pantry` class, patience/giving up, average wait |
| 3 | `stage3_food_stock.py` | Diet groups, `simpy.Container` stock, suitable / unsuitable / no-food outcomes |
| 4 | `stage4_scenarios_pandas.py` | pandas summaries, repeated runs, scenario comparison |
| 5 | `stage5_cli_export.py` | Command-line options, CSV + chart export |
| 6 | `stage6_final.py` | CSV scenario input, validation, logging, 95% CI, timing, closing-time bug fix |
| 7 | `stage7_refactor.py` | Refactor: pure `choose_parcel` rule, own random generator, no pandas, ~2× faster |
| 8 | `stage8_simplified.py` (= `pantry_sim.py`) | Simplified to 178 lines: scenarios come from CSV, SimPy is the only library, fewer options |

The included `.git` history has one commit per stage. `push_with_prs.sh` pushes it to GitHub with one pull request per stage (see `PUSH_GUIDE.md`).

## Limitations
- Arrival rate, service time, diet shares and stock levels are assumptions, not real data.
- No restocking during a session, no repeat visitors, no budget constraints.

## Sources
Full list with how each is used: `docs/EVIDENCE.md`.
- Kent, K., et al. (2025). Food insecurity among Australian university students is higher and more severe across an extended period of high inflation. *Health Promotion Journal of Australia, 36*(2), e70037. https://doi.org/10.1002/hpja.70037
- Foodbank Australia (2025). *Hunger Report 2025.* https://reports.foodbank.org.au/foodbank-hunger-report-2025/
- Kothamasu, M., et al. (2022). Modeling and simulation of food bank disaster relief operations. *Winter Simulation Conference.* https://www.informs-sim.org/wsc22papers/160.pdf
- Swinburne Student Union. *Services* (FoodBank, Daily Breakfast, Wednesday BBQ). https://ssu.org.au/services
- Swinburne Student Union. *Welfare* (FoodBank location and access). https://ssu.org.au/category/welfare/
- Swinburne University. *COS60018 Programming Principles and Practices.* https://www.swinburne.edu.au/course/unit/c/cos60018/
- Leung, K. M., Charlton, K., McMahon, A., Walton, K., Roy, R., & Kent, K. (2025). A qualitative exploration of food insecurity and institutional support among international students at a regional Australian university. *Health Promotion Journal of Australia, 36*(4), e70080. https://doi.org/10.1002/hpja.70080
- Western Sydney University. *Food security programs* (example of a university food relief model). https://www.westernsydney.edu.au/home/students/support/food-security-programs
- Global Indigenous Data Alliance. *CARE Principles.* https://www.gida-global.org/care
- University of Melbourne SAFES: *Food insecurity of university students.* https://safes.unimelb.edu.au/research/food-politics-and-policy/research/food-insecurity-of-university-students
- SimPy documentation: https://simpy.readthedocs.io/en/latest/
