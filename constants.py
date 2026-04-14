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
PLAYER_W             = 44
PLAYER_H             = 68
PLAYER_Y             = 310        # above centre (screen H=700, centre=350)
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
STATE_GAMEOVER    = "gameover"
STATE_LEADERBOARD = "leaderboard"
