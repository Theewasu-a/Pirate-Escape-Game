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

from constants import (
    SCREEN_W, SCREEN_H, LANES, LANE_COUNT,
    SPEED_START, SPEED_INCREMENT, MAX_SPEED_CRASH, CRASH_SPEED_PENALTY,
    CHASE_DURATION_MS,
    SCORE_SPEED_FACTOR, KM_SPEED_FACTOR, SCORE_PER_COIN,
    SCORE_CRASH_PENALTY, SCORE_SPEED_PICKUP,
    COMBO_THRESHOLD, COMBO_BONUS_PER_COIN, COMBO_RESET_MS,
    PU_MAGNET_RADIUS, KM_MILESTONE,
    STATE_MENU, STATE_PLAYING, STATE_GAMEOVER, STATE_LEADERBOARD,
    C_GOLD, C_RED_LIGHT, C_GREEN, C_OCEAN_FOAM,
)
from player_boat  import PlayerBoat
from objects      import Obstacle, Coin, Powerup, PoliceBoat
from particles    import ParticleSystem
from data_recorder import (
    SessionData, save_session,
    LeaderboardEntry, add_to_leaderboard, load_leaderboard,
    generate_report,
)
import ui


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
        self.particles   = ParticleSystem()

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

        self._build_buttons()

    # ── Buttons ──────────────────────────────────────────────
    def _build_buttons(self):
        bw, bh = 200, 38
        cx = SCREEN_W//2 - bw//2
        self.menu_buttons = {
            "SET  SAIL":   pygame.Rect(cx, 300, bw, bh),
            "LEADERBOARD": pygame.Rect(cx, 352, bw, bh),
        }
        self.over_buttons = {
            "PLAY AGAIN":  pygame.Rect(cx, 360, bw, bh),
            "LEADERBOARD": pygame.Rect(cx, 408, bw, bh),
            "MAIN MENU":   pygame.Rect(cx, 456, bw, bh),
        }
        self.lb_buttons = {
            "BACK": pygame.Rect(cx, SCREEN_H - 90, bw, bh),
        }

    # ── State transitions ────────────────────────────────────
    def _start_game(self):
        self.state = STATE_PLAYING
        self.player = PlayerBoat()
        self.obstacles.clear()
        self.coins.clear()
        self.powerups.clear()
        self.police_boats.clear()
        self.particles.clear()

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

    def _end_game(self, reason: str):
        self.state = STATE_GAMEOVER
        elapsed_s  = (pygame.time.get_ticks() - self.session_start_ms) // 1000

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
        }

        for _ in range(3):
            self.particles.explosion(
                self.player.x + random.uniform(-30, 30),
                self.player.y + random.uniform(-20, 20),
                color=C_RED_LIGHT, count=20
            )

    # ── Spawning ─────────────────────────────────────────────
    def _spawn_objects(self):
        r = random.random()
        if r < 0.42:
            self._spawn_obstacle()
            # Extra rock at higher speeds
            if self.speed > 7.0 and random.random() < 0.35:
                self._spawn_obstacle()
        elif r < 0.60:
            self._spawn_coin()
        elif r < 0.82:
            self._spawn_coin_row()
        elif r < 0.92:
            self._spawn_powerup()
        else:
            self._spawn_obstacle()
            self._spawn_coin_row()

    def _spawn_obstacle(self):
        self.obstacles.append(Obstacle(random.randint(0, LANE_COUNT-1)))

    def _spawn_coin(self):
        self.coins.append(Coin(random.randint(0, LANE_COUNT-1)))

    def _spawn_coin_row(self):
        lane  = random.randint(0, LANE_COUNT-1)
        count = random.randint(4, 7)
        for i in range(count):
            self.coins.append(Coin(lane, y_offset=float(i*38)))

    def _spawn_powerup(self):
        self.powerups.append(Powerup(random.randint(0, LANE_COUNT-1)))

    def _spawn_police(self):
        """Police boats enter from the bottom into the patrol row."""
        left  = max(0, self.player.lane - 1)
        right = min(LANE_COUNT-1, self.player.lane + 1)
        self.police_boats.append(PoliceBoat(left))
        if left != right:
            self.police_boats.append(PoliceBoat(right))

    # ── Collision events ─────────────────────────────────────
    def _on_hit_rock(self):
        """
        First crash  → start 10-second chase, spawn police, slow down 15 %.
        Second crash within chase window → game over.
        """
        self.collisions += 1
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

        self.particles.float_text(self.player.x, self.player.y - 60,
                                  "POLICE CHASE!", color=C_RED_LIGHT)
        self.particles.float_text(self.player.x, self.player.y - 80,
                                  "-15% SPEED", color=C_RED_LIGHT, font_size=13)

    # ── Powerup activation ───────────────────────────────────
    def _activate_powerup(self, pu: Powerup):
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
        self.particles.update(dt)

        # ── Distance & score — both scale with speed ──────────
        # dt is milliseconds; convert to seconds for formula
        dt_s = dt / 1000.0

        km_gained = KM_SPEED_FACTOR * self.speed * dt_s
        if self.player.double_coins:
            km_gained *= 2              # x2 km when double-coin active
        self.distance_km += km_gained

        self.score += SCORE_SPEED_FACTOR * self.speed * dt_s

        # km milestone
        if self.distance_km >= self.next_km_milestone:
            self._show_announce(f"{int(self.next_km_milestone)} KM!")
            self.score            += 200
            self.next_km_milestone += KM_MILESTONE

    def _update_speed(self, dt: int):
        # Speed boost powerup gives a temporary multiplier on top
        base_increment = SPEED_INCREMENT * dt
        self.speed += base_increment

        effective_speed = self.speed * 1.4 if self.player.speed_boost else self.speed

        if effective_speed >= MAX_SPEED_CRASH:
            self._end_game("Boat sank — maximum speed reached!")
            return

        # Store effective speed for use in object movement
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
            if not self.player.shield and self.player.rect.colliderect(obs.rect):
                self.obstacles.remove(obs)
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
                val = 2 if self.player.double_coins else 1
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
                self.particles.explosion(coin.x, coin.y, C_GOLD, count=6)

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
            pb.update_position(self._eff_speed, dt)
            # Police do NOT collide with player — they just idle at bottom

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
            interval = max(280, 900 - int(self._eff_speed * 45))
            self.spawn_timer = int(interval * random.uniform(0.7, 1.3))
            self._spawn_objects()

    def _update_combo(self, dt: int):
        if self.combo_timer_ms > 0:
            self.combo_timer_ms -= dt
            if self.combo_timer_ms <= 0:
                self.coin_combo = 0

    def _update_announce(self, dt: int):
        if self.announce_timer > 0:
            self.announce_timer -= dt
            if self.announce_timer < 600:
                self.announce_alpha = max(0, int(self.announce_timer * (255/600)))
        else:
            self.announce_alpha = 0

    # ── Event handling ───────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.state == STATE_MENU:
                if self.menu_buttons["SET  SAIL"].collidepoint(pos):   self._start_game()
                elif self.menu_buttons["LEADERBOARD"].collidepoint(pos): self.state = STATE_LEADERBOARD
            elif self.state == STATE_GAMEOVER:
                if self.over_buttons["PLAY AGAIN"].collidepoint(pos):   self._start_game()
                elif self.over_buttons["LEADERBOARD"].collidepoint(pos): self.state = STATE_LEADERBOARD
                elif self.over_buttons["MAIN MENU"].collidepoint(pos):  self.state = STATE_MENU
            elif self.state == STATE_LEADERBOARD:
                if self.lb_buttons["BACK"].collidepoint(pos): self.state = STATE_MENU

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == STATE_PLAYING: self._end_game("Quit")
                else: self.state = STATE_MENU
            if event.key == pygame.K_r and self.state == STATE_GAMEOVER:
                print(generate_report())

    # ── Draw ─────────────────────────────────────────────────
    def draw(self):
        mp = pygame.mouse.get_pos()

        if self.state == STATE_MENU:
            ui.draw_menu(self.screen, self.wave_offset, self.menu_buttons, mp)

        elif self.state == STATE_PLAYING:
            self._draw_game()

        elif self.state == STATE_GAMEOVER:
            self._draw_game()
            ui.draw_gameover(self.screen, self.end_stats,
                             self.over_buttons, mp,
                             is_highscore=self.is_highscore)

        elif self.state == STATE_LEADERBOARD:
            ui.draw_leaderboard(self.screen, load_leaderboard(),
                                self.lb_buttons, mp)

    def _draw_game(self):
        ui.draw_water(self.screen, self.wave_offset)

        for obs in self.obstacles:    obs.draw(self.screen)
        for coin in self.coins:       coin.draw(self.screen)
        for pu in self.powerups:      pu.draw(self.screen, self.tick)
        for pb in self.police_boats:  pb.draw(self.screen, self.tick)
        self.player.draw(self.screen, self.tick)
        self.particles.draw(self.screen)

        spd = getattr(self, "_eff_speed", self.speed)
        ui.draw_hud(self.screen, self.score, self.coins_count,
                    self.distance_km, spd,
                    self.player.get_active_powerups(),
                    self.chase_timer if self.chasing else 0,
                    self.tick)
        ui.draw_speed_bar(self.screen, spd)

        if self.announce_alpha > 0:
            ui.draw_announce(self.screen, self.announce_text, self.announce_alpha)
