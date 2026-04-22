"""
data_recorder.py - CSV session recording, leaderboard, stats report
"""
import csv, os, json, statistics
from dataclasses import dataclass, fields, astuple

_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE        = os.path.join(_DIR, "game_stats.csv")
REPORT_FILE      = os.path.join(_DIR, "stats_report.txt")
LB_FILE          = os.path.join(_DIR, "leaderboard.json")
COLLISIONS_FILE  = os.path.join(_DIR, "collision_speeds.csv")
WALLET_FILE      = os.path.join(_DIR, "wallet.json")
GARAGE_FILE      = os.path.join(_DIR, "garage.json")
LB_MAX           = 10


# ── Wallet (persistent coin bank) ──────────────────────────
def load_wallet() -> int:
    if not os.path.isfile(WALLET_FILE):
        return 0
    try:
        with open(WALLET_FILE) as f:
            return int(json.load(f).get("coins", 0))
    except Exception:
        return 0


def save_wallet(coins: int):
    with open(WALLET_FILE, "w") as f:
        json.dump({"coins": max(0, int(coins))}, f)


def add_coins(amount: int):
    save_wallet(load_wallet() + amount)


def spend_coins(amount: int) -> bool:
    """Deduct coins if affordable. Returns True on success."""
    bal = load_wallet()
    if bal < amount:
        return False
    save_wallet(bal - amount)
    return True


# ── Garage (owned boats + selected boat) ──────────────────
_DEFAULT_GARAGE = {
    "owned": ["starter"],
    "selected": "starter",
    "colors": {},   # boat_id -> {"hull": [r,g,b], "sail": [r,g,b]}
}


def load_garage() -> dict:
    if not os.path.isfile(GARAGE_FILE):
        return dict(_DEFAULT_GARAGE)
    try:
        with open(GARAGE_FILE) as f:
            data = json.load(f)
        return {
            "owned":    data.get("owned", ["starter"]),
            "selected": data.get("selected", "starter"),
            "colors":   data.get("colors", {}),
        }
    except Exception:
        return dict(_DEFAULT_GARAGE)


def save_garage(garage: dict):
    with open(GARAGE_FILE, "w") as f:
        json.dump(garage, f, indent=2)


def buy_boat(boat_id: str, price: int) -> bool:
    garage = load_garage()
    if boat_id in garage["owned"]:
        return True   # already owned
    if not spend_coins(price):
        return False
    garage["owned"].append(boat_id)
    save_garage(garage)
    return True


def select_boat(boat_id: str):
    garage = load_garage()
    if boat_id in garage["owned"]:
        garage["selected"] = boat_id
        save_garage(garage)


def save_boat_colors(boat_id: str, hull: tuple, sail: tuple):
    garage = load_garage()
    garage["colors"][boat_id] = {
        "hull": list(hull),
        "sail": list(sail),
    }
    save_garage(garage)


def load_boat_colors(boat_id: str) -> dict:
    garage = load_garage()
    return garage["colors"].get(boat_id, {})


def save_collision_speed(speed: float):
    """Record a single collision's boat speed for analysis (Graph 3)."""
    exists = os.path.isfile(COLLISIONS_FILE)
    with open(COLLISIONS_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if not exists: w.writerow(["speed"])
        w.writerow([round(float(speed), 3)])


def load_collision_speeds():
    if not os.path.isfile(COLLISIONS_FILE): return []
    out = []
    with open(COLLISIONS_FILE, newline="") as f:
        for row in csv.DictReader(f):
            try: out.append(float(row["speed"]))
            except (KeyError, ValueError): continue
    return out


@dataclass
class SessionData:
    score:           int
    time_played:     int    # seconds
    distance:        float  # km
    coins_collected: int
    collisions:      int
    level_reached:   int    # kept for CSV compat (always 1 in endless)


def _fieldnames():
    return [f.name for f in fields(SessionData)]


def save_session(s: SessionData):
    exists = os.path.isfile(DATA_FILE)
    with open(DATA_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if not exists: w.writerow(_fieldnames())
        w.writerow(astuple(s))


def load_sessions():
    if not os.path.isfile(DATA_FILE): return []
    out = []
    with open(DATA_FILE, newline="") as f:
        for row in csv.DictReader(f):
            try:
                out.append(SessionData(
                    score           = int(row["score"]),
                    time_played     = int(row["time_played"]),
                    distance        = float(row["distance"]),
                    coins_collected = int(row["coins_collected"]),
                    collisions      = int(row["collisions"]),
                    level_reached   = int(row["level_reached"]),
                ))
            except (KeyError, ValueError):
                continue
    return out


def generate_report() -> str:
    sessions = load_sessions()
    if not sessions: return "No session data yet."
    lines = ["="*44, "     PIRATE ESCAPE - STATS REPORT", "="*44,
             f"  Sessions: {len(sessions)}", ""]
    metrics = {
        "Score":      [s.score           for s in sessions],
        "Time(s)":    [s.time_played      for s in sessions],
        "Dist(km)":   [s.distance         for s in sessions],
        "Coins":      [s.coins_collected  for s in sessions],
        "Crashes":    [s.collisions       for s in sessions],
    }
    lines.append(f"  {'Metric':<10} {'Mean':>8} {'Min':>8} {'Max':>8} {'SD':>8}")
    lines.append("  "+"-"*40)
    for name, vals in metrics.items():
        mn  = min(vals); mx = max(vals)
        avg = statistics.mean(vals)
        sd  = statistics.stdev(vals) if len(vals) > 1 else 0.0
        lines.append(f"  {name:<10} {avg:>8.1f} {mn:>8} {mx:>8} {sd:>8.1f}")
    lines += ["", "="*44]
    report = "\n".join(lines)
    with open(REPORT_FILE, "w") as f: f.write(report)
    return report


# ── Leaderboard ─────────────────────────────────────────────
@dataclass
class LeaderboardEntry:
    score:    int
    coins:    int
    level:    int
    distance: float  # km
    time:     int


def load_leaderboard():
    if not os.path.isfile(LB_FILE): return []
    try:
        with open(LB_FILE) as f: data = json.load(f)
        return [LeaderboardEntry(
            score    = int(e["score"]),
            coins    = int(e["coins"]),
            level    = int(e["level"]),
            distance = float(e["distance"]),
            time     = int(e["time"]),
        ) for e in data]
    except Exception: return []


def save_leaderboard(entries):
    with open(LB_FILE, "w") as f:
        json.dump([e.__dict__ for e in entries], f, indent=2)


def add_to_leaderboard(entry: LeaderboardEntry) -> bool:
    entries = load_leaderboard()
    entries.append(entry)
    entries.sort(key=lambda e: e.score, reverse=True)
    entries = entries[:LB_MAX]
    save_leaderboard(entries)
    return entries[0].score == entry.score
