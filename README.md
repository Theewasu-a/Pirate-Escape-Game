# Pirate Escape

## Project Description
- **Project by:** Mr.Theewasu
- **Game Genre:** Endless Runner, Arcade

Inspired by the endless runner genre popularized by games like **Subway Surfers**,
Pirate Escape brings the same addictive "dodge and collect" gameplay to a top-down
ocean setting. You captain a pirate boat through 5 ocean lanes, dodging rocks,
collecting gold coins, and outsmarting police patrol boats. The longer you survive,
the faster the sea gets — can you escape the law?

The game also features a built-in data analytics page that records and visualizes your
play session statistics across three interactive graphs.

---

## Installation

Clone this project:
```sh
git clone https://github.com/<username>/pirate-escape.git
cd pirate-escape
```

Create and activate a Python virtual environment:

**Windows:**
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Mac / Linux:**
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Running Guide

After activating the virtual environment, run:

**Windows:**
```bat
python main.py
```

**Mac / Linux:**
```sh
python3 main.py
```

The game window is resizable — drag the corners to scale it up or down.

---

## Tutorial / Usage

| Action | Keys |
|---|---|
| Steer left | `←` Arrow or `A` |
| Steer right | `→` Arrow or `D` |
| Pause / Unpause | `ESC` or click `||` button |

**Menus accessible from the main menu:**
- **SET SAIL** — start a new game
- **BOATS** — visit the boat shop (buy & customize your vessel)
- **LEADERBOARD** — view top 10 high scores
- **DATA** — view session statistics and graphs
- **SETTINGS** — adjust music and SFX volume

---

## Game Features

- **5-lane endless runner** — dodge rocks, collect coins, survive as long as possible
- **Speed scaling** — game gradually accelerates over ~10 minutes, reaching maximum speed
- **Police chase mechanic** — crash once and police boats hunt you; crash again within 10 seconds = game over
- **4 unique boats** with different abilities and color customization:
  - *Driftwood* — free starter boat
  - *Sea Breeze* — faster lane switching (300 coins)
  - *Iron Tide* — smaller hitbox + extended magnet range (1000 coins)
  - *Crimson Storm* — x1.5 coin multiplier + higher speed threshold (2500 coins)
- **Powerups** — Shield, Speed Boost, Coin Magnet, Double Coins
- **Combo system** — chain coin pickups for bonus score
- **Persistent wallet & garage** — coins carry over between sessions; owned boats & color choices are saved
- **Data analytics page** — 3 graphs: time distribution histogram, distance vs coins scatter plot, collision speed boxplot
- **Leaderboard** — top 10 scores saved locally
- **Background music + SFX** with adjustable volume sliders

---

## Known Bugs

- None currently known.

---

## Unfinished Works

- All planned features have been implemented.
- Possible future additions: whirlpool obstacles, name entry on leaderboard, mobile/touch controls.

---

## External Sources

1. Background music: *Pirate1_Theme1.mp3* — by Olivier Bérubé, License: GPL 3.0, from https://opengameart.org
2. **pygame** library — https://www.pygame.org — LGPL 2.1
3. **numpy** library — https://numpy.org — BSD License
