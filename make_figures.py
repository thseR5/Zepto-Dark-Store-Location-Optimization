r"""Figures for the deck, built from REAL lat/long (projected to a local km
grid so the map has correct proportions).
   fig_baseline_map.png  - Step 1 baseline (5 stores)
   fig_budget_map.png    - Step 4 new solution (4 stores)
   fig_ladder.png        - cost vs resilience for the recommendation
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from math import cos, radians

from dark_store_optimization import build_and_solve, store_load
from chandigarh_data import REGIONS, CANDIDATES

INK="#1A1535"; VIOLET="#7C3AED"; MUTED="#9aa0b4"; DEMAND="#2563EB"
LINE="#c4b5fd"; GOOD="#059669"; BAD="#DC2626"; AMBER="#D97706"

# local equirectangular projection (km) centred on the data
LAT0 = sum(v[1] for v in REGIONS.values()) / len(REGIONS)
LON0 = sum(v[2] for v in REGIONS.values()) / len(REGIONS)
def xy(lat, lon):
    x = (lon - LON0) * 111.320 * cos(radians(LAT0))
    y = (lat - LAT0) * 110.574
    return x, y


def draw_map(res, fname, title, store_color=VIOLET):
    loads = store_load(res)
    fig, ax = plt.subplots(figsize=(8.0, 7.0))
    for i, j in res["assign"].items():
        rx, ry = xy(REGIONS[i][1], REGIONS[i][2])
        jx, jy = xy(CANDIDATES[j][1], CANDIDATES[j][2])
        ax.plot([rx, jx], [ry, jy], color=LINE, lw=1.2, zorder=1)
    for i, (name, lat, lon, dem) in REGIONS.items():
        x, y = xy(lat, lon)
        ax.scatter(x, y, s=dem*4.5, color=DEMAND, alpha=0.55,
                   edgecolors="white", linewidths=0.8, zorder=2)
        ax.text(x, y-0.18, name.replace("Sector ", "S"), ha="center", va="top",
                fontsize=7, color=INK)
    for j, (name, lat, lon, cap, fc) in CANDIDATES.items():
        x, y = xy(lat, lon)
        if j in res["opened"]:
            ld, util = loads[j]
            col = BAD if util >= 93 else (AMBER if util >= 80 else store_color)
            ax.scatter(x, y, s=380, marker="*", color=col,
                       edgecolors="white", linewidths=1.3, zorder=4)
            ax.text(x, y+0.22, f"{name}\n{util:.0f}% full", ha="center",
                    va="bottom", fontsize=7.5, color=col, fontweight="bold")
        else:
            ax.scatter(x, y, s=120, marker="X", color=MUTED,
                       edgecolors="white", linewidths=1.0, zorder=3)
            ax.text(x, y+0.18, f"{name}\n(not opened)", ha="center", va="bottom",
                    fontsize=6.5, color=MUTED)
    ax.set_title(title, fontsize=11.5, color=INK, fontweight="bold")
    ax.set_xlabel("km (east-west)"); ax.set_ylabel("km (north-south)")
    ax.set_aspect("equal"); ax.grid(alpha=0.15)
    legend = [
        Line2D([0],[0],marker="*",color="w",markerfacecolor=store_color,markersize=15,label="Open store (healthy load)"),
        Line2D([0],[0],marker="*",color="w",markerfacecolor=BAD,markersize=15,label="Open store (>=93% load)"),
        Line2D([0],[0],marker="X",color="w",markerfacecolor=MUTED,markersize=10,label="Candidate (not opened)"),
        Line2D([0],[0],marker="o",color="w",markerfacecolor=DEMAND,markersize=10,alpha=0.6,label="Sector (size = demand)"),
    ]
    ax.legend(handles=legend, loc="upper right", fontsize=7.5, framealpha=0.92)
    fig.tight_layout(); fig.savefig(fname, dpi=170); plt.close(fig)
    print("wrote", fname)


def fig_ladder():
    base = build_and_solve()                       # 5 stores, 75%
    bud  = build_and_solve(cap_util=1.0, max_open=4)
    pts = [("4 stores\n(budget cut)", bud, BAD),
           ("5 stores\n(baseline)", base, GOOD)]
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    for label, res, col in pts:
        cost = res["total_cost"]/100.0   # lakh
        maxutil = max(u for _,(l,u) in store_load(res).items())
        ax.scatter(cost, maxutil, s=520, color=col, zorder=3,
                   edgecolors="white", linewidths=2)
        ax.annotate(label, (cost, maxutil), textcoords="offset points",
                    xytext=(0, 18 if col==GOOD else -34), ha="center",
                    fontsize=11, fontweight="bold", color=col)
    ax.axhspan(93, 102, color="#fee2e2", alpha=0.7)
    ax.text(18.6, 98, "fragile zone (>=93% load)", color=BAD, fontsize=9,
            va="center", ha="right")
    ax.set_xlabel("Total monthly cost  (Rs lakh / month)", fontsize=11)
    ax.set_ylabel("Busiest store's load  (%)", fontsize=11)
    ax.set_title("Cheaper network, but no safety margin", fontsize=12.5,
                 color=INK, fontweight="bold")
    ax.set_xlim(13.5, 20.5); ax.set_ylim(60, 104); ax.grid(alpha=0.2)
    fig.tight_layout(); fig.savefig("fig_ladder.png", dpi=170); plt.close(fig)
    print("wrote fig_ladder.png")


if __name__ == "__main__":
    base = build_and_solve()
    draw_map(base, "fig_baseline_map.png",
             "STEP 1 - Baseline: 5 stores, 75% capacity buffer\n"
             "avg 0.93 km - max 2.30 km - every sector within 4 km", VIOLET)
    bud = build_and_solve(cap_util=1.0, max_open=4)
    draw_map(bud, "fig_budget_map.png",
             "STEP 4 - Budget cut: 4 stores, run at full load\n"
             "avg 0.82 km - max 2.30 km - stores at 94-100% capacity", VIOLET)
    fig_ladder()
