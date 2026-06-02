r"""
DATA for the Zepto Chandigarh dark-store project.

Everything the optimisation needs lives here: customer regions (sectors),
candidate dark-store sites, and the operational parameters.

COORDINATES ARE REAL.
  - Latitude/longitude are real Chandigarh sector locations. The central
    sectors (17, 22) use published GPS centroids; the rest are placed on
    Chandigarh's actual sector grid (the city is a planned grid, ~0.7-0.8 km
    per sector step) so all pairwise distances are realistic.
  - Distances d_ij are computed as true great-circle (haversine) distances
    in kilometres -- see haversine() below. Nothing is on an invented grid.

DEMAND / COST NUMBERS ARE FICTITIOUS BUT STRUCTURED (allowed by the brief):
  - P_i  : monthly order volume of a sector, in HUNDREDS of orders.
           (e.g. 42 -> 4,200 orders/month). Total ~63,100 orders/month,
           ~2,100/day -- a realistic scale for a quick-commerce entrant.
  - C_j  : capacity of a candidate store, same units (hundreds of orders/mo).
  - f_j  : fixed cost of operating store j, in THOUSANDS of rupees / month
           (e.g. 240 -> Rs 2.40 lakh/month rent+staff+utilities).

TRANSPORTATION (DELIVERY) COST:
  - DELIVERY_COST_PER_ORDER_KM : Rs per order per km of delivery distance.
    Quick-commerce last-mile (rider pay + fuel) is roughly Rs 8-12 per order
    for a short hop; we use Rs 10/order/km as a documented assumption.
"""
from math import radians, sin, cos, asin, sqrt

# ----------------------------------------------------------------------
# CUSTOMER REGIONS  (set I)
#   id : (name, latitude, longitude, demand P_i in '00s of orders/month)
# ----------------------------------------------------------------------
REGIONS = {
    "S15": ("Sector 15", 30.7585, 76.7680, 42),
    "S22": ("Sector 22", 30.7281, 76.7707, 55),   # real GPS centroid; commercial
    "S17": ("Sector 17", 30.7398, 76.7827, 30),   # real GPS centroid; city centre
    "S35": ("Sector 35", 30.7236, 76.7544, 48),
    "S34": ("Sector 34", 30.7250, 76.7610, 40),
    "S40": ("Sector 40", 30.7180, 76.7520, 52),
    "S43": ("Sector 43", 30.7150, 76.7600, 38),
    "S44": ("Sector 44", 30.7120, 76.7660, 45),
    "S20": ("Sector 20", 30.7350, 76.7720, 33),
    "S11": ("Sector 11", 30.7520, 76.7850, 28),
    "S08": ("Sector 8",  30.7460, 76.7950, 31),
    "S46": ("Sector 46", 30.7080, 76.7680, 36),
    "S38": ("Sector 38", 30.7265, 76.7460, 44),
    "S32": ("Sector 32", 30.7220, 76.7700, 39),
    "S47": ("Sector 47", 30.7050, 76.7620, 41),
    "S27": ("Sector 27", 30.7300, 76.7950, 29),
}

# ----------------------------------------------------------------------
# CANDIDATE FACILITIES  (set J)  -- possible dark-store sites
#   id : (name, latitude, longitude, capacity C_j ['00s/mo], fixed cost f_j ['000 Rs/mo])
# ----------------------------------------------------------------------
CANDIDATES = {
    "W1": ("Industrial Area Ph-1", 30.7080, 76.8050, 180, 240),  # SE industrial belt
    "W2": ("Sector 34 hub",        30.7250, 76.7610, 220, 300),
    "W3": ("Sector 22 hub",        30.7290, 76.7710, 160, 280),
    "W4": ("Sector 45 hub",        30.7110, 76.7640, 200, 260),
    "W5": ("Sector 38 hub",        30.7270, 76.7470, 150, 210),
    "W6": ("Sector 11 hub",        30.7510, 76.7840, 140, 230),
    "W7": ("Sector 47 hub",        30.7050, 76.7610, 170, 220),
}

# ----------------------------------------------------------------------
# Operational parameters
# ----------------------------------------------------------------------
DELIVERY_RADIUS_KM = 4.0   # 10-minute promise: a store serves only sectors
                           # within this great-circle distance
CAP_UTIL = 0.75            # baseline 75% capacity safety buffer (from lecture)
DELIVERY_COST_PER_ORDER_KM = 10.0   # Rs per order per km (last-mile)


def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance between two lat/lon points, in kilometres."""
    R = 6371.0088  # mean Earth radius (km)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (sin(dlat / 2) ** 2
         + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2)
    return 2 * R * asin(sqrt(a))


if __name__ == "__main__":
    tot_d = sum(d for *_, d in REGIONS.values())
    tot_c = sum(c for *_, c, _ in CANDIDATES.values())
    print(f"{len(REGIONS)} regions, {len(CANDIDATES)} candidates")
    print(f"Total demand   : {tot_d} ('00s) = {tot_d*100:,} orders/month")
    print(f"Total capacity : {tot_c} ('00s) if all 7 open")
    # quick distance sanity check
    s17 = REGIONS["S17"]; s47 = REGIONS["S47"]
    print(f"Sample distance S17<->S47: "
          f"{haversine(s17[1], s17[2], s47[1], s47[2]):.2f} km (city is ~6-7 km tall)")
