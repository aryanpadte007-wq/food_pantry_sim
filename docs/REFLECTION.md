# Reflection: impact, responsibility and development practice

## 1. Social and cultural context
- **Swinburne context:** the Swinburne Student Union runs a free walk-in FoodBank (10am–1pm weekdays, used as the model's 180-minute session), free weekday breakfast and a Wednesday BBQ, explicitly to help with the cost of living. The model asks how a service like this could be run to meet more students' needs.
- **Scale:** food insecurity among Australian university students rose from 42% to 53% (2022–2024), with international students at higher risk (Kent et al., 2025); 1 in 3 Australian households are food insecure (Foodbank, 2025).
- **Research context:** Leung et al. (2025) found that international students at an Australian university faced a lack of **culturally appropriate food**, inefficient pantry operations, stigma and poor communication about support. University of Melbourne SAFES research also documents student food insecurity.
- A food bank can serve many students and still fail those whose dietary or religious needs are not met. The model separates "got food" from "got food they can eat".
- The model makes this visible by separating "got food" from "got food they can eat".

## 2. What the results suggest (and do not)
- An extra volunteer cuts waiting (3.6 → 0.5 min) but does **not** raise suitable outcomes.
- Re-balancing the **same** 110 parcels toward vegetarian/halal raises suitable outcomes (84% → 89%), with a small rise in "no food" for general-diet students. That trade-off is a real decision for the community, not the program.
- Under heavy demand (`experiments.py`), total stock matters more than mix. Matching helps most at medium demand.
- **Limit:** all inputs are assumptions. The program shows *how* to reason about choices, not *what* a real pantry should do.

## 3. Responsible and inclusive development
- **Not speaking for communities.** Diet categories are simplified. Real categories should come from the students served, not from a programmer.
- **Data, if collected for real:** diet and religion are sensitive. Collect only aggregate counts with consent, never names. The CARE principles for Indigenous data governance (Collective benefit, Authority to control, Responsibility, Ethics) are a useful model here: the community the data describes should benefit from and control it.
- **Indigenous perspective:** this project does not model Indigenous communities and does not claim to. If adapted for Aboriginal or Torres Strait Islander students at Swinburne, the design should be led by that community. That means working with Swinburne's Moondani Toombadool Centre and its Indigenous Student Charter, and following Indigenous data sovereignty principles (CARE; Maiam nayri Wingara).
- **Risk of misuse:** a "suitable %" could be used to justify cutting services. Results should always be shown with their assumptions and confidence intervals.

## 4. Tools and practice
- **Refactoring:** Stage 7 simplified the design (pure decision function, own random generator, no pandas) and halved run time, with the tests confirming behaviour stayed correct. Stage 8 then cut the program from 298 to 178 lines without changing any result.
- **Version control:** built in seven stages, one commit each (see `git log`). Each stage runs on its own.
- **Testing:** `pytest` suite (16 tests) covers repeatability, stock limits, bad input and file reading.
- **Debugging:** a test (`test_empty_records_do_not_crash`) exposed a real bug: the arrivals loop checked the clock *before* waiting, so one student always arrived after closing. Fixed by checking *after* the wait. A regression test now guards against it.
- **Performance measurement:** `experiments.py` times runs (~1.4 ms per run after the refactor, down from 2.8 ms; scales linearly), so 20 repetitions are cheap.
- **IDE / debugger:** fixed seeds make every run repeatable, so breakpoints in `choose_parcel()` hit the same student every time.

## 5. What I would do next
- Validate against real counts, as Kothamasu et al. (2022) did for Texas food banks.
- Replace assumptions with real (consented, aggregate) data, e.g. visit counts from the SSU FoodBank QR check-in.
- Add restocking mid-session and repeat visitors.
- Simple Pygame or web front end for coordinators.

## Sources
See `EVIDENCE.md` for the full list. Additional to those below:
- Kent, K., et al. (2025). *Health Promotion Journal of Australia, 36*(2), e70037. https://doi.org/10.1002/hpja.70037
- Foodbank Australia (2025). *Hunger Report 2025.* https://reports.foodbank.org.au/foodbank-hunger-report-2025/
- Kothamasu, M., et al. (2022). *Winter Simulation Conference.* https://www.informs-sim.org/wsc22papers/160.pdf
- Swinburne Student Union. *Services* (FoodBank, Daily Breakfast, Wednesday BBQ). https://ssu.org.au/services
- Swinburne Student Union. *Welfare* (FoodBank location and access). https://ssu.org.au/category/welfare/
- Swinburne University. *COS60018 Programming Principles and Practices.* https://www.swinburne.edu.au/course/unit/c/cos60018/
- Swinburne University. *Moondani Toombadool Centre.* https://swinburne.edu.au/indigenous
- Swinburne University. *Indigenous Student Charter: our key principles.* https://swinburne.edu.au/life-at-swinburne/student-support-services/indigenous-student-services/indigenous-student-charter
- Leung, K. M., Charlton, K., McMahon, A., Walton, K., Roy, R., & Kent, K. (2025). A qualitative exploration of food insecurity and institutional support among international students at a regional Australian university. *Health Promotion Journal of Australia, 36*(4), e70080. https://doi.org/10.1002/hpja.70080
- University of Melbourne SAFES. *Food insecurity of university students.* https://safes.unimelb.edu.au/research/food-politics-and-policy/research/food-insecurity-of-university-students
- Western Sydney University. *Food security programs.* https://www.westernsydney.edu.au/home/students/support/food-security-programs
- Global Indigenous Data Alliance. *CARE Principles for Indigenous Data Governance.* https://www.gida-global.org/care
- Maiam nayri Wingara Indigenous Data Sovereignty Collective. https://www.maiamnayriwingara.org/
- SimPy documentation. https://simpy.readthedocs.io/en/latest/
