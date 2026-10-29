#!/usr/bin/env python3
"""Pick the CSV to summarize: the one given, or a random one made to fit the title.

Usage: prepare.py <given.csv or ""> <title> <rows> <out.csv> [seed]

With a CSV given, it is used as is. With none, the title picks a theme (orders,
weather, web traffic, staff, golf rounds, inventory, or a general one) and
<rows> random rows are written to <out.csv>. The same seed gives the same file.
Output (flow): {"file": <csv>, "generated": true/false, "theme": <name>, "rows": <n>}
Standard library only.
"""
import csv
import random
import sys
from datetime import date, timedelta

from flow import flow

given, title, rows_text, out = sys.argv[1:5]
seed = sys.argv[5] if len(sys.argv) > 5 else ""

if given.strip():
    print(f"using {given}")
    flow.set_output({"file": given, "generated": False, "theme": "", "rows": None})
    sys.exit(0)

rng = random.Random(seed or None)
try:
    rows = max(1, min(10_000, int(float(rows_text or 50))))
except ValueError:
    sys.exit(f"rows must be a number, got {rows_text!r}")

start = date.today() - timedelta(days=90)


def day():
    return (start + timedelta(days=rng.randrange(90))).isoformat()


def money(low, high):
    return f"{rng.uniform(low, high):.2f}"


STATES = ["CA", "TX", "FL", "NY", "AZ", "CO", "WA", "IL", "GA", "NC", "OR"]
# Each product sells within its own price range, so prices read as real.
PRODUCTS = {
    "Apparel": {"Tour Polo - Navy": (58, 72), "Quarter Zip - Grey": (78, 96), "Rain Jacket": (120, 160)},
    "Headwear": {"Rope Hat": (32, 40), "Bucket Hat": (28, 36), "Visor": (22, 28)},
    "Balls": {"Pro Distance Balls (12)": (44, 52), "Soft Feel Balls (12)": (30, 38)},
    "Accessories": {"Divot Tool": (12, 18), "Ball Marker Set": (9, 15), "Towel": (18, 26)},
    "Bags": {"Stand Bag": (179, 229), "Cart Bag": (219, 279)},
}


def orders():
    cat = rng.choice(list(PRODUCTS))
    product, (low, high) = rng.choice(list(PRODUCTS[cat].items()))
    return {"date": day(), "product": product, "category": cat,
            "quantity": rng.choices([1, 2, 3, 4, 6], [50, 25, 12, 8, 5])[0], "price": money(low, high), "state": rng.choice(STATES)}


def weather():
    temp = rng.gauss(72, 14)
    return {"date": day(), "city": rng.choice(["Phoenix", "Denver", "Seattle", "Austin", "Miami", "Chicago"]),
            "temp_high_f": round(temp + rng.uniform(4, 12)), "temp_low_f": round(temp - rng.uniform(6, 18)),
            "rain_in": f"{max(0, rng.gauss(0.1, 0.25)):.2f}", "wind_mph": round(abs(rng.gauss(9, 5))),
            "conditions": rng.choice(["Sunny", "Cloudy", "Rain", "Windy", "Partly cloudy"])}


def traffic():
    visits = round(abs(rng.gauss(1200, 600)))
    return {"date": day(), "page": rng.choice(["/", "/shop", "/products/rope-hat", "/about", "/contact", "/cart"]),
            "source": rng.choice(["google", "instagram", "direct", "email", "tiktok"]), "visits": visits,
            "bounce_rate": f"{rng.uniform(0.2, 0.75):.2f}", "conversions": round(visits * rng.uniform(0.005, 0.04))}


def staff():
    first = rng.choice(["Ava", "Liam", "Maya", "Noah", "Zoe", "Eli", "Ivy", "Leo", "Nina", "Owen"])
    last = rng.choice(["Kim", "Patel", "Garcia", "Nguyen", "Smith", "Okafor", "Rossi", "Chen"])
    dept = rng.choice(["Design", "Engineering", "Sales", "Support", "Operations"])
    return {"name": f"{first} {last}", "department": dept, "salary": round(rng.gauss(88_000, 22_000), -2),
            "start_date": (date.today() - timedelta(days=rng.randrange(60, 3000))).isoformat(),
            "remote": rng.choice(["yes", "no", "hybrid"]), "rating": rng.choice([3, 3, 4, 4, 4, 5])}


def golf():
    par = 72
    score = round(rng.gauss(86, 8))
    return {"date": day(), "course": rng.choice(["Pebble Creek", "Pine Valley", "Torrey Pines", "Lakeside", "Desert Ridge"]),
            "player": rng.choice(["Ethan", "Sam", "Jordan", "Riley", "Casey", "Morgan"]), "score": score,
            "to_par": score - par, "putts": round(rng.gauss(33, 3)), "fairways_hit": rng.randrange(3, 14)}


def inventory():
    cat = rng.choice(list(PRODUCTS))
    product, (low, high) = rng.choice(list(PRODUCTS[cat].items()))
    on_hand = rng.randrange(0, 240)
    return {"sku": f"SR-{rng.randrange(1000, 9999)}", "product": product, "category": cat,
            "warehouse": rng.choice(["Austin", "Reno", "Columbus"]), "on_hand": on_hand,
            "reorder_point": rng.choice([10, 20, 30, 50]), "unit_cost": money(low * 0.35, high * 0.45)}


def general(words):
    labels = [w for w in words if len(w) > 3][:5] or ["alpha", "beta", "gamma", "delta"]
    return {"id": rng.randrange(10_000, 99_999), "date": day(), "category": rng.choice(labels).lower(),
            "region": rng.choice(["North", "South", "East", "West"]), "value": round(abs(rng.gauss(100, 40)), 1),
            "amount": money(5, 500), "status": rng.choice(["open", "closed", "pending"])}


THEMES = [
    ("orders", orders, ["order", "sale", "sales", "shop", "store", "revenue", "purchase", "customer", "ecommerce"]),
    ("weather", weather, ["weather", "temperature", "rain", "climate", "forecast"]),
    ("web traffic", traffic, ["traffic", "visit", "visits", "web", "site", "page", "analytics", "seo", "marketing"]),
    ("staff", staff, ["staff", "employee", "employees", "team", "hr", "payroll", "people", "salary", "hiring"]),
    ("golf rounds", golf, ["golf", "round", "rounds", "score", "scores", "course", "handicap"]),
    ("inventory", inventory, ["inventory", "stock", "warehouse", "sku", "supply", "reorder"]),
]

words = [w.strip(".,:;!?()").lower() for w in title.split()]
theme, make = "general", None
for name, fn, keys in THEMES:
    if any(w.rstrip("s") in [k.rstrip("s") for k in keys] for w in words):
        theme, make = name, fn
        break

data = [make() if make else general(title.split()) for _ in range(rows)]
data.sort(key=lambda r: r.get("date", ""))

with open(out, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
    writer.writeheader()
    writer.writerows(data)

print(f"generated {rows} rows of {theme} data for {title!r} -> {out}")
flow.set_output({"file": out, "generated": True, "theme": theme, "rows": rows})
