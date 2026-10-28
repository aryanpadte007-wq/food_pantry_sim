# Evidence base

Every claim and every model setting, linked to where it comes from.
**Rule used:** if a number is not backed by a source, it is labelled an *assumption*.

## 1. The problem is real and growing

| # | Evidence | Source | Used for |
|---|---|---|---|
| E1 | 1 in 3 Australian households (3.5 million) were food insecure in the past 12 months; 48% of renting households; cost of living was the top concern for 91% of food-insecure households. | Foodbank Australia, *Hunger Report 2025* | National context: food relief demand is high and cost-driven |
| E2 | Food insecurity among Australian university students rose from **42% (2022) to 53% (2024)**; severe food insecurity rose from 17% to 29%. Younger, on-campus and **international students** had significantly higher odds. Surveys of 1,249 and 1,603 students. | Kent et al. (2025), *Health Promotion Journal of Australia* 36(2), e70037 | Why students, and international students in particular |
| E3 | Earlier baseline survey of the same population (2022), measured with the USDA six-item short form. | Kent et al. (2022), *Nutrients* 14(19), 3956 | Shows a repeat measurement, not a one-off |
| E4 | ~14–15% of undergraduates (domestic and international) regularly go without food or other necessities. | Universities Australia *Student Finances Survey* (2017, published 2018), via University of Melbourne Pursuit | Long-running issue, not only post-COVID |
| E5 | University of Melbourne SAFES research program on student food insecurity. | UniMelb SAFES | Victorian/Melbourne context |

## 2. Culturally appropriate food matters

| # | Evidence | Source | Used for |
|---|---|---|---|
| E6 | International students reported a **lack of culturally appropriate food choices**, high cost of living, and barriers to support: **inefficient pantry operations**, stigma and poor communication. Authors call for "tailored, culturally appropriate interventions". 4 focus groups, 17 students. | Leung, Charlton, McMahon, Walton, Roy & Kent (2025), *Health Promotion Journal of Australia* 36(4), e70080 | Core design choice: separate "suitable" from "unsuitable" food; model pantry operations (queue, volunteers) |

## 3. The Swinburne setting

| # | Evidence | Source | Used for |
|---|---|---|---|
| E7 | SSU runs a free FoodBank "stocked with free food and other essential items" for the cost-of-living crisis, plus free weekday breakfast and a Wednesday BBQ. Listed hours: **10am–1pm, Mon–Fri**. | Swinburne Student Union, *Services* | `open_minutes = 180` |
| E8 | FoodBank is a free, **walk-in** service (no appointment), UN Building Level 4, students check in via QR code. An older post lists 10am–4pm. | SSU, *Welfare* posts | Random walk-in arrivals (Poisson process); QR check-in = future real data source; hours flagged as uncertain |
| E9 | Other Australian universities run comparable food security programs (pantry, low-cost meals). | Western Sydney University, *Food security programs* | Model is transferable beyond one campus |

## 4. Method is an accepted approach

| # | Evidence | Source | Used for |
|---|---|---|---|
| E10 | Discrete-event simulation was used to model a network of Texas food banks (donations, warehouse, distribution), validated against historical data within 15%; collaboration raised demand fulfilment substantially. | Kothamasu, Mendez-Mediavilla & Perez (2022), *Proceedings of the Winter Simulation Conference* | Shows DES is a recognised way to study food bank operations; also shows what proper validation looks like (which this project does not yet have) |
| E11 | SimPy: process-based discrete-event simulation for Python. | SimPy documentation | Library choice (required by the unit brief) |

## 5. Unit requirements

| # | Evidence | Source | Used for |
|---|---|---|---|
| E12 | COS60018 outcomes: decomposition, flowcharts and pseudocode; file I/O and data structures; professional tools (IDE, debugger, version control); social, cultural and Indigenous perspectives. Topics include debugging, experimentation and performance measurement. | Swinburne, *COS60018 unit page* | Structure of `DESIGN.md`, tests, experiments, `REFLECTION.md` |
| E13 | Swinburne's Moondani Toombadool Centre and Indigenous Student Charter. | Swinburne | Indigenous perspective: who should lead any adaptation |
| E14 | CARE principles (Collective benefit, Authority to control, Responsibility, Ethics); Maiam nayri Wingara Indigenous Data Sovereignty principles. | GIDA; Maiam nayri Wingara | Responsible data collection |

