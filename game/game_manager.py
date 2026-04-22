"""
game_manager.py - GameManager
Controls main game logic, state machine, spawning, collision, scoring.

Changes from previous version:
  1. Speed rises slowly — takes ~10 minutes to reach MAX_SPEED_CRASH
  2. Player boat sits above centre (PLAYER_Y in constants)
  3. Police drive into bottom row and STAY there (don't chase/catch)
     — 2nd crash within 10-second chase window = game over
  4. Crash penalty: speed -15 %
  5. Score and distance both scale with current speed
"""

import pygame
import random
import math
import array
import struct

from .constants import (
    SCREEN_W, SCREEN_H, LANES, LANE_COUNT,
    SPEED_START, SPEED_INCREMENT, MAX_SPEED_CRASH, CRASH_SPEED_PENALTY,
    CHASE_DURATION_MS,
    SCORE_SPEED_FACTOR, KM_SPEED_FACTOR, SCORE_PER_COIN,
    SCORE_CRASH_PENALTY, SCORE_SPEED_PICKUP,
    COMBO_THRESHOLD, COMBO_BONUS_PER_COIN, COMBO_RESET_MS,
    PU_MAGNET_RADIUS, KM_MILESTONE,
    STATE_MENU, STATE_PLAYING, STATE_PAUSED, STATE_GAMEOVER,
    STATE_LEADERBOARD, STATE_DATA, STATE_SETTINGS, STATE_BOAT,
    C_GOLD, C_RED_LIGHT, C_GREEN, C_OCEAN_FOAM, C_OCEAN_DEEP,
    BOAT_CATALOG, BOAT_BY_ID,
)
from .player_boat  import PlayerBoat
from .objects      import Obstacle, Coin, Powerup, PoliceBoat, PirateShip, GiantFish
from .particles    import ParticleSystem
from data.data_recorder import (
    SessionData, save_session,
    LeaderboardEntry, add_to_leaderboard, load_leaderboard,
    generate_report, load_sessions,
    save_collision_speed, load_collision_speeds,
    load_wallet, add_coins,
    load_garage, select_boat, buy_boat, save_boat_colors, load_boat_colors,
)
from .sounds import SoundBank
from . import ui


def _generate_theme_music():
    """
    Generate a procedural pirate-style theme using pygame mixer.
    Uses only synthesized audio — no copyrighted material.
    Returns a pygame.mixer.Sound object.
    """
    sample_rate = 22050
    duration_s  = 8.0      # loop length
    n_samples   = int(sample_rate * duration_s)

    # Note frequencies (Hz)
    notes = {
        'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
        'G4': 392.00, 'A4': 440.00, 'Bb4': 466.16, 'B4': 493.88,
        'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46,
        'G5': 783.99, 'A5': 880.00,
        'G3': 196.00, 'A3': 220.00, 'C3': 130.81, 'D3': 146.83,
        'F3': 174.61, 'E3': 164.81,
    }

    # Shanty-style melody (note, beat_start, beat_duration)
    # Each beat = 0.25s at tempo ~120 bpm (0.5s per beat, using 16th notes)
    beat = 60.0 / 120.0 / 2   # 0.25s per 8th note
    melody = [
        ('G4',0,2),('G4',2,1),('G4',3,1),('C5',4,4),
        ('D5',8,2),('C5',10,1),('D5',11,1),('E5',12,4),
        ('G5',16,2),('E5',18,1),('D5',19,1),('C5',20,4),
        ('G4',24,2),('A4',26,2),('G4',28,4),
        ('F5',32,2),('F5',34,1),('E5',35,1),('D5',36,2),('C5',38,2),
        ('E5',40,2),('D5',42,1),('C5',43,1),('B4',44,4),
        ('G4',48,2),('A4',50,2),('G4',52,2),('D4',54,2),
        ('G4',56,4),('G4',60,4),
    ]
    # Bass line
    bass = [
        ('C3',0,4),('F3',4,4),('G3',8,4),('C3',12,4),
        ('A3',16,4),('D3',20,4),('G3',24,4),('C3',28,4),
        ('F3',32,4),('Bb4',36,4),('C3',40,4),('G3',44,4),
        ('C3',48,4),('F3',52,4),('G3',56,4),('C3',60,4),
    ]

    buf = [0.0] * n_samples

    def add_tone(freq, start_beat, dur_beats, amp=0.3, waveform='saw'):
        t0 = int(start_beat * beat * sample_rate)
        t1 = int((start_beat + dur_beats) * beat * sample_rate)
        t1 = min(t1, n_samples)
        length = t1 - t0
        for i in range(length):
            t = i / sample_rate
            env = min(1.0, i / (sample_rate * 0.02))  # attack
            env *= min(1.0, (length - i) / (sample_rate * 0.05))  # release
            phase = freq * t
            if waveform == 'saw':
                v = 2 * (phase % 1.0) - 1
            elif waveform == 'square':
                v = 1.0 if (phase % 1.0) < 0.5 else -1.0
            else:
                v = math.sin(2 * math.pi * phase)
            buf[t0 + i] += amp * env * v

    for (note, sb, db) in melody:
        add_tone(notes[note], sb, db, amp=0.25, waveform='saw')
    for (note, sb, db) in bass:
        add_tone(notes[note], sb, db, amp=0.18, waveform='square')

    # Percussion: kick on beat 1 & 3 per measure (every 8 8th-notes)
    for measure in range(4):
        for kick_beat in [0, 4]:
            b = measure * 16 + kick_beat
            t0 = int(b * beat * sample_rate)
            for i in range(min(int(0.15 * sample_rate), n_samples - t0)):
                decay = math.exp(-i / (sample_rate * 0.04))
                freq_drop = 80 * math.exp(-i / (sample_rate * 0.05))
                buf[t0 + i] += 0.35 * decay * math.sin(2 * math.pi * freq_drop * i / sample_rate)

    # Normalize and convert to 16-bit stereo
    peak = max(abs(v) for v in buf) or 1.0
    raw = array.array('h', [
        int(max(-32767, min(32767, v / peak * 28000)))
        for v in buf
    ])
    # Duplicate mono → stereo
    stereo = array.array('h')
    for s in raw:
        stereo.append(s)
        stereo.append(s)

    sound = pygame.sndarray.make_sound(
        __import__('numpy').array(stereo, dtype='int16').reshape(-1, 2)
    )
    return sound


