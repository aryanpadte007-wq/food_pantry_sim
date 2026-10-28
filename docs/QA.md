# Demo and marker Q&A

Short, honest answers to questions a marker is likely to ask.
Learn the reasoning, not the wording.

---

## A. The idea and its context

**Q1. What does your program do, in one sentence?**
It simulates a campus food bank session and measures how many students leave with food that suits their dietary needs, so a coordinator can compare choices like more volunteers or a different stock mix.

**Q2. Why this topic?**
Student food insecurity in Australia rose from 42% to 53% between 2022 and 2024, and international students are at higher risk (Kent et al., 2025). Swinburne's Student Union runs a FoodBank because of the cost of living. As an international student, the problem is close to me.

**Q3. What is the societal or cultural perspective?**
Cultural food needs. Leung et al. (2025) found international students struggle to get culturally appropriate food and that pantries are poorly run. My model treats "got food" and "got food you can eat" as different outcomes.

**Q4. Where is the Indigenous perspective?**
The project does not model Indigenous communities, and I do not claim to speak for them. In the reflection I explain that any adaptation for Aboriginal or Torres Strait Islander students should be led by that community, through Swinburne's Moondani Toombadool Centre, and follow Indigenous data sovereignty principles (CARE, Maiam nayri Wingara). The brief says "societal, cultural *or* Indigenous", and my main lens is cultural.

**Q5. Why halal and vegetarian specifically?**
They are common, well-understood dietary needs that general stock often does not meet. They are simplified examples, not a full list. In real use the categories should come from the students served.

**Q6. Is this real data?**
No. The setting (SSU FoodBank, 10am–1pm, walk-in) is real. Arrival rate, service time, diet mix and stock are assumptions, clearly labelled in `docs/EVIDENCE.md`. I test arrival rate across a range in `experiments.py`.

**Q7. How would you get real data?**
The SSU FoodBank uses a QR check-in. Anonymous, aggregate counts (visits per hour, broad diet category, with consent) would replace my arrival and diet assumptions. No names or personal records.

**Q8. Who would use this?**
A food bank coordinator deciding how to spend a limited budget: more volunteers, more food, or a different mix of food.

---

## B. Results

**Q9. What is your main finding?**
At the baseline demand, adding a third volunteer cuts average wait from 3.6 to 0.5 minutes but does not increase suitable outcomes (84.0% vs 83.4%). Re-balancing the same 110 parcels toward vegetarian and halal raises suitable outcomes to 89.0%.

**Q10. Is that difference real or random noise?**
I ran each scenario 20 times and report a 95% confidence interval: 84.0 ± 3.2 vs 89.0 ± 2.9. The intervals overlap slightly, so I call it *likely*, not proven. Every scenario uses the same seeds (common random numbers), so each pair of runs faces the same arrivals; comparing each pair directly, matched stock scored higher in 16 of 20 runs, by an average of 5.0 ± 1.5 points (95% CI). That paired result clearly excludes zero, which is stronger evidence than the separate intervals show. More runs (`--reps 100`) would narrow the intervals.

**Q11. Is there a downside to matched stock?**
Yes. With fewer general parcels, "no food" rises slightly (8.0% → 9.2%). It is a trade-off the community should decide, not the program.

**Q12. What did the experiments show?**
When demand is low, the mix barely matters (everyone is served). Under very high demand, total stock matters more than the mix. Matching helps most at medium demand.

**Q13. What does "+20 general parcels" in `scenarios.csv` show?**
Adding 20 general parcels gives a similar suitable % to re-balancing, but many more students get *unsuitable* food. More food is not the same as the right food.

---

## C. Code and concepts (COS60018 outcome 1 and 2)

**Q14. How did you break the problem down?**
See the table in `docs/DESIGN.md`: settings (`Config`), the decision rule (`choose_parcel`), one run (`run`, with inner `student` and `arrivals`), summaries (`summarise`, `replicate`), file input (`load_scenarios`), file output (`save_results`), and the entry point (`main`).

**Q15. Where are sequence, selection and iteration?**
- Sequence: `student()`: arrive, queue, get served, record.
- Selection: `choose_parcel()`: suitable / unsuitable / no food. `Config.validate()`.
- Iteration: the `while True` loop in `arrivals()`; loops over scenarios and repetitions.

**Q16. Which data structures do you use and why?**
- `dict` for stock and diet shares (look up by diet name).
- `list` of `(diet, wait, outcome)` tuples for results, one per student. Tuples are fixed records that cannot be changed by mistake.
- `tuple` for `OUTCOMES` (fixed, should not change).
- `dataclass` for settings (named fields, defaults, easy to copy with `replace`).
- `Counter` to count outcomes; `dict` rows for summaries.

**Q17. Where is file input and output?**
Input: `load_scenarios()` reads `scenarios.csv` with the `csv` module. Output: `results.csv` via `csv.DictWriter`.

**Q18. What happens with a bad input file?**
`load_scenarios()` catches `KeyError`/`ValueError` and raises a clear message with the line number. `main()` turns it into "Input error: ..." instead of a crash. This is covered by a test.

**Q19. What is a generator and why does SimPy use them?**
A function with `yield`. It pauses and resumes. SimPy uses `yield` to mean "wait for this event", so one student can pause in a queue while time moves on for others.

**Q20. Explain `result = yield req | env.timeout(max_wait)`.**
`|` means "whichever happens first". The student waits for a volunteer *or* until patience runs out. If `req` is in `result`, they got a volunteer; otherwise they gave up.

