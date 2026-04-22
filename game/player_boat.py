"""
player_boat.py - PlayerBoat class (multi-boat support)
"""

import pygame
import math
from .constants import (
    LANES, LANE_COUNT, PLAYER_W, PLAYER_H, PLAYER_Y, PLAYER_MOVE_COOLDOWN,
    C_WOOD, C_WOOD_DARK, C_OCEAN_FOAM, C_GOLD, C_WHITE,
    PU_SHIELD_DURATION, PU_SPEED_DURATION, PU_MAGNET_DURATION, PU_DOUBLE_DURATION,
    BOAT_BY_ID,
)


class PlayerBoat:
    def __init__(self, boat_id: str = "starter",
                 hull_color: tuple = None, sail_color: tuple = None):
        self.boat_id   = boat_id
        self.boat_data = BOAT_BY_ID.get(boat_id, BOAT_BY_ID["starter"])
        ab             = self.boat_data["abilities"]

        self.lane: int     = 2
        self.x: float      = float(LANES[self.lane])
        self.y: float      = float(PLAYER_Y)
        self.target_x: float = self.x
        self.w: int        = PLAYER_W
        self.h: int        = PLAYER_H

        # Colors (use provided or first palette option)
        hp = self.boat_data.get("hull_palette")
        sp = self.boat_data.get("sail_palette")
        self.hull_color = hull_color if hull_color else (hp[0] if hp else C_WOOD)
        self.sail_color = sail_color if sail_color else (sp[0] if sp else (245, 238, 215))

        # Stat modifiers from boat abilities
        self._move_cd_bonus  = ab.get("move_cooldown_bonus", 0)
        self.hitbox_shrink   = ab.get("hitbox_shrink", 1.0)
        self.magnet_bonus    = ab.get("magnet_bonus", 0)
        self.coin_multiplier = ab.get("coin_multiplier", 1.0)
        self.speed_threshold_bonus = ab.get("speed_threshold_bonus", 0.0)

        # Powerup timers (ms remaining)
        self.shield_timer: int = 0
        self.speed_timer:  int = 0
        self.magnet_timer: int = 0
        self.double_timer: int = 0

        self._move_cooldown: int = 0

    # ── Properties ──────────────────────────────────────────
    @property
    def move_cooldown_ms(self) -> int:
        return max(60, PLAYER_MOVE_COOLDOWN + self._move_cd_bonus)

    @property
    def shield(self) -> bool:      return self.shield_timer > 0
    @property
    def speed_boost(self) -> bool: return self.speed_timer  > 0
    @property
    def magnet(self) -> bool:      return self.magnet_timer > 0
    @property
    def double_coins(self) -> bool:return self.double_timer > 0

    @property
    def rect(self) -> pygame.Rect:
        hw = int(self.w * 0.68 * self.hitbox_shrink) // 2
        hh = int(self.h * 0.60 * self.hitbox_shrink) // 2
        return pygame.Rect(int(self.x) - hw, int(self.y) - hh, hw*2, hh*2)

    # ── Movement ─────────────────────────────────────────────
    def move_left(self) -> bool:
        if self._move_cooldown <= 0 and self.lane > 0:
            self.lane -= 1
            self.target_x = float(LANES[self.lane])
            self._move_cooldown = self.move_cooldown_ms
            return True
        return False

    def move_right(self) -> bool:
        if self._move_cooldown <= 0 and self.lane < LANE_COUNT - 1:
            self.lane += 1
            self.target_x = float(LANES[self.lane])
            self._move_cooldown = self.move_cooldown_ms
            return True
        return False

    # ── Powerups ─────────────────────────────────────────────
    def activate_shield(self):  self.shield_timer = PU_SHIELD_DURATION
    def activate_speed(self):   self.speed_timer  = PU_SPEED_DURATION
    def activate_magnet(self):  self.magnet_timer = PU_MAGNET_DURATION
    def activate_double(self):  self.double_timer = PU_DOUBLE_DURATION

    def get_active_powerups(self) -> list:
        out = []
        if self.shield:       out.append("SHIELD")
        if self.speed_boost:  out.append("SPEED")
        if self.magnet:       out.append("MAGNET")
        if self.double_coins: out.append("x2 COINS")
        return out

    # ── Update ───────────────────────────────────────────────
    def update(self, dt: int):
        self.x += (self.target_x - self.x) * 0.18
        if self._move_cooldown > 0: self._move_cooldown -= dt
        if self.shield_timer  > 0: self.shield_timer  = max(0, self.shield_timer  - dt)
        if self.speed_timer   > 0: self.speed_timer   = max(0, self.speed_timer   - dt)
        if self.magnet_timer  > 0: self.magnet_timer  = max(0, self.magnet_timer  - dt)
        if self.double_timer  > 0: self.double_timer  = max(0, self.double_timer  - dt)

    # ── Draw dispatcher ──────────────────────────────────────
    def draw(self, surface: pygame.Surface, tick: int):
        _DRAW = {
            "starter": _draw_starter,
            "sloop":   _draw_sloop,
            "galleon": _draw_galleon,
            "manowar": _draw_manowar,
        }
        fn = _DRAW.get(self.boat_id, _draw_starter)
        cx, cy = int(self.x), int(self.y)
        w, h   = self.w, self.h
        bob    = math.sin(tick * 0.04) * 1.5
        sway   = math.sin(tick * 0.03) * 0.06
        cy_b   = cy + int(bob)

        # Shield aura (all boats)
        if self.shield:
            for ring_i, base_r in enumerate((38, 44)):
                alpha = int(90 - ring_i*30 + 35 * math.sin(tick * 0.015 + ring_i))
                s = pygame.Surface((100, 100), pygame.SRCALPHA)
                pygame.draw.circle(s, (*C_OCEAN_FOAM, max(0, alpha)),
                                   (50, 50), base_r, 2)
                surface.blit(s, (cx - 50, cy_b - 50))

        fn(surface, cx, cy_b, w, h, tick, sway, self.hull_color, self.sail_color)


