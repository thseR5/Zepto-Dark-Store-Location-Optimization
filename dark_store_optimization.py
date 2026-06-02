r"""
Zepto Chandigarh dark-store location model  (capacitated facility location).

OBJECTIVE = total monthly cost, in Rs '000 / month:

    minimise   SUM_j f_j y_j        (fixed store cost)
             + SUM_ij  t_ij x_ij     (delivery / transportation cost)

  where the per-assignment transport cost is real money:
     t_ij = (P_i * 100 orders) * d_ij km * (Rs c per order-km)  / 1000
          = P_i * d_ij * c / 10          [in Rs '000 / month]
  with c = DELIVERY_COST_PER_ORDER_KM (Rs 10) -> t_ij = P_i * d_ij.

CONSTRAINTS (Lecture 2 notation):
   (1) SUM_j x_ij = 1                  each sector served exactly once
   (2) x_ij <= y_j                     serve only from an open store
   (3) SUM_i P_i x_ij <= u * C_j y_j   capacity (u = buffer, 0.75 baseline)
   (4) x_ij = 0 if d_ij > 4 km         10-minute delivery radius
   (5) SUM_j y_j <= max_open           OPTIONAL budget cap (the challenge)

Distances d_ij are real great-circle (haversine) km from chandigarh_data.py.
"""
import pulp
from chandigarh_data import (
    REGIONS, CANDIDATES, DELIVERY_RADIUS_KM, CAP_UTIL,
    DELIVERY_COST_PER_ORDER_KM, haversine,
)


def build_and_solve(radius=DELIVERY_RADIUS_KM, cap_util=CAP_UTIL,
                    cost_per_order_km=DELIVERY_COST_PER_ORDER_KM,
                    max_open=None):
    I = list(REGIONS)
    J = list(CANDIDATES)

    P = {i: REGIONS[i][3] for i in I}
    C = {j: CANDIDATES[j][3] for j in J}
    f = {j: CANDIDATES[j][4] for j in J}
    # real great-circle distances
    d = {(i, j): haversine(REGIONS[i][1], REGIONS[i][2],
                           CANDIDATES[j][1], CANDIDATES[j][2])
         for i in I for j in J}

    # transport cost coefficient per assignment, in Rs '000/month
    #   = P_i(hundreds)*100 * d_ij * c  / 1000  =  P_i * d_ij * c / 10
    tcoef = cost_per_order_km / 10.0

    allowed = {(i, j) for i in I for j in J if d[(i, j)] <= radius}

    m = pulp.LpProblem("zepto_chandigarh_darkstores", pulp.LpMinimize)
    y = {j: pulp.LpVariable(f"open_{j}", cat="Binary") for j in J}
    x = {(i, j): pulp.LpVariable(f"assign_{i}_{j}", cat="Binary")
         for (i, j) in allowed}

    m += (pulp.lpSum(f[j] * y[j] for j in J)
          + tcoef * pulp.lpSum(P[i] * d[(i, j)] * x[(i, j)] for (i, j) in allowed))

    for i in I:                                   # (1)
        feas = [x[(i, j)] for j in J if (i, j) in allowed]
        if not feas:
            raise ValueError(f"Region {i} has NO candidate within {radius} km")
        m += pulp.lpSum(feas) == 1, f"assign_once_{i}"
    for (i, j) in allowed:                         # (2)
        m += x[(i, j)] <= y[j], f"link_{i}_{j}"
    for j in J:                                    # (3)
        served = [P[i] * x[(i, j)] for i in I if (i, j) in allowed]
        m += pulp.lpSum(served) <= cap_util * C[j] * y[j], f"cap_{j}"
    if max_open is not None:                       # (5)
        m += pulp.lpSum(y[j] for j in J) <= max_open, "budget_max_open"

    m.solve(pulp.PULP_CBC_CMD(msg=False))

    opened = [j for j in J if y[j].value() and y[j].value() > 0.5]
    assign = {i: j for (i, j) in allowed
              if x[(i, j)].value() and x[(i, j)].value() > 0.5}

    status = pulp.LpStatus[m.status]
    if status != "Optimal":
        return {"status": status, "opened": opened, "assign": assign, "d": d,
                "P": P, "C": C, "f": f}

    fixed = sum(f[j] for j in opened)                                  # Rs '000
    delivery = tcoef * sum(P[i] * d[(i, assign[i])] for i in I)        # Rs '000
    avg = sum(P[i] * d[(i, assign[i])] for i in I) / sum(P.values())
    mx = max(d[(i, assign[i])] for i in I)
    return {
        "status": status, "opened": opened, "assign": assign, "d": d,
        "P": P, "C": C, "f": f,
        "fixed_cost": fixed, "delivery_cost": delivery,
        "total_cost": fixed + delivery,
        "avg_dist": avg, "max_dist": mx,
    }


def store_load(res):
    """demand routed to each opened store and its utilisation %."""
    load = {j: 0 for j in res["opened"]}
    for i, j in res["assign"].items():
        load[j] += res["P"][i]
    return {j: (load[j], 100 * load[j] / res["C"][j]) for j in res["opened"]}


def lakh(thousands):
    """Rs '000 -> Rs lakh string."""
    return f"Rs {thousands/100:.2f} L"


if __name__ == "__main__":
    print("BASELINE  (problem as stated: all 7 sites available, 75% buffer)\n")
    r = build_and_solve()
    print("Status        :", r["status"])
    print("Stores opened :", r["opened"], f"({len(r['opened'])} of 7)")
    print("Fixed cost    :", lakh(r["fixed_cost"]), "/month")
    print("Delivery cost :", lakh(r["delivery_cost"]), "/month")
    print("TOTAL cost    :", lakh(r["total_cost"]), "/month")
    print(f"Avg distance  : {r['avg_dist']:.2f} km")
    print(f"Max distance  : {r['max_dist']:.2f} km")
    print("\nStore utilisation:")
    for j, (ld, u) in store_load(r).items():
        print(f"  {j} {CANDIDATES[j][0]:<22} load {ld:>4}  {u:5.1f}%")