**Q21. Why `simpy.Resource` for volunteers but a plain dict for stock?**
A `Resource` is something used then released, and students must queue for it, so SimPy is needed. Stock never makes anyone wait (a parcel is either there or not), so a plain dict of counts per diet is simpler and faster than a `simpy.Container`. Each diet still runs out separately.

**Q22. Why `field(default_factory=...)` for stock?**
A plain `dict` default would be shared between every `Config` object. Changing one would change all. `default_factory` creates a fresh dict each time.

**Q23. Why exponential (`expovariate`) times?**
It is the standard model for random walk-in arrivals (a Poisson process). Students arrive independently, which fits a walk-in FoodBank.

**Q24. Why set a random seed?**
Repeatability. The same seed gives exactly the same run, which makes debugging and testing possible.

---

## D. Tools and practice (outcome 3)

**Q25. How did you use version control?**
One commit per stage (6 stages + experiments + docs), each runnable on its own. Stages 3–6 were merged through pull requests from feature branches.

**Q26. How did you test?**
16 pytest tests: repeatability, config not changed by a run, the `choose_parcel` rule in 4 cases, outcomes add to 100, stock never over-issued, more volunteers means shorter wait, no arrivals after closing, 3 kinds of bad settings rejected, CSV reading, bad-line errors, and an end-to-end test of `main()`.

**Q27. Tell us about a bug you found.**
`test_empty_records_do_not_crash` failed. The arrivals loop checked closing time *before* waiting, so one student always arrived after closing. I moved the check *after* the wait. The fix is in the Stage 6 commit message.

**Q28. How do you debug?**
Fixed seeds, tests, and IDE breakpoints in `choose_parcel()` or `student()`. Because runs repeat exactly, a breakpoint hits the same student every time.

**Q29. How did you measure performance?**
`experiments.py` times runs with `time.perf_counter()`: about 1.4 ms per run (down from 2.8 ms before the refactor), growing linearly. 20 repetitions of 4 scenarios take about 0.1 seconds.

**Q30. Why did you remove logging and the chart?**
They added code and a dependency (matplotlib) but did not change what the model can answer. Fixed seeds plus breakpoints give the same tracing as logging. The chart lives on the project web page instead.

---

## E. Limits and next steps (outcome 4 and honesty)

**Q31. What are the biggest limitations?**
Assumed numbers, no validation against real data, no restocking during a session, no repeat visitors, and simplified diet categories.

**Q32. How would you validate the model?**
Compare simulated queue length and parcels issued against real SSU counts for a few sessions, as Kothamasu et al. (2022) did for Texas food banks (within 15%).

**Q33. Could this cause harm?**
A "suitable %" could be used to justify cutting a service. Results must always be shown with their assumptions and confidence intervals. Diet and religion are sensitive, so only aggregate, consented data should be used.

**Q34. Why SimPy and not Pygame?**
The question is about a process (queues, stock) and measuring settings, which is what discrete-event simulation is for. The brief lists "a model of a process using simulation" as a suggested topic.

**Q35. Did you use AI?**
Yes, and it is declared in the commit messages (`Co-Authored-By`). *(Check and follow your unit's AI policy; answer this one truthfully in your own words.)*

**Q36. What would you add next?**
Real SSU data, restocking mid-session, a simple dashboard or Pygame front end for coordinators, and diet categories designed with students.

**Q37. The guide says 200–300 lines. Why is yours 178?**
The brief says a clear, well-explained program scores better than a large one. Stage 6 was 270 lines and Stage 7 was 298. Stage 8 removes everything that did not change the answer, while keeping file input/output, validation, error handling, confidence intervals and tests. With `experiments.py` (52 lines) the program is 230 lines; the tests add 81 more. The growth is visible in `stages/`.

---

## F. Refactor (Stage 7)

**Q38. What did you change in the refactor and why?**
- Moved the food decision into `choose_parcel()`, a pure function: easy to test and reuse.
- Each run uses its own `random.Random(seed)`: no hidden global state.
- Replaced `simpy.Container` with a dict of counts, since stock never makes anyone wait.
- Removed pandas: `Counter` and `statistics` were enough. Run time halved (2.8 → 1.4 ms).
- `env.run()` now stops by itself once the last student leaves, instead of a guessed end time.

**Q39. Why did the results change slightly after the refactor?**
Each run now uses its own random generator, so the random numbers differ from Stage 6. The conclusions are the same: an extra volunteer cuts waiting but not unsuitable food; matched stock raises suitable outcomes. This is a reminder that single numbers from a simulation are estimates, which is why I report confidence intervals.

**Q40. What are closures, and why are `student` and `arrivals` inside `run`?**
They are functions defined inside `run()` that can use its variables (`env`, `volunteers`, `stock`, `rng`, `records`). This removes the need for a separate `Pantry` class and keeps all state for one run in one place.

---

## G. Simplification (Stage 8)

**Q41. What did you remove in Stage 8, and why is it still a strong project?**
Removed: logging and `--verbose`, the matplotlib chart, the `--volunteers`/`--minutes` options, the hard-coded scenario list, and the `Record` class. Each added code without changing what the model can answer.
Kept: SimPy queue with patience, the culturally-appropriate decision rule, file input and output, validation with clear errors, repeated runs with 95% confidence intervals, a paired comparison in `experiments.py`, and 16 tests.

**Q42. Where are the scenarios now?**
In `scenarios.csv`. A coordinator can add a "what if" in Excel without editing code.

**Q43. How do you know the simplified version still gives the same answers?**
Same seeds give exactly the same results as Stage 7 (84.0%, 83.4%, 89.0%, 88.2%), and all tests pass.
