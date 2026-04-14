"""
data_recorder.py - CSV session recording, leaderboard, stats report
"""
import csv, os, json, statistics
from dataclasses import dataclass, fields, astuple

DATA_FILE   = "game_stats.csv"
REPORT_FILE = "stats_report.txt"
LB_FILE     = "leaderboard.json"
LB_MAX      = 10


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
