"""
objects.py - Game object classes
"""

import pygame
import random
import math
from .constants import (
    SCREEN_H, LANES, LANE_COUNT,
    C_GOLD, C_GOLD_DARK, C_RED, C_RED_LIGHT, C_WHITE, C_POLICE_BLUE,
)


# ── Obstacle ────────────────────────────────────────────────
class Obstacle:
    ROCK_COLORS = [(122,122,138),(106,106,122),(138,138,154),(90,90,106)]

    def __init__(self, lane: int):
        self.lane  = lane
        self.x     = float(LANES[lane])
        self.y     = -40.0
        self.size  = random.uniform(20, 38)
        n = random.randint(7, 11)
        self.points_rel = [
            (math.cos(i/n*math.pi*2)*self.size*random.uniform(0.7,1.15),
             math.sin(i/n*math.pi*2)*self.size*random.uniform(0.7,1.15))
            for i in range(n)
        ]
        self.color = random.choice(self.ROCK_COLORS)
        self.hit_w = self.size * 1.1
        self.hit_h = self.size * 0.9

    @property
    def rect(self):
        return pygame.Rect(int(self.x-self.hit_w/2), int(self.y-self.hit_h/2),
                           int(self.hit_w), int(self.hit_h))

    def move(self, speed, dt):   self.y += speed * dt * 0.06
    def is_offscreen(self):      return self.y > SCREEN_H + 60

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        s = int(self.size)

        # ── Drop shadow (water ripple) ────────────────────────
        sh_w, sh_h = int(s * 2.0), int(s * 0.55)
        sh = pygame.Surface((sh_w, sh_h), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 55), sh.get_rect())
        surface.blit(sh, (cx - sh_w // 2 + 3, cy + int(s * 0.35)))

        # ── Foam ring around base ─────────────────────────────
        foam_w, foam_h = int(s * 2.2), int(s * 0.45)
        foam = pygame.Surface((foam_w, foam_h), pygame.SRCALPHA)
        pygame.draw.ellipse(foam, (180, 220, 240, 45), foam.get_rect())
        surface.blit(foam, (cx - foam_w // 2, cy + int(s * 0.28)))

        # ── Dark base layer (depth) ───────────────────────────
        dark_color = tuple(max(0, c - 38) for c in self.color)
        dark_pts = [(cx + int(px * 1.07), cy + int(py * 1.07) + 3)
                    for px, py in self.points_rel]
        pygame.draw.polygon(surface, dark_color, dark_pts)

        # ── Main rock body ────────────────────────────────────
        pts = [(cx + px, cy + py) for px, py in self.points_rel]
        pygame.draw.polygon(surface, self.color, pts)

        # ── Moss/algae patches (dark green splotches) ─────────
        moss_color = (60, 90, 55, 90)
        for i in range(0, len(self.points_rel) - 1, 3):
            px = int(self.points_rel[i][0] * 0.45)
            py = int(self.points_rel[i][1] * 0.45)
            ms = pygame.Surface((int(s * 0.55), int(s * 0.3)), pygame.SRCALPHA)
            pygame.draw.ellipse(ms, moss_color, ms.get_rect())
            surface.blit(ms, (cx + px - int(s * 0.27), cy + py - int(s * 0.15)))

        # ── Edge outline for definition ───────────────────────
        edge_color = tuple(max(0, c - 55) for c in self.color)
        pygame.draw.polygon(surface, edge_color, pts, 2)

        # ── Highlight (top-left light source) ─────────────────
        hl_w, hl_h = int(s * 0.75), int(s * 0.42)
        hl = pygame.Surface((hl_w, hl_h), pygame.SRCALPHA)
        pygame.draw.ellipse(hl, (255, 255, 255, 55), hl.get_rect())
        surface.blit(hl, (cx - int(s * 0.55), cy - int(s * 0.48)))

        # ── Small bright specular dot ─────────────────────────
        spec = pygame.Surface((int(s * 0.28), int(s * 0.18)), pygame.SRCALPHA)
        pygame.draw.ellipse(spec, (255, 255, 255, 120), spec.get_rect())
        surface.blit(spec, (cx - int(s * 0.38), cy - int(s * 0.35)))


# ── Coin ────────────────────────────────────────────────────
class Coin:
    def __init__(self, lane: int, y_offset: float = 0.0):
        self.lane      = lane
        self.x         = float(LANES[lane])
        self.y         = -20.0 - y_offset
        self.r         = 10
        self.rot       = random.uniform(0, math.pi*2)
        self.rot_speed = random.uniform(0.03, 0.07)
        self.value     = 1

    @property
    def rect(self):
        cr = self.r + 14
        return pygame.Rect(int(self.x)-cr, int(self.y)-cr, cr*2, cr*2)

    def move(self, speed, dt):
        self.y   += speed * dt * 0.06
        self.rot += self.rot_speed

    def is_offscreen(self): return self.y > SCREEN_H + 30

    def apply_magnet(self, px, py, radius):
        dx, dy = px - self.x, py - self.y
        dist   = math.hypot(dx, dy)
        if 0 < dist < radius:
            self.x += dx * 0.12
            self.y += dy * 0.12

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        r = self.r
        glow = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*C_GOLD, 50), (r*2, r*2), r*2)
        surface.blit(glow, (cx-r*2, cy-r*2))
        pygame.draw.circle(surface, C_GOLD, (cx, cy), r)
        pygame.draw.circle(surface, C_GOLD_DARK, (cx, cy), r, 2)
        pygame.draw.circle(surface, C_GOLD_DARK, (cx, cy), r-3, 1)
        f = pygame.font.SysFont("serif", r+2, bold=True)
        t = f.render("$", True, (120,80,0))
        surface.blit(t, (cx-t.get_width()//2, cy-t.get_height()//2))


# ── Powerup ─────────────────────────────────────────────────
class Powerup:
    TYPE_CONFIG = {
        "shield": {"color":(68,170,255),  "icon":"SH"},
        "speed":  {"color":(255,255,68),  "icon":"SP"},
        "magnet": {"color":(255,68,255),  "icon":"MG"},
        "double": {"color":(68,255,136),  "icon":"x2"},
    }
    TYPES = list(TYPE_CONFIG.keys())

    def __init__(self, lane: int):
        self.lane      = lane
        self.x         = float(LANES[lane])
        self.y         = -20.0
        self.type      = random.choice(self.TYPES)
        self.rot       = 0.0
        self.rot_speed = 0.04
        self.r         = 16

    @property
    def color(self):  return self.TYPE_CONFIG[self.type]["color"]
    @property
    def rect(self):
        return pygame.Rect(int(self.x)-self.r, int(self.y)-self.r, self.r*2, self.r*2)

    def move(self, speed, dt):
        self.y   += speed * dt * 0.06
        self.rot += self.rot_speed

    def is_offscreen(self): return self.y > SCREEN_H + 30

    def draw(self, surface, tick):
        cx, cy = int(self.x), int(self.y)
        r = self.r
        pulse = int(6 + 4*math.sin(tick*0.01))
        gs = pygame.Surface((r*2+pulse*2, r*2+pulse*2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*self.color, 40), (r+pulse, r+pulse), r+pulse)
        surface.blit(gs, (cx-r-pulse, cy-r-pulse))
        bg = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(bg, (*self.color, 60), (r,r), r)
        surface.blit(bg, (cx-r, cy-r))
        pygame.draw.circle(surface, self.color, (cx,cy), r, 2)
        f = pygame.font.SysFont("consolas,monospace", 10, bold=True)
        t = f.render(self.TYPE_CONFIG[self.type]["icon"], True, self.color)
        surface.blit(t, (cx-t.get_width()//2, cy-t.get_height()//2))


# ── PoliceBoat ──────────────────────────────────────────────
class PoliceBoat:
    """
    Spawns from BOTTOM of screen and drives to the patrol row.
    After arriving it tracks the player's X position.
    A 2nd player crash while chasing = game over.
    """

    def __init__(self, lane: int):
        self.lane = lane
        self.x    = float(LANES[lane])
        self.y    = float(SCREEN_H + 80)
        self.patrol_y = float(SCREEN_H - 100)
        self.arrived  = False
        self.w = 44
        self.h = 64
        # Target X for tracking (set from game_manager)
        self.target_x = self.x

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - 22, int(self.y) - 32, 44, 64)

    def update_position(self, speed: float, dt: int, player_x: float = None):
        if not self.arrived:
            self.y -= speed * dt * 0.06 * 2.5
            if self.y <= self.patrol_y:
                self.y       = self.patrol_y
                self.arrived = True
        else:
            # Smoothly track player X
            if player_x is not None:
                self.target_x = player_x
            dx = self.target_x - self.x
            max_move = speed * dt * 0.045
            if abs(dx) < max_move:
                self.x = self.target_x
            else:
                self.x += max_move * (1 if dx > 0 else -1)

    def is_offscreen(self): return False

    def draw(self, surface, tick):
        cx, cy = int(self.x), int(self.y)
        flash = (tick // 7) % 2 == 0

        # ── Shadow ───────────────────────────────────────────
        sh = pygame.Surface((50, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 50), sh.get_rect())
        surface.blit(sh, (cx - 25, cy + 28))

        # ── Hull (wooden dark navy, old-fashioned pointed bow) ─
        HULL_DARK  = (28,  48, 110)
        HULL_MID   = (40,  68, 148)
        WOOD_HULL  = (80,  55,  28)
        WOOD_PLANK = (100, 70,  36)

        hull_pts = [
            (cx,    cy - 34),   # bow (top, pointed)
            (cx+20, cy - 12),
            (cx+22, cy + 20),
            (cx+14, cy + 34),
            (cx - 14, cy + 34),
            (cx - 22, cy + 20),
            (cx - 20, cy - 12),
        ]
        pygame.draw.polygon(surface, HULL_DARK, hull_pts)

        # Wood plank lines on hull
        for offset in (-8, 0, 10, 20):
            y_line = cy + offset
            x_clip = max(2, int(22 * (1 - abs(offset - 5) / 35)))
            pygame.draw.line(surface, WOOD_PLANK,
                             (cx - x_clip - 12, y_line),
                             (cx + x_clip + 12, y_line), 1)

        # Hull outline
        pygame.draw.polygon(surface, (15, 28, 72), hull_pts, 2)

        # ── Cabin / wheelhouse ───────────────────────────────
        CABIN_COLOR = (55, 42, 22)
        cabin_rect  = pygame.Rect(cx - 13, cy - 16, 26, 22)
        pygame.draw.rect(surface, CABIN_COLOR, cabin_rect, border_radius=3)
        # Cabin window (porthole)
        pygame.draw.circle(surface, (180, 210, 230), (cx, cy - 6), 5)
        pygame.draw.circle(surface, (120, 150, 170), (cx, cy - 6), 5, 1)
        # Cabin trim
        pygame.draw.rect(surface, WOOD_PLANK, cabin_rect, 2, border_radius=3)

        # ── Mast / flagpole ───────────────────────────────────
        mast_top = cy - 54
        pygame.draw.line(surface, WOOD_HULL, (cx, cy - 16), (cx, mast_top), 2)
        # Crossbeam
        pygame.draw.line(surface, WOOD_HULL, (cx - 9, mast_top + 8), (cx + 9, mast_top + 8), 2)

        # ── Police flag (blue & white stripes) ────────────────
        flag_x, flag_y = cx + 1, mast_top
        for i in range(4):
            col = C_POLICE_BLUE if i % 2 == 0 else C_WHITE
            pygame.draw.rect(surface, col,
                             (flag_x, flag_y + i * 4, 14, 4))
        pygame.draw.rect(surface, (15, 28, 72),
                         (flag_x, flag_y, 14, 16), 1)

        # ── Vintage siren lanterns (red + blue alternating) ──
        lc = (220, 40,  40) if flash else ( 40,  80, 220)
        rc = ( 40,  80, 220) if flash else (220,  40,  40)
        for (lx, color) in ((cx - 16, lc), (cx + 16, rc)):
            # lantern body
            pygame.draw.rect(surface, color,
                             (lx - 5, cy - 22, 10, 10), border_radius=2)
            # glow halo
            glow = pygame.Surface((22, 22), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 70), (11, 11), 11)
            surface.blit(glow, (lx - 11, cy - 28))

        # ── White stripe / name badge ────────────────────────
        pygame.draw.rect(surface, C_WHITE, (cx - 14, cy + 4, 28, 7), border_radius=2)
        f = pygame.font.SysFont("georgia,serif", 7, bold=True)
        t = f.render("POLICE", True, (20, 20, 80))
        surface.blit(t, (cx - t.get_width() // 2, cy + 5))

        # ── Bow wave foam ─────────────────────────────────────
        for side in (-1, 1):
            foam = pygame.Surface((16, 8), pygame.SRCALPHA)
            pygame.draw.ellipse(foam, (200, 230, 255, 60), foam.get_rect())
            surface.blit(foam, (cx + side * 14, cy - 30))


# ── PirateShip ───────────────────────────────────────────────
class PirateShip:
    """
    2-lane wide enemy ship that approaches from below (upward movement).
    Drawn top-down — bow points toward the player (upward on screen).
    Unlocked after 2 km. Shield absorbs one hit; unshielded = game over.
    """
    DRAW_W = 112
    DRAW_H = 128
    HIT_W  = 94
    HIT_H  = 76

    def __init__(self, lane_left: int):
        ll = max(0, min(lane_left, LANE_COUNT - 2))
        self.lane_l = ll
        self.lane_r = ll + 1
        self.x = float((LANES[ll] + LANES[ll + 1]) // 2)
        self.y = float(SCREEN_H + self.DRAW_H // 2 + 20)

    @property
    def rect(self):
        return pygame.Rect(
            int(self.x) - self.HIT_W // 2,
            int(self.y) - self.HIT_H // 2,
            self.HIT_W, self.HIT_H,
        )

    def move(self, player_speed: float, dt: int):
        self.y -= player_speed * 0.42 * (dt / 16.67)

    def is_offscreen(self):
        return self.y < -(self.DRAW_H // 2 + 30)

    def draw(self, surface, tick: int):
        px, py = int(self.x), int(self.y)
        W, H = self.DRAW_W, self.DRAW_H

        # Pulsing red warning glow
        pulse = (math.sin(tick * 0.09) + 1) * 0.5
        ga = int(38 + pulse * 52)
        gs = pygame.Surface((W + 44, H + 44), pygame.SRCALPHA)
        pygame.draw.ellipse(gs, (200, 20, 20, ga), (0, 0, W + 44, H + 44))
        surface.blit(gs, (px - W // 2 - 22, py - H // 2 - 22))

        # Hull — dark crimson, top-down elongated shape
        hull_col = (68, 15, 15)
        hull_pts = [
            (px,           py - H // 2),        # bow (front/top)
            (px + W // 2,  py - H // 6),        # right shoulder
            (px + W // 2,  py + H // 4),        # right beam
            (px + W // 3,  py + H // 2),        # right stern quarter
            (px - W // 3,  py + H // 2),        # left stern quarter
            (px - W // 2,  py + H // 4),        # left beam
            (px - W // 2,  py - H // 6),        # left shoulder
        ]
        pygame.draw.polygon(surface, hull_col, hull_pts)
        pygame.draw.polygon(surface, (130, 28, 28), hull_pts, 2)

        # Wood plank grain lines
        for i in range(4):
            frac = 0.45 + i * 0.10
            ry = py - H // 3 + i * (H // 6)
            pygame.draw.line(surface, (52, 12, 12),
                             (int(px - W // 2 * frac), ry),
                             (int(px + W // 2 * frac), ry), 1)

        # Deck highlight (central raised area)
        deck = [
            (px,           py - H // 2 + 14),
            (px + W // 3,  py - H // 6 + 6),
            (px + W // 3,  py + H // 5),
            (px - W // 3,  py + H // 5),
            (px - W // 3,  py - H // 6 + 6),
        ]
        pygame.draw.polygon(surface, (82, 20, 20), deck)

        # Forward mast (circle top-down)
        pygame.draw.circle(surface, (28, 13, 5),  (px, py - H // 7), 8)
        pygame.draw.circle(surface, (48, 22, 8),  (px, py - H // 7), 8, 2)
        # Aft mast
        pygame.draw.circle(surface, (28, 13, 5),  (px, py + H // 6), 6)
        pygame.draw.circle(surface, (48, 22, 8),  (px, py + H // 6), 6, 2)

        # Skull flag at forward mast
        fx, fy = px + 11, py - H // 7 - 18
        pygame.draw.rect(surface, (8, 8, 8), (fx, fy, 24, 17))
        pygame.draw.circle(surface, (205, 205, 205), (fx + 9, fy + 8), 5)
        pygame.draw.line(surface, (205, 205, 205), (fx + 3, fy + 3), (fx + 21, fy + 14), 1)
        pygame.draw.line(surface, (205, 205, 205), (fx + 21, fy + 3), (fx + 3, fy + 14), 1)
        pygame.draw.rect(surface, (160, 20, 20), (fx, fy, 24, 17), 1)

        # Cannons — 2 per side
        for side in (-1, 1):
            for ci in range(2):
                cx_ = px + side * (W // 2 - 2)
                cy_ = py - H // 10 + ci * (H // 6)
                bx_ = cx_ - 12 if side < 0 else cx_
                pygame.draw.rect(surface, (22, 22, 24), (bx_, cy_ - 5, 14, 10), border_radius=3)
                pygame.draw.circle(surface, (14, 14, 16), (cx_, cy_), 5)

        # Bow wake foam
        for side in (-1, 1):
            foam = pygame.Surface((18, 7), pygame.SRCALPHA)
            pygame.draw.ellipse(foam, (190, 225, 255, 65), foam.get_rect())
            surface.blit(foam, (px + side * 10 - 9, py - H // 2 - 5))


# ── GiantFish ────────────────────────────────────────────────
class GiantFish:
    """
    3-lane wide leviathan that bursts from below with a bubble warning.
    Warning phase: bubbles visible at screen bottom for WARN_MS ms.
    Rising phase: body rushes upward — collision is instant kill.
    """
    WARN_MS = 2600
    DRAW_W  = 228
    DRAW_H  = 96
    HIT_W   = 198
    HIT_H   = 68

    def __init__(self, center_lane: int):
        self.x       = float(LANES[center_lane])
        self.y       = float(SCREEN_H + self.DRAW_H + 10)
        self.warn_ms = float(self.WARN_MS)
        self.phase   = "warning"   # "warning" | "rising"
        self._bub    = [
            (random.uniform(-88, 88), random.uniform(0.09, 0.21), random.uniform(3, 8))
            for _ in range(14)
        ]

    @property
    def rect(self):
        if self.phase != "rising":
            return pygame.Rect(0, 0, 0, 0)
        return pygame.Rect(
            int(self.x) - self.HIT_W // 2,
            int(self.y) - self.HIT_H // 2,
            self.HIT_W, self.HIT_H,
        )

    def update(self, dt: int):
        if self.phase == "warning":
            self.warn_ms -= dt
            if self.warn_ms <= 0:
                self.phase = "rising"
        else:
            self.y -= 22 * (dt / 16.67)

    def is_offscreen(self):
        return self.y < -(self.DRAW_H + 30)

    def draw(self, surface, tick: int):
        if self.phase == "warning":
            self._draw_warning(surface, tick)
        else:
            self._draw_fish(surface, tick)

    def _draw_warning(self, surface, tick):
        progress = 1.0 - self.warn_ms / self.WARN_MS
        bx = int(self.x)

        # Expanding shimmer band at screen bottom
        alpha = int(22 + progress * 55)
        ws = pygame.Surface((self.DRAW_W + 30, 58), pygame.SRCALPHA)
        ws.fill((50, 130, 220, alpha // 2))
        surface.blit(ws, (bx - (self.DRAW_W + 30) // 2, SCREEN_H - 60))
        lw = max(1, int(progress * 3))
        pygame.draw.line(surface, (70, 170, 255),
                         (bx - self.DRAW_W // 2, SCREEN_H - 60),
                         (bx + self.DRAW_W // 2, SCREEN_H - 60), lw)

        # Rising bubbles
        for (boff, speed_f, base_r) in self._bub:
            offset_y = (tick * speed_f * 2.4) % 66
            bx_ = int(bx + boff)
            by_ = int(SCREEN_H - 8 - offset_y)
            if SCREEN_H - 70 < by_ <= SCREEN_H:
                r = max(2, int(base_r * (0.5 + progress * 0.7)))
                ba = int(95 + progress * 140)
                bs = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(bs, (120, 205, 255, min(255, ba)),
                                   (r + 1, r + 1), r, 1)
                surface.blit(bs, (bx_ - r - 1, by_ - r - 1))

        # Warning text (appears after 40% of warning elapsed)
        if progress > 0.38:
            wf = pygame.font.SysFont("consolas,monospace", 13, bold=True)
            wt = wf.render("!! LEVIATHAN !!", True, (70, 195, 255))
            wt.set_colorkey((0, 0, 0))
            tmp = pygame.Surface(wt.get_size(), pygame.SRCALPHA)
            tmp.blit(wt, (0, 0))
            tmp.set_alpha(int(220 * min(1.0, (progress - 0.38) / 0.4)))
            surface.blit(tmp, (bx - tmp.get_width() // 2, SCREEN_H - 86))

    def _draw_fish(self, surface, tick):
        px, py = int(self.x), int(self.y)
        W, H = self.DRAW_W, self.DRAW_H

        # Blue-green glow
        gs = pygame.Surface((W + 34, H + 34), pygame.SRCALPHA)
        pygame.draw.ellipse(gs, (28, 135, 215, 65), (0, 0, W + 34, H + 34))
        surface.blit(gs, (px - W // 2 - 17, py - H // 2 - 17))

        # Main body — top-down oval (fish seen from above)
        body_col = (14, 76, 138)
        pygame.draw.ellipse(surface, body_col,
                            pygame.Rect(px - W // 2, py - H // 2, W, H))
        # Belly lighter stripe
        pygame.draw.ellipse(surface, (18, 108, 178),
                            pygame.Rect(px - W // 3, py - H // 4, W * 2 // 3, H // 2))
        pygame.draw.ellipse(surface, (9, 52, 98),
                            pygame.Rect(px - W // 2, py - H // 2, W, H), 2)

        # Eye (right side — fish faces right = "front/bow")
        pygame.draw.circle(surface, (235, 235, 235), (px + W // 3, py - H // 7), 13)
        pygame.draw.circle(surface, (8,   8,   8),   (px + W // 3 + 2, py - H // 7), 8)
        pygame.draw.circle(surface, (255, 255, 255), (px + W // 3 + 5, py - H // 7 - 4), 3)

        # Open mouth at the bow (right side)
        mx = px + W // 2 - 14
        pygame.draw.polygon(surface, (8, 8, 8), [
            (mx + 12, py - 18), (mx + 26, py), (mx + 12, py + 18)])
        for i in range(4):
            ty = py - 15 + i * 8
            pygame.draw.polygon(surface, (225, 225, 225), [
                (mx + 10, ty), (mx + 17, ty), (mx + 13, ty + 6)])

        # Tail fin (left side)
        pygame.draw.polygon(surface, (11, 62, 112), [
            (px - W // 2,      py),
            (px - W // 2 - 34, py - 38),
            (px - W // 2 - 34, py + 38),
        ])

        # Dorsal fin (top of fish = top of screen from above)
        pygame.draw.polygon(surface, (11, 62, 112), [
            (px - W // 6,  py - H // 2),
            (px + W // 6,  py - H // 2),
            (px,           py - H // 2 - 32),
        ])

        # Pectoral fins (both sides)
        for side in (-1, 1):
            pygame.draw.polygon(surface, (11, 62, 112), [
                (px - W // 5,  py + side * H // 2),
                (px + W // 5,  py + side * H // 2),
                (px,           py + side * (H // 2 + 30)),
            ])

        # Scale arc highlights
        for i in range(-2, 3):
            for j in (-1, 0):
                sx = px + i * (W // 8)
                sy = py + j * (H // 4)
                pygame.draw.arc(surface, (17, 88, 152),
                                pygame.Rect(sx - 14, sy - 10, 28, 20),
                                0, math.pi, 1)