class GameManager:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.state  = STATE_MENU
        self.tick   = 0
        self.wave_offset = 0.0

        self.player      = PlayerBoat()
        self.obstacles:  list = []
        self.coins:      list = []
        self.powerups:   list = []
        self.police_boats: list = []
        self.pirate_ships: list = []
        self.giant_fish:   list = []
        self.particles   = ParticleSystem()

        # Difficulty state
        self._difficulty      = 0
        self._pirate_ship_cd  = 35_000
        self._giant_fish_cd   = 45_000

        # Session stats
        self.score       = 0.0
        self.coins_count = 0
        self.distance_km = 0.0
        self.collisions  = 0
        self.session_start_ms = 0
        self.speed       = SPEED_START
        self.next_km_milestone = KM_MILESTONE

        # Chase state
        # chasing=True means player already hit once; police are on screen.
        # A 2nd crash while chasing=True → game over.
        self.chasing    = False
        self.chase_timer= 0

        # Combo
        self.coin_combo     = 0
        self.combo_timer_ms = 0

        # Spawn
        self.spawn_timer = 0

        # Announcement
        self.announce_text  = ""
        self.announce_alpha = 0
        self.announce_timer = 0

        # End-screen data
        self.end_stats    = {}
        self.is_highscore = False

        # Volume settings (0.0 – 1.0)
        self.music_vol = 0.5
        self.sfx_vol   = 0.7
        # Where we came from when entering settings
        self._settings_source = STATE_MENU
        # Slider drag state
        self._drag_slider = None   # "music" | "sfx" | None

        # Boat shop state
        self._shop_idx = 0          # currently previewed catalog index
        self._shop_color_pick = {"hull_idx": 0, "sail_idx": 0}
        self._shop_source = STATE_MENU

        # Data page tab (0=histogram, 1=scatter, 2=boxplot)
        self._data_tab = 0

        self._build_buttons()

        # ── Music + SFX ──────────────────────────────────────────
        self._music_channel = None
        self.sfx = SoundBank()
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        except Exception:
            pass

        # Load MP3 music via pygame.mixer.music
        self._music_loaded = False
        import os
        _mp3_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "Pirate1_Theme1.mp3")
        try:
            pygame.mixer.music.load(_mp3_path)
            pygame.mixer.music.set_volume(self.music_vol)
            self._music_loaded = True
        except Exception:
            self._music_loaded = False

        # Logical mouse position (may be remapped for resizable window)
        self.mouse_pos = (0, 0)

    def _play_music(self):
        if self._music_loaded:
            try:
                pygame.mixer.music.play(loops=-1)
            except Exception:
                pass
        self.sfx.start_ambient()

    def _stop_music(self):
        if self._music_loaded:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self.sfx.stop_ambient()

    def _pause_music(self):
        if self._music_loaded:
            try:
                pygame.mixer.music.pause()
            except Exception:
                pass

    def _resume_music(self):
        if self._music_loaded:
            try:
                pygame.mixer.music.unpause()
            except Exception:
                pass

    def _apply_volumes(self):
        """Push current volume settings to all audio channels."""
        if self._music_loaded:
            try:
                pygame.mixer.music.set_volume(self.music_vol)
            except Exception:
                pass
        if self.sfx.enabled:
            self.sfx.coin.set_volume(0.35 * self.sfx_vol)
            self.sfx.crash.set_volume(0.6 * self.sfx_vol)
            self.sfx.shield_break.set_volume(0.55 * self.sfx_vol)
            self.sfx.powerup.set_volume(0.45 * self.sfx_vol)
            self.sfx.police.set_volume(0.5 * self.sfx_vol)
            self.sfx.wave.set_volume(0.25 * self.sfx_vol)

    # ── Buttons ──────────────────────────────────────────────
    def _build_buttons(self):
        bw, bh = 200, 38
        cx = SCREEN_W//2 - bw//2
        self.menu_buttons = {
            "SET  SAIL":   pygame.Rect(cx, 270, bw, bh),
            "BOATS":       pygame.Rect(cx, 316, bw, bh),
            "LEADERBOARD": pygame.Rect(cx, 362, bw, bh),
            "DATA":        pygame.Rect(cx, 408, bw, bh),
            "SETTINGS":    pygame.Rect(cx, 454, bw, bh),
        }
        self.over_buttons = {
            "PLAY AGAIN":  pygame.Rect(cx, 360, bw, bh),
            "LEADERBOARD": pygame.Rect(cx, 408, bw, bh),
            "MAIN MENU":   pygame.Rect(cx, 456, bw, bh),
        }
        self.lb_buttons = {
            "BACK": pygame.Rect(cx, SCREEN_H - 90, bw, bh),
        }
        self.data_buttons = {
            "BACK": pygame.Rect(cx, SCREEN_H - 90, bw, bh),
        }
        # Pause overlay buttons
        self.pause_buttons = {
            "RESUME":   pygame.Rect(cx, 290, bw, bh),
            "SETTINGS": pygame.Rect(cx, 338, bw, bh),
            "MAIN MENU":pygame.Rect(cx, 386, bw, bh),
        }
        # HUD pause button (top-right corner)
        self.pause_btn_rect = pygame.Rect(SCREEN_W - 44, 8, 36, 36)
        # Settings sliders
        sw, sh_ = 200, 12
        sx = SCREEN_W//2 - sw//2
        self.settings_sliders = {
            "music": pygame.Rect(sx, 195, sw, sh_),
            "sfx":   pygame.Rect(sx, 295, sw, sh_),
        }
        self.settings_buttons = {
            "BACK": pygame.Rect(cx, SCREEN_H - 90, bw, bh),
        }
        # Boat shop buttons  (dots drawn at btn_area_top+14 = SCREEN_H-126)
        self.shop_buttons = {
            "<":    pygame.Rect(14,          SCREEN_H - 112, 44, 44),
            ">":    pygame.Rect(SCREEN_W-58, SCREEN_H - 112, 44, 44),
            "ACT":  pygame.Rect(cx,          SCREEN_H - 112, bw, bh),
            "BACK": pygame.Rect(cx,          SCREEN_H - 60,  bw, bh),
        }
        # Color swatch click rects (built dynamically in handle_event)
        self._shop_color_rects = {}   # "hull_0" -> Rect, etc.

    # ── State transitions ────────────────────────────────────
    def _start_game(self):
        self.state = STATE_PLAYING
        # Load selected boat + colors
        garage = load_garage()
        bid    = garage.get("selected", "starter")
        colors = garage.get("colors", {}).get(bid, {})
        hull_c = tuple(colors["hull"]) if "hull" in colors else None
        sail_c = tuple(colors["sail"]) if "sail" in colors else None
        self.player = PlayerBoat(boat_id=bid, hull_color=hull_c, sail_color=sail_c)

        # Apply Man-o-War speed threshold bonus
        self._speed_threshold_bonus = self.player.speed_threshold_bonus
        self.obstacles.clear()
        self.coins.clear()
        self.powerups.clear()
        self.police_boats.clear()
        self.pirate_ships.clear()
        self.giant_fish.clear()
        self.particles.clear()

        self._difficulty     = 0
        self._pirate_ship_cd = 35_000
        self._giant_fish_cd  = 45_000

        self.score              = 0.0
        self.coins_count        = 0
        self.distance_km        = 0.0
        self.collisions         = 0
        self.session_start_ms   = pygame.time.get_ticks()
        self.speed              = SPEED_START
        self.next_km_milestone  = KM_MILESTONE
        self.chasing            = False
        self.chase_timer        = 0
        self.coin_combo         = 0
        self.combo_timer_ms     = 0
        self.spawn_timer        = 0

        self._show_announce("SET  SAIL!")
        self._play_music()

    def _end_game(self, reason: str):
        self._stop_music()
        self.state = STATE_GAMEOVER
        elapsed_s  = (pygame.time.get_ticks() - self.session_start_ms) // 1000

        # Add coins to persistent wallet
        add_coins(self.coins_count)

        save_session(SessionData(
            score           = int(self.score),
            time_played     = elapsed_s,
            distance        = round(self.distance_km, 3),
            coins_collected = self.coins_count,
            collisions      = self.collisions,
            level_reached   = 1,
        ))

        lb_entry = LeaderboardEntry(
            score    = int(self.score),
            coins    = self.coins_count,
            level    = 1,
            distance = round(self.distance_km, 3),
            time     = elapsed_s,
        )
        self.is_highscore = add_to_leaderboard(lb_entry)

        self.end_stats = {
            "score":       self.score,
            "coins":       self.coins_count,
            "distance_km": round(self.distance_km, 2),
            "collisions":  self.collisions,
            "time":        elapsed_s,
            "reason":      reason,
            "wallet":      load_wallet(),
        }

        for _ in range(3):
            self.particles.explosion(
                self.player.x + random.uniform(-30, 30),
                self.player.y + random.uniform(-20, 20),
                color=C_RED_LIGHT, count=20
            )

    # ── Spawning ─────────────────────────────────────────────
    def _lane_clear(self, lane: int, y_check: float = -60.0,
                    margin: float = 80.0) -> bool:
        """Return True if nothing is within `margin` px of y_check in that lane."""
        for obs in self.obstacles:
            if obs.lane == lane and abs(obs.y - y_check) < margin:
                return False
        for coin in self.coins:
            if coin.lane == lane and abs(coin.y - y_check) < margin:
                return False
        for pu in self.powerups:
            if pu.lane == lane and abs(pu.y - y_check) < margin:
                return False
        return True

    def _free_lane(self, exclude: int = -1) -> int:
        """Pick a random lane that is currently clear at spawn y; fallback random."""
        lanes = list(range(LANE_COUNT))
        random.shuffle(lanes)
        for lane in lanes:
            if lane != exclude and self._lane_clear(lane):
                return lane
        return random.randint(0, LANE_COUNT - 1)   # fallback

    def _spawn_objects(self):
        rock_bias     = min(0.62, 0.42 + self._difficulty * 0.03)
        double_thresh = max(0.20, 0.35 - self._difficulty * 0.03)
        t1 = rock_bias
        t2 = t1 + 0.18   # single coin
        t3 = t2 + 0.22   # coin row
        t4 = t3 + 0.10   # powerup
        # else: mixed obstacle+coin row
        r = random.random()
        if r < t1:
            self._spawn_obstacle()
            if self.speed > 6.0 and random.random() < double_thresh:
                self._spawn_obstacle()
        elif r < t2:
            self._spawn_coin()
        elif r < t3:
            self._spawn_coin_row()
        elif r < t4:
            self._spawn_powerup()
        else:
            lane = self._free_lane()
            self.obstacles.append(Obstacle(lane))
            coin_lane = self._free_lane(exclude=lane)
            count = random.randint(4, 7)
            for i in range(count):
                self.coins.append(Coin(coin_lane, y_offset=float(i*38)))

    def _spawn_obstacle(self):
        lane = self._free_lane()
        self.obstacles.append(Obstacle(lane))

    def _spawn_coin(self):
        lane = self._free_lane()
        self.coins.append(Coin(lane))

    def _spawn_coin_row(self):
        lane  = self._free_lane()
        count = random.randint(4, 7)
        for i in range(count):
            self.coins.append(Coin(lane, y_offset=float(i*38)))

    def _spawn_powerup(self):
        lane = self._free_lane()
        self.powerups.append(Powerup(lane))

    def _spawn_police(self):
        """One police boat enters from the bottom into the patrol row."""
        options = []
        if self.player.lane > 0:
            options.append(self.player.lane - 1)
        if self.player.lane < LANE_COUNT - 1:
            options.append(self.player.lane + 1)
        if not options:
            options = [self.player.lane]
        self.police_boats.append(PoliceBoat(random.choice(options)))

    # ── Collision events ─────────────────────────────────────
    def _on_hit_rock(self):
        """
        First crash  → start 10-second chase, spawn police, slow down 15 %.
        Second crash within chase window → game over.
        """
        self.collisions += 1
        # Log boat speed at collision for Graph 3 (speed-at-collision boxplot)
        save_collision_speed(getattr(self, "_eff_speed", self.speed))
        self.sfx.play("crash")
        self.particles.explosion(self.player.x, self.player.y,
                                 color=(255,136,68), count=18)

        if self.chasing:
            # 2nd crash during active chase → caught
            self._end_game("Caught! You crashed twice in 10 seconds!")
            return

        # ── First crash ──
        # Speed penalty: -15 %
        self.speed = max(SPEED_START, self.speed * (1.0 - CRASH_SPEED_PENALTY))

        # Score penalty
        self.score = max(0.0, self.score - SCORE_CRASH_PENALTY)

        # Start chase
        self.chasing     = True
        self.chase_timer = CHASE_DURATION_MS
        self._spawn_police()
        self.sfx.play("police")

        self.particles.float_text(self.player.x, self.player.y - 60,
                                  "POLICE CHASE!", color=C_RED_LIGHT)
        self.particles.float_text(self.player.x, self.player.y - 80,
                                  "-15% SPEED", color=C_RED_LIGHT, font_size=13)

    # ── Powerup activation ───────────────────────────────────
    def _activate_powerup(self, pu: Powerup):
        self.sfx.play("powerup")
        self.particles.explosion(pu.x, pu.y, color=pu.color, count=12)
        labels = {"shield":"SHIELD!","speed":"SPEED!","magnet":"MAGNET!","double":"x2 COINS!"}
        self.particles.float_text(pu.x, pu.y-40, labels[pu.type], color=pu.color)

        if   pu.type == "shield": self.player.activate_shield()
        elif pu.type == "speed":  self.player.activate_speed();  self.score += SCORE_SPEED_PICKUP
        elif pu.type == "magnet": self.player.activate_magnet()
        elif pu.type == "double": self.player.activate_double()

    # ── Announcement ─────────────────────────────────────────
    def _show_announce(self, text: str, duration: int = 2500):
        self.announce_text  = text
        self.announce_alpha = 255
        self.announce_timer = duration

    # ── Update ───────────────────────────────────────────────
    def update(self, dt: int):
        self.tick        += 1
        self.wave_offset += 0.5 * (dt / 16.67)

        if self.state != STATE_PLAYING:
            return

        self._update_speed(dt)
        if self.state != STATE_PLAYING: return   # speed crash check

        self._update_player(dt)
        self._update_obstacles(dt)
        if self.state != STATE_PLAYING: return

        self._update_coins(dt)
        self._update_powerups(dt)
        self._update_police(dt)
        if self.state != STATE_PLAYING: return

        self._update_spawn(dt)
        self._update_combo(dt)
        self._update_announce(dt)
        self._update_pirate_ships(dt)
        if self.state != STATE_PLAYING: return
        self._update_giant_fish(dt)
        if self.state != STATE_PLAYING: return
        self.particles.update(dt)

        # ── Distance & score — both scale with speed ──────────
        dt_s = dt / 1000.0

        km_gained = KM_SPEED_FACTOR * self.speed * dt_s
        if self.player.double_coins:
            km_gained *= 2
        self.distance_km += km_gained

        self.score += SCORE_SPEED_FACTOR * self.speed * dt_s

        # km milestone
        if self.distance_km >= self.next_km_milestone:
            km_int = int(self.next_km_milestone)
            self._difficulty = km_int
            self._show_announce(f"{km_int} KM!")
            self.score            += 200
            self.next_km_milestone += KM_MILESTONE

    def _update_speed(self, dt: int):
        base_increment = SPEED_INCREMENT * dt
        self.speed += base_increment

        effective_speed = self.speed * 1.4 if self.player.speed_boost else self.speed

        # Man-o-War raises the crash threshold
        threshold = MAX_SPEED_CRASH * (1.0 + getattr(self, '_speed_threshold_bonus', 0.0))
        if effective_speed >= threshold:
            self._end_game("Boat sank — maximum speed reached!")
            return

        self._eff_speed = effective_speed

    def _update_player(self, dt: int):
        self.player.update(dt)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.player.move_left()
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.player.move_right()

    def _update_obstacles(self, dt: int):
        spd = self._eff_speed
        for obs in self.obstacles[:]:
            obs.move(spd, dt)
            if obs.is_offscreen():
                self.obstacles.remove(obs); continue
            if self.player.rect.colliderect(obs.rect):
                self.obstacles.remove(obs)
                if self.player.shield:
                    # Shield absorbs the hit and shatters dramatically
                    self.player.shield_timer = 0
                    self.sfx.play("shield_break")
                    self.particles.shield_shatter(
                        self.player.x, self.player.y, color=(68, 170, 255))
                    self.particles.float_text(self.player.x, self.player.y - 50,
                                             "SHIELD SHATTERED!", color=(68,170,255))
                else:
                    self._on_hit_rock()
                    if self.state != STATE_PLAYING: return

    def _update_coins(self, dt: int):
        spd = self._eff_speed
        for coin in self.coins[:]:
            coin.move(spd, dt)
            if self.player.magnet:
                coin.apply_magnet(self.player.x, self.player.y, PU_MAGNET_RADIUS)
            if coin.is_offscreen():
                self.coins.remove(coin)
                self.coin_combo = 0; continue
            if self.player.rect.colliderect(coin.rect):
                self.coins.remove(coin)
                self.sfx.play("coin")
                base_val = 2 if self.player.double_coins else 1
                val = int(base_val * self.player.coin_multiplier)
                self.coins_count += val
                self.score       += val * SCORE_PER_COIN
                self.coin_combo  += 1
                self.combo_timer_ms = COMBO_RESET_MS

                if self.coin_combo >= COMBO_THRESHOLD:
                    bonus = self.coin_combo * COMBO_BONUS_PER_COIN
                    self.score += bonus
                    self.particles.float_text(coin.x, coin.y-24,
                                             f"COMBO x{self.coin_combo}! +{bonus}",
                                             color=C_GOLD, font_size=15)
                else:
                    self.particles.float_text(coin.x, coin.y-14, f"+{val}",
                                             color=C_GOLD, font_size=13)

    def _update_powerups(self, dt: int):
        spd = self._eff_speed
        for pu in self.powerups[:]:
            pu.move(spd, dt)
            if pu.is_offscreen():
                self.powerups.remove(pu); continue
            if self.player.rect.colliderect(pu.rect):
                self.powerups.remove(pu)
                self._activate_powerup(pu)

    def _update_police(self, dt: int):
        if not self.chasing:
            return

        self.chase_timer -= dt

        for pb in self.police_boats[:]:
            pb.update_position(self._eff_speed, dt, player_x=self.player.x)
            # Police do NOT collide with player — they just patrol below

        if self.chase_timer <= 0:
            # Chase expired — player escaped!
            self.chasing = False
            self.police_boats.clear()
            self.chase_timer = 0
            self.particles.float_text(self.player.x, self.player.y - 60,
                                      "ESCAPED!", color=C_GREEN)

    def _update_spawn(self, dt: int):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            base_interval = max(280, 900 - int(self._eff_speed * 45))
            diff_scale = max(0.5, 1.0 - self._difficulty * 0.08)
            interval = int(base_interval * diff_scale)
            self.spawn_timer = int(interval * random.uniform(0.7, 1.3))
            self._spawn_objects()

    def _update_combo(self, dt: int):
        if self.combo_timer_ms > 0:
            self.combo_timer_ms -= dt
            if self.combo_timer_ms <= 0:
                self.coin_combo = 0

    # ── Pirate ship (2-lane, from below, after 2 km) ─────────
    def _update_pirate_ships(self, dt: int):
        if self.distance_km < 2.0:
            return

        self._pirate_ship_cd -= dt
        if self._pirate_ship_cd <= 0:
            self._spawn_pirate_ship()
            self._pirate_ship_cd = random.randint(18_000, 30_000)

        spd = self._eff_speed
        for ps in self.pirate_ships[:]:
            ps.move(spd, dt)
            if ps.y < -ps.DRAW_H:
                self.pirate_ships.remove(ps)
                continue
            if self.player.rect.colliderect(ps.rect):
                self.pirate_ships.remove(ps)
                if self.player.shield:
                    self.player.shield_timer = 0
                    self.sfx.play("shield_break")
                    self.particles.shield_shatter(self.player.x, self.player.y,
                                                  color=(255, 80, 80))
                    self.particles.float_text(self.player.x, self.player.y - 50,
                                             "SHIELD SHATTERED!", color=(255, 80, 80))
                else:
                    self._end_game("Crushed by the Pirate Armada!")
                    return

    def _spawn_pirate_ship(self):
        player_lane = self.player.lane
        options = [ll for ll in range(LANE_COUNT - 1)
                   if player_lane not in (ll, ll + 1)]
        if not options:
            options = list(range(LANE_COUNT - 1))
        ll = random.choice(options)
        self.pirate_ships.append(PirateShip(ll))
        self.particles.float_text(SCREEN_W // 2, SCREEN_H // 2 + 60,
                                  "!! PIRATE SHIP !!", color=(255, 80, 80),
                                  font_size=17)

    # ── Giant fish (3-lane, bubble warning, after 3 km) ──────
    def _update_giant_fish(self, dt: int):
        if self.distance_km < 3.0:
            return

        self._giant_fish_cd -= dt
        if self._giant_fish_cd <= 0:
            self._spawn_giant_fish()
            self._giant_fish_cd = random.randint(22_000, 38_000)

        for gf in self.giant_fish[:]:
            gf.update(dt)
            if gf.y < -gf.DRAW_H:
                self.giant_fish.remove(gf)
                continue
            gr = gf.rect
            if gr.width == 0:
                continue   # still in warning phase
            if self.player.rect.colliderect(gr):
                self.giant_fish.remove(gf)
                self._end_game("Swallowed by the Leviathan!")
                return

    def _spawn_giant_fish(self):
        center = random.randint(1, 3)
        self.giant_fish.append(GiantFish(center))
        self.particles.float_text(SCREEN_W // 2, SCREEN_H // 2 + 60,
                                  "!! LEVIATHAN !!", color=(80, 220, 255),
                                  font_size=17)

    # ── Ocean background color ───────────────────────────────
    def _ocean_bg(self):
        km = self.distance_km
        if km < 1.0:
            return C_OCEAN_DEEP          # (10, 22, 40)
        elif km < 2.0:
            t = km - 1.0
            return (int(10 + t*(8-10)), int(22 + t*(18-22)), int(40 + t*(56-40)))
        elif km < 3.0:
            t = km - 2.0
            return (int(8 + t*(6-8)), int(18 + t*(15-18)), int(56 + t*(60-56)))
        else:
            t = min(1.0, (km - 3.0) / 3.0)
            return (int(6 + t*(20-6)), int(15 + t*(11-15)), int(60 + t*(38-60)))

    def _update_announce(self, dt: int):
        if self.announce_timer > 0:
            self.announce_timer -= dt
            if self.announce_timer < 600:
                self.announce_alpha = max(0, int(self.announce_timer * (255/600)))
        else:
            self.announce_alpha = 0

    # ── Event handling ───────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        # ── Slider drag (settings) ────────────────────────────
        if self.state == STATE_SETTINGS:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                for name, rect in self.settings_sliders.items():
                    hit = pygame.Rect(rect.x, rect.y - 8, rect.width, rect.height + 16)
                    if hit.collidepoint(pos):
                        self._drag_slider = name
                        self._update_slider(name, pos[0])
                        return
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._drag_slider = None
            if event.type == pygame.MOUSEMOTION and self._drag_slider:
                self._update_slider(self._drag_slider, event.pos[0])
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.state == STATE_MENU:
                if   self.menu_buttons["SET  SAIL"].collidepoint(pos):    self._start_game()
                elif self.menu_buttons["BOATS"].collidepoint(pos):        self.state = STATE_BOAT
                elif self.menu_buttons["LEADERBOARD"].collidepoint(pos):  self.state = STATE_LEADERBOARD
                elif self.menu_buttons["DATA"].collidepoint(pos):         self.state = STATE_DATA
                elif self.menu_buttons["SETTINGS"].collidepoint(pos):
                    self._settings_source = STATE_MENU
                    self.state = STATE_SETTINGS
            elif self.state == STATE_PLAYING:
                if self.pause_btn_rect.collidepoint(pos):
                    self._pause_game()
            elif self.state == STATE_PAUSED:
                if   self.pause_buttons["RESUME"].collidepoint(pos):    self._resume_game()
                elif self.pause_buttons["SETTINGS"].collidepoint(pos):
                    self._settings_source = STATE_PAUSED
                    self.state = STATE_SETTINGS
                elif self.pause_buttons["MAIN MENU"].collidepoint(pos):
                    self._stop_music()
                    self.state = STATE_MENU
            elif self.state == STATE_GAMEOVER:
                if   self.over_buttons["PLAY AGAIN"].collidepoint(pos):   self._start_game()
                elif self.over_buttons["LEADERBOARD"].collidepoint(pos):  self.state = STATE_LEADERBOARD
                elif self.over_buttons["MAIN MENU"].collidepoint(pos):    self.state = STATE_MENU
            elif self.state == STATE_LEADERBOARD:
                if self.lb_buttons["BACK"].collidepoint(pos): self.state = STATE_MENU
            elif self.state == STATE_DATA:
                if self.data_buttons["BACK"].collidepoint(pos):
                    self.state = STATE_MENU
                else:
                    for i, rect in enumerate(ui.get_data_tab_rects()):
                        if rect.collidepoint(pos):
                            self._data_tab = i
                            break
            elif self.state == STATE_SETTINGS:
                if self.settings_buttons["BACK"].collidepoint(pos):
                    self.state = self._settings_source
            elif self.state == STATE_BOAT:
                self._handle_shop_click(pos)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.state != STATE_SETTINGS:
                self._drag_slider = None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == STATE_PLAYING:
                    self._pause_game()
                elif self.state == STATE_PAUSED:
                    self._resume_game()
                elif self.state == STATE_SETTINGS:
                    self.state = self._settings_source
                elif self.state == STATE_BOAT:
                    self.state = STATE_MENU
                else:
                    self.state = STATE_MENU
            if event.key == pygame.K_r and self.state == STATE_GAMEOVER:
                print(generate_report())

    def _handle_shop_click(self, pos):
        boat = BOAT_CATALOG[self._shop_idx]
        garage = load_garage()

        # Navigate
        if self.shop_buttons["<"].collidepoint(pos):
            self._shop_idx = (self._shop_idx - 1) % len(BOAT_CATALOG)
            self._shop_color_pick = {"hull_idx": 0, "sail_idx": 0}
            return
        if self.shop_buttons[">"].collidepoint(pos):
            self._shop_idx = (self._shop_idx + 1) % len(BOAT_CATALOG)
            self._shop_color_pick = {"hull_idx": 0, "sail_idx": 0}
            return
        if self.shop_buttons["BACK"].collidepoint(pos):
            self.state = STATE_MENU
            return

        # Color swatch clicks — use exact rects from ui to match draw positions
        swatch_rects = ui.get_shop_color_rects(boat)
        for key, rect in swatch_rects.items():
            if rect.collidepoint(pos):
                kind, ci_str = key.split("_")   # "hull" or "sail", index
                self._shop_color_pick[f"{kind}_idx"] = int(ci_str)
                self._save_shop_colors(boat["id"], garage)
                return

        # Main action button
        if self.shop_buttons["ACT"].collidepoint(pos):
            is_owned = boat["id"] in garage["owned"]
            is_selected = boat["id"] == garage["selected"]
            if not is_owned:
                if buy_boat(boat["id"], boat["price"]):
                    select_boat(boat["id"])
                    self._save_shop_colors(boat["id"], load_garage())
            elif not is_selected:
                select_boat(boat["id"])
                self._save_shop_colors(boat["id"], garage)
            else:
                # Already selected — start game!
                self._start_game()

    def _save_shop_colors(self, boat_id: str, garage: dict):
        boat = BOAT_BY_ID.get(boat_id, {})
        hp = boat.get("hull_palette")
        sp = boat.get("sail_palette")
        hull_c = tuple(hp[self._shop_color_pick["hull_idx"]]) if hp else None
        sail_c = tuple(sp[self._shop_color_pick["sail_idx"]]) if sp else None
        if hull_c or sail_c:
            colors = {}
            if hull_c: colors["hull"] = list(hull_c)
            if sail_c: colors["sail"] = list(sail_c)
            g = load_garage()
            g["colors"][boat_id] = colors
            from data.data_recorder import save_garage
            save_garage(g)

    def _pause_game(self):
        self.state = STATE_PAUSED
        self._pause_music()

    def _resume_game(self):
        self.state = STATE_PLAYING
        self._resume_music()

    def _update_slider(self, name: str, mouse_x: int):
        rect = self.settings_sliders[name]
        val = max(0.0, min(1.0, (mouse_x - rect.x) / rect.width))
        if name == "music":
            self.music_vol = val
        else:
            self.sfx_vol = val
        self._apply_volumes()

    # ── Powerup visual effects ───────────────────────────────
    def _draw_powerup_effects(self):
        px, py = int(self.player.x), int(self.player.y)
        pulse = (math.sin(self.tick * 0.10) + 1) * 0.5

        if self.player.magnet:
            mr = PU_MAGNET_RADIUS + self.player.magnet_bonus
            for ring_r, base_a in [(int(mr), 55), (int(mr * 0.55), 28)]:
                alpha = int(base_a + pulse * base_a)
                rs = pygame.Surface((ring_r*2+4, ring_r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(rs, (220, 80, 255, alpha), (ring_r+2, ring_r+2), ring_r, 2)
                self.screen.blit(rs, (px - ring_r - 2, py - ring_r - 2))
            for i in range(6):
                angle = (i / 6) * math.pi * 2 + self.tick * 0.07
                sx = int(px + math.cos(angle) * mr)
                sy = int(py + math.sin(angle) * mr)
                dot_a = int(70 + pulse * 130)
                ds = pygame.Surface((7, 7), pygame.SRCALPHA)
                pygame.draw.circle(ds, (220, 80, 255, dot_a), (3, 3), 3)
                self.screen.blit(ds, (sx - 3, sy - 3))

        if self.player.speed_boost:
            spulse = (math.sin(self.tick * 0.20) + 1) * 0.5
            for ox, length, base_a in [(-14, 20, 140), (-5, 30, 210), (5, 30, 210), (14, 20, 140)]:
                line_a = int(base_a * (0.35 + spulse * 0.65))
                ts = pygame.Surface((3, length), pygame.SRCALPHA)
                ts.fill((255, 230, 60, line_a))
                self.screen.blit(ts, (px + ox - 1, py + 30))
            glow_a = int(80 + spulse * 100)
            gs = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(gs, (255, 240, 80, glow_a), (10, 10), 10)
            self.screen.blit(gs, (px - 10, py + 28))

        if self.player.double_coins:
            d2pulse = (math.sin(self.tick * 0.13) + 1) * 0.5
            # Orbiting coin sparks
            for i in range(5):
                angle = (i / 5) * math.pi * 2 + self.tick * 0.055
                dr = int(34 + d2pulse * 10)
                sx = int(px + math.cos(angle) * dr)
                sy = int(py + math.sin(angle) * dr)
                dot_a = int(100 + d2pulse * 130)
                ds = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(ds, (68, 255, 150, dot_a), (4, 4), 4)
                self.screen.blit(ds, (sx - 4, sy - 4))
            # Pulsing ring
            rr = int(44 + d2pulse * 8)
            rs = pygame.Surface((rr*2+4, rr*2+4), pygame.SRCALPHA)
            ring_a = int(38 + d2pulse * 38)
            pygame.draw.circle(rs, (68, 255, 150, ring_a), (rr+2, rr+2), rr, 2)
            self.screen.blit(rs, (px - rr - 2, py - rr - 2))

    # ── Draw ─────────────────────────────────────────────────
    def draw(self):
        # Use remapped mouse position (set by main loop for resizable window)
        mp = self.mouse_pos if self.mouse_pos != (0, 0) else pygame.mouse.get_pos()

        if self.state == STATE_MENU:
            ui.draw_menu(self.screen, self.wave_offset, self.menu_buttons, mp)

        elif self.state == STATE_PLAYING:
            self._draw_game(mp)

        elif self.state == STATE_PAUSED:
            self._draw_game(mp)
            ui.draw_pause(self.screen, self.pause_buttons, mp)

        elif self.state == STATE_GAMEOVER:
            self._draw_game(mp)
            ui.draw_gameover(self.screen, self.end_stats,
                             self.over_buttons, mp,
                             is_highscore=self.is_highscore)

        elif self.state == STATE_LEADERBOARD:
            ui.draw_leaderboard(self.screen, load_leaderboard(),
                                self.lb_buttons, mp)

        elif self.state == STATE_DATA:
            ui.draw_data_page(self.screen, load_sessions(),
                              load_collision_speeds(),
                              self.data_buttons, mp,
                              tab=self._data_tab)

        elif self.state == STATE_SETTINGS:
            ui.draw_settings(self.screen, self.music_vol, self.sfx_vol,
                             self.settings_buttons, self.settings_sliders, mp)

        elif self.state == STATE_BOAT:
            garage  = load_garage()
            # Build action button label dynamically
            boat    = BOAT_CATALOG[self._shop_idx]
            is_owned    = boat["id"] in garage["owned"]
            is_selected = boat["id"] == garage["selected"]
            if not is_owned:
                act_label = "BUY"
            elif not is_selected:
                act_label = "SELECT"
            else:
                act_label = "PLAY"
            # Rename ACT button rect to correct label for ui
            btns = dict(self.shop_buttons)
            btns[act_label] = btns.pop("ACT")
            ui.draw_boat_shop(
                self.screen,
                BOAT_CATALOG,
                garage["owned"],
                garage["selected"],
                load_wallet(),
                self._shop_idx,
                self._shop_color_pick,
                btns,
                mp,
                tick=self.tick,
            )

    def _draw_game(self, mp=(0, 0)):
        ui.draw_water(self.screen, self.wave_offset,
                      bg_color=self._ocean_bg() if self.state == STATE_PLAYING else None)

        for obs in self.obstacles:    obs.draw(self.screen)
        for coin in self.coins:       coin.draw(self.screen)
        for pu in self.powerups:      pu.draw(self.screen, self.tick)
        for pb in self.police_boats:  pb.draw(self.screen, self.tick)
        for ps in self.pirate_ships:  ps.draw(self.screen, self.tick)
        for gf in self.giant_fish:    gf.draw(self.screen, self.tick)
        self.player.draw(self.screen, self.tick)
        self._draw_powerup_effects()
        self.particles.draw(self.screen)

        spd = getattr(self, "_eff_speed", self.speed)
        ui.draw_hud(self.screen, self.score, self.coins_count,
                    self.distance_km, spd,
                    self.player.get_active_powerups(),
                    self.chase_timer if self.chasing else 0,
                    self.tick,
                    pause_btn_rect=self.pause_btn_rect,
                    mouse_pos=mp)
        ui.draw_speed_bar(self.screen, spd)

        if self.announce_alpha > 0:
            ui.draw_announce(self.screen, self.announce_text, self.announce_alpha)