r"""
run_all.py  --  ONE script that reproduces EVERY number in the slide deck.

Run:  python run_all.py
It prints, with full provenance:
  - the data summary,
  - STEP 1 baseline solve,
  - STEP 2/3 the budget cap and why 75% buffer is infeasible,
  - STEP 4 the new 4-store solve,
  - STEP 5 the side-by-side comparison.

Every figure on the slides is one of these printed numbers -- nothing is
typed in by hand.
"""
from dark_store_optimization import build_and_solve, store_load, lakh
from chandigarh_data import REGIONS, CANDIDATES, CAP_UTIL

LINE = "=" * 70


def show(res, title):
    print(f"\n{title}")
    print("-" * len(title))
    if res["status"] != "Optimal":
        print("  SOLVER STATUS:", res["status"])
        return
    print(f"  stores opened : {res['opened']}  ({len(res['opened'])} of 7)")
    print(f"  fixed cost    : {lakh(res['fixed_cost'])}/month")
    print(f"  delivery cost : {lakh(res['delivery_cost'])}/month")
    print(f"  TOTAL cost    : {lakh(res['total_cost'])}/month")
    print(f"  avg distance  : {res['avg_dist']:.2f} km   (demand-weighted)")
    print(f"  max distance  : {res['max_dist']:.2f} km   (worst-served sector)")
    busiest = max(u for _, (l, u) in store_load(res).items())
    print(f"  busiest store : {busiest:.0f}% of capacity")
    print(f"  utilisation   : " + ", ".join(
        f"{j} {u:.0f}%" for j, (l, u) in store_load(res).items()))


print(LINE)
print("DATA  (real Chandigarh coordinates; haversine distances)")
print(LINE)
tot_d = sum(d for *_, d in REGIONS.values())
print(f"  {len(REGIONS)} sectors, {len(CANDIDATES)} candidate sites")
print(f"  total demand   = {tot_d} ('00s) = {tot_d*100:,} orders/month")
print(f"  total capacity = {sum(c for *_,c,_ in CANDIDATES.values())} ('00s) if all 7 open")

# ---- STEP 1: baseline = problem 'as stated' -------------------------------
print("\n" + LINE)
print("STEP 1  BASELINE  --  the problem 'as stated'")
print("  = all 7 sites AVAILABLE to the optimiser, 75% safety buffer,")
print("    4 km delivery radius, NO budget cap. The model chooses how")
print("    many and which stores. (It is NOT pre-set to any number.)")
print(LINE)
base = build_and_solve()                    # defaults: 75% buffer, no cap
show(base, "Baseline solution")

# ---- STEP 2 & 3: the challenge + why it breaks ----------------------------
print("\n" + LINE)
print("STEP 2/3  MANAGERIAL CHALLENGE: cap the network at 4 stores")
print(LINE)
cut75 = build_and_solve(max_open=4)         # 75% buffer + cap -> infeasible
print(f"\n  Add constraint  SUM_j y_j <= 4  at the 75% buffer:")
print(f"  solver status = {cut75['status']}")
caps = sorted([round(CAP_UTIL * c) for *_, c, _ in CANDIDATES.values()],
              reverse=True)
print(f"  WHY: the 4 largest stores hold only {sum(caps[:4])} units at 75% "
      f"({caps[:4]}),")
print(f"       but total demand is {tot_d}. 4 stores cannot serve the city")
print(f"       *with* a safety buffer  ->  we must drop the buffer to 100%.")

# ---- STEP 4: new solution -------------------------------------------------
print("\n" + LINE)
print("STEP 4  NEW SOLUTION  --  4 stores, buffer relaxed to 100%")
print(LINE)
cut = build_and_solve(cap_util=1.0, max_open=4)
show(cut, "Budget-cut solution")

# ---- STEP 5: comparison table ---------------------------------------------
print("\n" + LINE)
print("STEP 5  COMPARISON")
print(LINE)
rows = [
    ("metric", "baseline (5)", "budget cut (4)"),
    ("stores", f"{len(base['opened'])}", f"{len(cut['opened'])}"),
    ("fixed cost", lakh(base['fixed_cost']), lakh(cut['fixed_cost'])),
    ("delivery cost", lakh(base['delivery_cost']), lakh(cut['delivery_cost'])),
    ("TOTAL cost", lakh(base['total_cost']), lakh(cut['total_cost'])),
    ("avg distance", f"{base['avg_dist']:.2f} km", f"{cut['avg_dist']:.2f} km"),
    ("max distance", f"{base['max_dist']:.2f} km", f"{cut['max_dist']:.2f} km"),
    ("busiest store",
     f"{max(u for _,(l,u) in store_load(base).items()):.0f}%",
     f"{max(u for _,(l,u) in store_load(cut).items()):.0f}%"),
]
for a, b, c in rows:
    print(f"  {a:<16}{b:>16}{c:>18}")
saving = base['total_cost'] - cut['total_cost']
print(f"\n  Saving from the cut: {lakh(saving)}/month "
      f"(~ Rs {saving*12/100:.1f} L / year)")
print("  ...but the busiest store goes from 75% to ~100% -> no safety margin.")