## 6. Model settings: evidence vs assumption

| Setting | Value | Status |
|---|---|---|
| Opening time | 180 min | **Evidence** (E7), hours need confirming (E8) |
| Walk-in, random arrivals | Exponential gaps | **Justified** by walk-in service (E8); standard queueing assumption |
| Average gap between arrivals | 1.5 min (~120 students/session) | *Assumption.* Tested from 1.0 to 3.0 in `experiments.py` |
| Service time | 2.5 min average | *Assumption* |
| Patience before leaving | 20 min | *Assumption* |
| Diet mix | 55% general / 25% vegetarian / 20% halal | *Assumption.* No public breakdown found for Swinburne |
| Stock | 110 parcels | *Assumption* |

**What this means for a marker's question "where do your numbers come from?"**
The *problem* and the *setting* are evidence-based. The *operating numbers* are assumptions, labelled as such, tested across a range, and designed to be replaced with SSU check-in data.

## Full references
1. Foodbank Australia (2025). *Foodbank Hunger Report 2025.* https://reports.foodbank.org.au/foodbank-hunger-report-2025/ (media release: https://www.foodbank.org.au/foodbank-hunger-report-2025-media-release/)
2. Kent, K., Visentin, D., Peterson, C., Elliott, C., Primo, C., & Murray, S. (2025). Food insecurity among Australian university students is higher and more severe across an extended period of high inflation: A repeated cross-sectional study 2022–2024. *Health Promotion Journal of Australia, 36*(2), e70037. https://doi.org/10.1002/hpja.70037
3. Kent, K., et al. (2022). *Nutrients, 14*(19), 3956. https://doi.org/10.3390/nu14193956
4. University of Melbourne Pursuit. *Financial anxiety widespread among university students* (on the Universities Australia Student Finances Survey). https://pursuit.unimelb.edu.au/articles/financial-anxiety-widespread-among-university-students
5. University of Melbourne SAFES. *Food insecurity of university students.* https://safes.unimelb.edu.au/research/food-politics-and-policy/research/food-insecurity-of-university-students
6. Leung, K. M., Charlton, K., McMahon, A., Walton, K., Roy, R., & Kent, K. (2025). A qualitative exploration of food insecurity and institutional support among international students at a regional Australian university. *Health Promotion Journal of Australia, 36*(4), e70080. https://doi.org/10.1002/hpja.70080
7. University of Wollongong (2025). *Many Australian uni students are worried about food.* https://www.uow.edu.au/media/2025/many-australian-uni-students-are-worried-about-food.php
8. Swinburne Student Union. *Services.* https://ssu.org.au/services
9. Swinburne Student Union. *Welfare.* https://ssu.org.au/category/welfare/
10. Western Sydney University. *Food security programs.* https://www.westernsydney.edu.au/home/students/support/food-security-programs
11. Kothamasu, M., Mendez-Mediavilla, F. A., & Perez, E. (2022). Modeling and simulation of food bank disaster relief operations. *Proceedings of the 2022 Winter Simulation Conference.* https://www.informs-sim.org/wsc22papers/160.pdf
12. SimPy documentation. https://simpy.readthedocs.io/en/latest/
13. Swinburne University. *COS60018 Programming Principles and Practices.* https://www.swinburne.edu.au/course/unit/c/cos60018/
14. Swinburne University. *Moondani Toombadool Centre.* https://swinburne.edu.au/indigenous
15. Swinburne University. *Indigenous Student Charter.* https://swinburne.edu.au/life-at-swinburne/student-support-services/indigenous-student-services/indigenous-student-charter
16. Global Indigenous Data Alliance. *CARE Principles.* https://www.gida-global.org/care
17. Maiam nayri Wingara. https://www.maiamnayriwingara.org/
