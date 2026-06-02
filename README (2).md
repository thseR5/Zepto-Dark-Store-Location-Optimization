# Zepto Chandigarh Dark Store Location

**Applied Operations Management – Final Project**
Group 8: Shubham Kumar, Maneesh Baghel, Sanchit Gupta, Chandrakant, Tadi Eswar Reddy
Instructor: Bismark

---

## What this project does

This codebase builds and solves a capacitated facility location problem to find where Zepto should open dark stores in Chandigarh. The model picks which of 7 candidate sites to open and which of 16 sectors each store should serve, so that total monthly cost (fixed rent plus delivery) is minimised while every sector gets delivery within 10 minutes.

The project then introduces a managerial constraint — a budget cap forcing at most 4 stores — and shows exactly what breaks, why, and what the manager gains and gives up.

---

## Files

| File | What it contains |
|---|---|
| `chandigarh_data.py` | All input data: 16 sector locations (real GPS coordinates), 7 candidate sites, demand figures, capacity, fixed costs, and the haversine distance function |
| `dark_store_optimization.py` | The integer programme: builds the PuLP model, solves it, and returns costs, assignments, and store load |
| `run_all.py` | Reproduces every number in the slide deck in one run — baseline, infeasibility demo, budget-cut solve, and comparison table |
| `make_figures.py` | Generates the three PNG maps and the cost-vs-resilience scatter plot used in the deck |

`scenarios.py` (also uploaded) is from a different version of the model that used a lambda-weighted objective and a `dist` helper that do not exist here. It will not run with this codebase and is not part of this project.

---

## The model

**Objective** (in Rs '000 per month):

```
minimise  SUM_j  f_j * y_j
        + (c/10) * SUM_ij  P_i * d_ij * x_ij
```

where `c = Rs 10 per order per km`, `P_i` is sector demand in hundreds of orders, and `d_ij` is the haversine distance in km.

**Constraints:**

1. Each sector is served by exactly one store.
2. A sector can only be assigned to an open store.
3. Demand assigned to store `j` cannot exceed `u * C_j` where `u` is the capacity buffer (0.75 baseline).
4. Sectors more than 4 km from a candidate site cannot be assigned to it (the 10-minute delivery radius).
5. Optionally, the total number of open stores is capped at `max_open`.

**Decision variables:**

- `y_j = 1` if store `j` is opened
- `x_ij = 1` if sector `i` is served by store `j`

---

## Data

Coordinates are real Chandigarh sector GPS locations. Chandigarh is a planned grid city, so sector centroids are placed on the actual grid with roughly 0.7–0.8 km per step. All pairwise distances are true great-circle (haversine) km.

Demand, capacity, and cost figures are structured assumptions documented in `chandigarh_data.py`. Total demand is 63,100 orders per month across 16 sectors; total installed capacity across all 7 sites is 122,000 orders per month.

---

## How to run

Install dependencies:

```bash
pip install pulp matplotlib
```

Reproduce all numbers from the deck:

```bash
python run_all.py
```

Generate figures:

```bash
python make_figures.py
```

Run just the solver:

```bash
python dark_store_optimization.py
```

---

## What the model finds

**Baseline (5 stores, 75% capacity buffer)**

The solver opens W2 (Sector 34 hub), W3 (Sector 22 hub), W4 (Sector 45 hub), W6 (Sector 11 hub), and W7 (Sector 47 hub). Total cost is Rs 18.8 lakh per month. Average delivery distance is 0.93 km; worst-case sector is 2.30 km. Every store runs at 68–75% load, leaving a meaningful safety margin.

**Managerial challenge (4-store cap with 75% buffer)**

Adding the constraint `SUM_j y_j <= 4` with the buffer intact produces an infeasible problem. The 4 largest stores can only absorb 578 units of demand at the 75% threshold, but total demand is 631 units. Fewer stores cannot serve the city at that buffer level.

**Budget-cut solution (4 stores, buffer relaxed to 100%)**

Relaxing the buffer to 1.0 and capping stores at 4 gives a feasible optimal: open W3, W4, W5, W6. Total cost drops to Rs 15.0 lakh per month (down Rs 3.8 lakh, about Rs 45 lakh per year). Average delivery distance actually improves to 0.82 km. Worst-case distance stays at 2.30 km. But store loads climb to 94–100% — no slack at all.

**Comparison**

| Metric | Baseline (5 stores) | Budget cut (4 stores) |
|---|---|---|
| Stores opened | 5 of 7 | 4 of 7 |
| Fixed cost | Rs 12.9 L | Rs 9.8 L |
| Delivery cost | Rs 5.9 L | Rs 5.2 L |
| Total cost / month | Rs 18.8 L | Rs 15.0 L |
| Avg distance | 0.93 km | 0.82 km |
| Worst-case distance | 2.30 km | 2.30 km |
| Busiest store load | 75% | 100% |

The budget cut saves money but removes all capacity headroom. Quick-commerce demand is not smooth — rain, weekends, and festival days can spike it considerably. The recommendation is to launch with 4 stores but treat it as a temporary configuration and phase in the 5th store as revenue grows.

---

## Solver

The model uses [PuLP](https://coin-or.github.io/pulp/) with the bundled CBC solver. Problem size is small (7 binary `y` variables, at most 112 binary `x` variables) so solve time is under a second.

---

## Notes on `scenarios.py`

This file was not used in the project and will not run against the current codebase. It imports `dist` and passes a `lam` argument to `build_and_solve`, neither of which exist in `dark_store_optimization.py`. It also reads `res["objective"]`, a key the solver function does not return. It appears to be a leftover from an earlier model version with a different objective formulation.