# ────────────────────────────────────────────────────────────
# BOAT DRAW FUNCTIONS
# ────────────────────────────────────────────────────────────

def _wake(surface, cx, cy_b, h):
    for i, (dx, sz) in enumerate([(8, 22), (18, 14), (26, 8)]):
        alpha = 90 - i*25
        wk = pygame.Surface((sz*2, sz), pygame.SRCALPHA)
        pygame.draw.ellipse(wk, (220, 240, 255, max(0, alpha)), (0, 0, sz*2, sz))
        surface.blit(wk, (cx - sz, cy_b + h//3 + dx))


def _hull_shadow(surface, cx, cy_b, w, h):
    sh = pygame.Surface((w+10, h//3), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 70), sh.get_rect())
    surface.blit(sh, (cx - (w+10)//2, cy_b + h//3 - 4))


# ── Starter: Driftwood ──────────────────────────────────────
def _draw_starter(surface, cx, cy_b, w, h, tick, sway, hull_color, sail_color):
    _wake(surface, cx, cy_b, h)
    _hull_shadow(surface, cx, cy_b, w, h)

    WOOD    = hull_color
    WOOD_DK = tuple(max(0, c - 40) for c in WOOD)
    SAIL    = sail_color

    hull_outer = [
        (cx - w//2 + 2,  cy_b - h//3),
        (cx - w//2 - 3,  cy_b + h//6),
        (cx - w//3,      cy_b + h//2 - 2),
        (cx + w//3,      cy_b + h//2 - 2),
        (cx + w//2 + 3,  cy_b + h//6),
        (cx + w//2 - 2,  cy_b - h//3),
        (cx + 4,         cy_b - h//2 + 2),
        (cx - 4,         cy_b - h//2 + 2),
    ]
    pygame.draw.polygon(surface, WOOD, hull_outer)
    pygame.draw.polygon(surface, WOOD_DK, hull_outer, 2)
    pygame.draw.line(surface, (210, 170, 70),
                     (cx - w//2 + 4, cy_b - h//4 + 2),
                     (cx + w//2 - 4, cy_b - h//4 + 2), 2)
    for offset in (-w//3, -w//9, w//9, w//3):
        pygame.draw.line(surface, WOOD_DK,
                         (cx + offset, cy_b - h//3 + 5),
                         (cx + offset, cy_b + h//3 - 5), 1)
    deck = pygame.Rect(cx - w//2 + 8, cy_b - h//5, w - 16, h//3)
    pygame.draw.rect(surface, (165, 120, 72), deck, border_radius=3)
    pygame.draw.rect(surface, WOOD_DK, deck, 1, border_radius=3)
    for cx_off in (-w//2 + 2, w//2 - 2):
        pygame.draw.circle(surface, (60, 60, 60), (cx + cx_off, cy_b + 4), 3)

    mast_top_y = cy_b - h//2 - 16
    pygame.draw.line(surface, WOOD_DK, (cx, cy_b - h//5), (cx, mast_top_y), 3)
    pygame.draw.line(surface, WOOD_DK,
                     (cx - w//2 + 6, cy_b - h//3 - 2),
                     (cx + w//2 - 6, cy_b - h//3 - 2), 2)
    top_x = cx + int(math.sin(sway) * 4)
    sail_pts = [
        (top_x,           mast_top_y + 4),
        (cx + w//2 - 4,   cy_b - h//3 + 2),
        (cx + w//3,       cy_b - h//5),
        (cx - w//3,       cy_b - h//5),
        (cx - w//2 + 4,   cy_b - h//3 + 2),
    ]
    pygame.draw.polygon(surface, SAIL, sail_pts)
    pygame.draw.polygon(surface, tuple(max(0,c-60) for c in SAIL), sail_pts, 1)
    sf = pygame.font.SysFont("consolas,monospace", 14, bold=True)
    sk_s = sf.render("☠", True, (30, 30, 30))
    if sk_s.get_width() < 4:
        sk_s = sf.render("X", True, (30, 30, 30))
    surface.blit(sk_s, (cx - sk_s.get_width()//2, cy_b - h//3 + 2))
    flag_wave = int(math.sin(tick * 0.12) * 2)
    pygame.draw.polygon(surface, (20, 20, 20), [
        (top_x,      mast_top_y),
        (top_x + 14, mast_top_y + 3 + flag_wave),
        (top_x + 12, mast_top_y + 7 + flag_wave),
        (top_x,      mast_top_y + 10),
    ])
    bw = pygame.Surface((w, 8), pygame.SRCALPHA)
    pygame.draw.ellipse(bw, (255, 255, 255, 150), (0, 0, w, 8))
    surface.blit(bw, (cx - w//2, cy_b - h//2 - 4))


# ── Sloop: Sea Breeze ───────────────────────────────────────
def _draw_sloop(surface, cx, cy_b, w, h, tick, sway, hull_color, sail_color):
    _wake(surface, cx, cy_b, h)
    _hull_shadow(surface, cx, cy_b, w, h)

    HULL  = hull_color
    HULLD = tuple(max(0, c - 50) for c in HULL)
    SAIL  = (240, 248, 255)   # sloop always white sail

    # Narrower, sleeker hull
    hull_pts = [
        (cx,          cy_b - h//2 + 2),   # sharp bow
        (cx + w//2,   cy_b - h//6),
        (cx + w//2-2, cy_b + h//3),
        (cx + w//4,   cy_b + h//2 - 4),
        (cx - w//4,   cy_b + h//2 - 4),
        (cx - w//2+2, cy_b + h//3),
        (cx - w//2,   cy_b - h//6),
    ]
    pygame.draw.polygon(surface, HULL, hull_pts)
    pygame.draw.polygon(surface, HULLD, hull_pts, 2)

    # Waterline stripe
    pygame.draw.line(surface, (200, 220, 255),
                     (cx - w//2 + 4, cy_b + h//4),
                     (cx + w//2 - 4, cy_b + h//4), 2)

    # Thin single mast
    mast_top = cy_b - h//2 - 22
    pygame.draw.line(surface, HULLD, (cx, cy_b - h//4), (cx, mast_top), 2)

    # Triangular jib sail (fore-sail)
    jib_pts = [
        (cx,      mast_top + 2),
        (cx + w//2 - 6, cy_b - h//6),
        (cx,      cy_b - h//6),
    ]
    jib = pygame.Surface((w, h), pygame.SRCALPHA)
    jib_pts_local = [(p[0] - cx + w//2, p[1] - cy_b + h//2) for p in jib_pts]
    pygame.draw.polygon(jib, (*SAIL, 180), jib_pts_local)
    surface.blit(jib, (cx - w//2, cy_b - h//2))
    pygame.draw.polygon(surface, tuple(max(0,c-40) for c in SAIL), jib_pts, 1)

    # Main sail (small, boom out)
    boom_x = cx - int(math.sin(sway) * 6)
    main_pts = [
        (cx,      mast_top + 8),
        (cx - w//2 + 4,  cy_b - h//4),
        (boom_x,  cy_b - h//8),
    ]
    pygame.draw.polygon(surface, SAIL, main_pts)
    pygame.draw.polygon(surface, tuple(max(0,c-50) for c in SAIL), main_pts, 1)

    # Speed lines on hull
    for i in range(3):
        lx1 = cx - w//3 + i*8
        pygame.draw.line(surface, (200, 220, 255),
                         (lx1, cy_b - h//8), (lx1 + 14, cy_b + h//5), 1)

    # Small flag
    flag_wave = int(math.sin(tick * 0.14) * 2)
    pygame.draw.polygon(surface, HULL, [
        (cx,     mast_top),
        (cx+12,  mast_top + 3 + flag_wave),
        (cx+10,  mast_top + 7 + flag_wave),
        (cx,     mast_top + 10),
    ])

    bw = pygame.Surface((w, 6), pygame.SRCALPHA)
    pygame.draw.ellipse(bw, (255, 255, 255, 120), (0, 0, w, 6))
    surface.blit(bw, (cx - w//2, cy_b - h//2 - 2))


# ── Galleon: Iron Tide ──────────────────────────────────────
def _draw_galleon(surface, cx, cy_b, w, h, tick, sway, hull_color, sail_color):
    _wake(surface, cx, cy_b, h)
    _hull_shadow(surface, cx, cy_b, w, h)

    HULL  = (55, 50, 40)       # iron-grey wood
    HULLD = (30, 28, 22)
    METAL = (100, 100, 110)
    SAIL  = sail_color

    # Wide armored hull
    hull_pts = [
        (cx - w//2 + 2,  cy_b - h//3 + 2),
        (cx - w//2 - 6,  cy_b + h//8),
        (cx - w//3,      cy_b + h//2),
        (cx + w//3,      cy_b + h//2),
        (cx + w//2 + 6,  cy_b + h//8),
        (cx + w//2 - 2,  cy_b - h//3 + 2),
        (cx + 5,         cy_b - h//2 + 4),
        (cx - 5,         cy_b - h//2 + 4),
    ]
    pygame.draw.polygon(surface, HULL, hull_pts)
    pygame.draw.polygon(surface, HULLD, hull_pts, 3)

    # Iron band stripes
    for oy in (-h//4, 0, h//6):
        clip = max(2, int(22 * (1 - abs(oy) / (h//2))))
        pygame.draw.line(surface, METAL,
                         (cx - w//2 + 2, cy_b + oy),
                         (cx + w//2 - 2, cy_b + oy), 1)

    # Cannon ports (3 per side)
    for side in (-1, 1):
        for oy in (-h//5, 0, h//5):
            px = cx + side * (w//2 - 2)
            pygame.draw.circle(surface, (20, 20, 20), (px, cy_b + oy), 4)
            pygame.draw.circle(surface, METAL, (px, cy_b + oy), 4, 1)

    # Armored prow plate
    prow = [(cx - 8, cy_b - h//2 + 4), (cx + 8, cy_b - h//2 + 4),
            (cx + 4, cy_b - h//2 - 6), (cx - 4, cy_b - h//2 - 6)]
    pygame.draw.polygon(surface, METAL, prow)

    # Two masts
    for mx in (-w//5, w//5):
        mast_top = cy_b - h//2 - 18
        pygame.draw.line(surface, HULLD, (cx + mx, cy_b - h//5),
                         (cx + mx, mast_top), 2)
        # Crossbeam
        pygame.draw.line(surface, HULLD,
                         (cx + mx - w//3, cy_b - h//3),
                         (cx + mx + w//3, cy_b - h//3), 2)
        # Sail panel
        top_x = cx + mx + int(math.sin(sway) * 3)
        sp = [
            (top_x,           mast_top + 4),
            (cx + mx + w//3 - 4, cy_b - h//3 + 2),
            (cx + mx + w//4,  cy_b - h//5),
            (cx + mx - w//4,  cy_b - h//5),
            (cx + mx - w//3 + 4, cy_b - h//3 + 2),
        ]
        pygame.draw.polygon(surface, SAIL, sp)
        pygame.draw.polygon(surface, tuple(max(0,c-50) for c in SAIL), sp, 1)

    # Iron flag (skull on metal)
    flag_wave = int(math.sin(tick * 0.10) * 2)
    mast_top = cy_b - h//2 - 18
    pygame.draw.polygon(surface, METAL, [
        (cx,     mast_top),
        (cx+14,  mast_top + 3 + flag_wave),
        (cx+12,  mast_top + 8 + flag_wave),
        (cx,     mast_top + 11),
    ])
    sf = pygame.font.SysFont("consolas,monospace", 9, bold=True)
    sk = sf.render("☠", True, HULLD)
    if sk.get_width() < 4:
        sk = sf.render("X", True, HULLD)
    surface.blit(sk, (cx + 2, mast_top + 1))

    bw = pygame.Surface((w + 8, 10), pygame.SRCALPHA)
    pygame.draw.ellipse(bw, (255, 255, 255, 130), (0, 0, w+8, 10))
    surface.blit(bw, (cx - (w+8)//2, cy_b - h//2 - 5))


# ── Man-o-War: Crimson Storm ────────────────────────────────
def _draw_manowar(surface, cx, cy_b, w, h, tick, sway, hull_color, sail_color):
    _wake(surface, cx, cy_b, h)
    _hull_shadow(surface, cx, cy_b, w, h)

    HULL  = hull_color
    HULLD = tuple(max(0, c - 55) for c in HULL)
    GOLD  = (210, 168, 60)
    SAIL  = sail_color

    # Massive hull
    hull_pts = [
        (cx - w//2 + 4,  cy_b - h//3),
        (cx - w//2 - 8,  cy_b + h//10),
        (cx - w//3 - 2,  cy_b + h//2 + 2),
        (cx + w//3 + 2,  cy_b + h//2 + 2),
        (cx + w//2 + 8,  cy_b + h//10),
        (cx + w//2 - 4,  cy_b - h//3),
        (cx + 6,         cy_b - h//2 + 2),
        (cx - 6,         cy_b - h//2 + 2),
    ]
    pygame.draw.polygon(surface, HULL, hull_pts)
    pygame.draw.polygon(surface, HULLD, hull_pts, 3)

    # Gold trim (3 stripes)
    for oy in (-h//3 + 6, -h//8, h//8):
        clip_l = cx - w//2 + max(2, int(8 * abs(oy)//h))
        clip_r = cx + w//2 - max(2, int(8 * abs(oy)//h))
        pygame.draw.line(surface, GOLD, (clip_l, cy_b + oy), (clip_r, cy_b + oy), 2)

    # Cannon ports (4 per side)
    for side in (-1, 1):
        for oy in (-h//4, -h//9, h//9, h//4):
            px = cx + side * (w//2 + 2)
            cannon = pygame.Rect(px - 5 if side < 0 else px, cy_b + oy - 3, 7, 6)
            pygame.draw.rect(surface, (20, 20, 20), cannon, border_radius=1)
            pygame.draw.rect(surface, GOLD, cannon, 1, border_radius=1)

    # Stern cabin
    cabin_rect = pygame.Rect(cx - w//2 + 6, cy_b - h//4, w - 12, h//3 - 2)
    pygame.draw.rect(surface, tuple(max(0,c-20) for c in HULL), cabin_rect, border_radius=4)
    pygame.draw.rect(surface, GOLD, cabin_rect, 2, border_radius=4)
    # Cabin windows (3 round portholes)
    for px in (-w//4, 0, w//4):
        pygame.draw.circle(surface, (180, 210, 240), (cx + px, cy_b - h//8), 4)
        pygame.draw.circle(surface, GOLD, (cx + px, cy_b - h//8), 4, 1)

    # Three tall masts
    mast_tops = []
    for mx, height_extra in ((-w//3, 10), (0, 20), (w//3, 10)):
        mt = cy_b - h//2 - 14 - height_extra
        mast_tops.append((cx + mx, mt))
        pygame.draw.line(surface, HULLD, (cx + mx, cy_b - h//5),
                         (cx + mx, mt), 3)
        pygame.draw.line(surface, HULLD,
                         (cx + mx - w//3 + 4, cy_b - h//3),
                         (cx + mx + w//3 - 4, cy_b - h//3), 2)
        top_x = cx + mx + int(math.sin(sway + mx * 0.02) * 4)
        sp = [
            (top_x,              mt + 4),
            (cx + mx + w//3 - 6, cy_b - h//3 + 2),
            (cx + mx + w//4,     cy_b - h//5),
            (cx + mx - w//4,     cy_b - h//5),
            (cx + mx - w//3 + 6, cy_b - h//3 + 2),
        ]
        pygame.draw.polygon(surface, SAIL, sp)
        pygame.draw.polygon(surface, tuple(max(0,c-60) for c in SAIL), sp, 1)

    # Crimson war flag on centre mast
    mt_cx, mt_cy = mast_tops[1]
    flag_wave = int(math.sin(tick * 0.11) * 3)
    pygame.draw.polygon(surface, (200, 20, 20), [
        (mt_cx,     mt_cy),
        (mt_cx+16,  mt_cy + 4 + flag_wave),
        (mt_cx+14,  mt_cy + 9 + flag_wave),
        (mt_cx,     mt_cy + 13),
    ])
    sf = pygame.font.SysFont("consolas,monospace", 9, bold=True)
    sk = sf.render("☠", True, GOLD)
    if sk.get_width() < 4:
        sk = sf.render("X", True, GOLD)
    surface.blit(sk, (mt_cx + 2, mt_cy + 1))

    # Glow aura (legendary effect)
    pulse = int(8 + 5 * math.sin(tick * 0.018))
    glow = pygame.Surface((w + pulse*2 + 20, h + pulse*2), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (*HULL, 18),
                        (0, 0, w + pulse*2 + 20, h + pulse*2))
    surface.blit(glow, (cx - (w + pulse*2 + 20)//2, cy_b - (h + pulse*2)//2))

    bw = pygame.Surface((w + 12, 12), pygame.SRCALPHA)
    pygame.draw.ellipse(bw, (255, 255, 255, 160), (0, 0, w+12, 12))
    surface.blit(bw, (cx - (w+12)//2, cy_b - h//2 - 6))
