"""
constants.py - All game constants for Pirate Escape
"""

# Screen
SCREEN_W = 480
SCREEN_H = 700
FPS = 60

# Colors
C_OCEAN_DEEP  = (10,  22,  40)
C_OCEAN_MID   = (13,  36,  68)
C_OCEAN_LIGHT = (26,  74, 122)
C_OCEAN_FOAM  = (74, 158, 202)
C_GOLD        = (240, 192,  64)
C_GOLD_DARK   = (184, 134,  11)
C_RED         = (204,  34,   0)
C_RED_LIGHT   = (255,  68,  34)
C_GREEN       = ( 34, 204, 102)
C_WHITE       = (240, 248, 255)
C_GRAY        = (120, 120, 140)
C_WOOD        = (139,  94,  62)
C_WOOD_DARK   = ( 92,  61,  30)
C_POLICE_BLUE = ( 34,  68, 170)
C_YELLOW      = (255, 255,  68)

# Lanes (5 lanes, X center positions)
LANES      = [56, 152, 248, 344, 424]
LANE_COUNT = len(LANES)

# Player
PLAYER_W             = 48
PLAYER_H             = 74
PLAYER_Y             = 410        # slightly below centre (screen H=700, centre=350)
PLAYER_MOVE_COOLDOWN = 160        # ms between lane changes

# ── Endless speed scaling ──────────────────────────────────
# Target: reach MAX_SPEED_CRASH in ~10 minutes (600 000 ms)
SPEED_START     = 2.2
MAX_SPEED_CRASH = 14.0
# increment per ms so that: START + INCREMENT * 600000 = MAX
SPEED_INCREMENT = (MAX_SPEED_CRASH - SPEED_START) / 600_000   # ≈ 0.0000197

# Crash penalty: lose 15 % of current speed
CRASH_SPEED_PENALTY = 0.15

# Police chase
CHASE_DURATION_MS = 10_000   # 10 seconds
# During chase, 2nd crash within this window = game over
# (the chase itself IS the 10-second window)

# Powerup durations (ms)
PU_SHIELD_DURATION = 6_000
PU_SPEED_DURATION  = 5_000
PU_MAGNET_DURATION = 7_000
PU_DOUBLE_DURATION = 8_000
PU_MAGNET_RADIUS   = 130

# Scoring  — both depend on current speed
# score_per_second  = SCORE_SPEED_FACTOR * speed
# km_per_second     = KM_SPEED_FACTOR    * speed
SCORE_SPEED_FACTOR  = 8.0     # score gained per unit of speed per second
KM_SPEED_FACTOR     = 0.0012  # km gained per unit of speed per second
SCORE_PER_COIN      = 10
SCORE_CRASH_PENALTY = 80
SCORE_SPEED_PICKUP  = 50
KM_MILESTONE        = 1.0     # announce every full km

# Combo
COMBO_THRESHOLD     = 5
COMBO_BONUS_PER_COIN = 5
COMBO_RESET_MS      = 2_000

# Spawn
SPAWN_BASE_MS = 900
SPAWN_MIN_MS  = 280

# Game states
STATE_MENU        = "menu"
STATE_PLAYING     = "playing"
STATE_PAUSED      = "paused"
STATE_GAMEOVER    = "gameover"
STATE_LEADERBOARD = "leaderboard"
STATE_DATA        = "data"
STATE_SETTINGS    = "settings"
STATE_BOAT        = "boat"

# ── Boat catalog ────────────────────────────────────────────
# Each entry: id, name, price, description, color_options (hull, sail),
#             abilities dict, hull_palette, sail_palette
BOAT_CATALOG = [
    {
        "id":    "starter",
        "name":  "Driftwood",
        "price": 0,
        "desc":  "The trusty old boat.\nNo special abilities.",
        "hull_palette": None,   # no customization
        "sail_palette": None,
        "abilities": {},
    },
    {
        "id":    "sloop",
        "name":  "Sea Breeze",
        "price": 300,
        "desc":  "Quick & nimble.\n-20ms lane switch cooldown.\nChoose hull color.",
        "hull_palette": [
            (139, 90,  40),   # Teak wood
            (40,  90, 160),   # Ocean blue
            (160, 40,  40),   # Crimson red
        ],
        "sail_palette": None,
        "abilities": {
            "move_cooldown_bonus": -20,   # ms reduction
        },
    },
    {
        "id":    "galleon",
        "name":  "Iron Tide",
        "price": 1000,
        "desc":  "Armored hull.\nSmaller hitbox. +40 magnet range.\nChoose sail color.",
        "hull_palette": None,
        "sail_palette": [
            (245, 238, 215),  # Classic cream
            (180, 220, 255),  # Sky blue sail
            (255, 210, 80),   # Golden sail
        ],
        "abilities": {
            "hitbox_shrink": 0.80,   # hitbox multiplier (smaller = easier)
            "magnet_bonus":  40,     # extra magnet radius
        },
    },
    {
        "id":    "manowar",
        "name":  "Crimson Storm",
        "price": 2500,
        "desc":  "Legendary warship.\nPassive x1.5 coins. Speed crash\nthreshold +15%. Full color pick.",
        "hull_palette": [
            (139, 90,  40),
            (40,  90, 160),
            (160, 40,  40),
            (40, 120,  60),   # Deep green
        ],
        "sail_palette": [
            (245, 238, 215),
            (180, 220, 255),
            (255, 80,  80),   # Red sail
            (80,  255, 150),  # Jade sail
        ],
        "abilities": {
            "coin_multiplier":    1.5,
            "speed_threshold_bonus": 0.15,  # +15% to MAX_SPEED_CRASH
        },
    },
]

# Quick lookup by id
BOAT_BY_ID = {b["id"]: b for b in BOAT_CATALOG}