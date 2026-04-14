"""
player_boat.py - PlayerBoat class
"""

import pygame
import math
from constants import (
    LANES, LANE_COUNT, PLAYER_W, PLAYER_H, PLAYER_Y, PLAYER_MOVE_COOLDOWN,
    C_WOOD, C_WOOD_DARK, C_OCEAN_FOAM,
    PU_SHIELD_DURATION, PU_SPEED_DURATION, PU_MAGNET_DURATION, PU_DOUBLE_DURATION,
)


class PlayerBoat:
    def __init__(self):
        self.lane: int     = 2
        self.x: float      = float(LANES[self.lane])
        self.y: float      = float(PLAYER_Y)
        self.target_x: float = self.x
        self.w: int        = PLAYER_W
        self.h: int        = PLAYER_H

        # Powerup timers (ms remaining)
        self.shield_timer: int = 0
        self.speed_timer:  int = 0
        self.magnet_timer: int = 0
        self.double_timer: int = 0

        self._move_cooldown: int = 0

    # ── Properties ──────────────────────────────────────────
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
        hw = int(self.w * 0.68) // 2
        hh = int(self.h * 0.60) // 2
        return pygame.Rect(int(self.x) - hw, int(self.y) - hh, hw*2, hh*2)

    # ── Movement ─────────────────────────────────────────────
    def move_left(self) -> bool:
        if self._move_cooldown <= 0 and self.lane > 0:
            self.lane -= 1
            self.target_x = float(LANES[self.lane])
            self._move_cooldown = PLAYER_MOVE_COOLDOWN
            return True
        return False

    def move_right(self) -> bool:
        if self._move_cooldown <= 0 and self.lane < LANE_COUNT - 1:
            self.lane += 1
            self.target_x = float(LANES[self.lane])
            self._move_cooldown = PLAYER_MOVE_COOLDOWN
            return True
        return False

    # ── Powerups ─────────────────────────────────────────────
    def activate_shield(self):  self.shield_timer = PU_SHIELD_DURATION
    def activate_speed(self):   self.speed_timer  = PU_SPEED_DURATION
    def activate_magnet(self):  self.magnet_timer = PU_MAGNET_DURATION
    def activate_double(self):  self.double_timer = PU_DOUBLE_DURATION

    def get_active_powerups(self) -> list[str]:
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

    # ── Draw ─────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface, tick: int):
        cx, cy = int(self.x), int(self.y)

        # Shield aura
        if self.shield:
            alpha = int(80 + 40 * math.sin(tick * 0.015))
            s = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C_OCEAN_FOAM, alpha), (40, 40), 36, 3)
            surface.blit(s, (cx - 40, cy - 40))

        # Wake trail
        wk = pygame.Surface((30, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(wk, (200, 230, 255, 30), (0, 0, 30, 50))
        surface.blit(wk, (cx - 15, cy + 20))

        # Hull
        hull_pts = [
            (cx - self.w//2 + 4, cy - self.h//3),
            (cx - self.w//2,     cy + self.h//3),
            (cx + self.w//2,     cy + self.h//3),
            (cx + self.w//2 - 4, cy - self.h//3),
            (cx,                 cy - self.h//2 - 4),
        ]
        pygame.draw.polygon(surface, C_WOOD, hull_pts)
        pygame.draw.polygon(surface, C_WOOD_DARK, hull_pts, 2)

        for offset in (-self.w//3, 0, self.w//3):
            pygame.draw.line(surface, C_WOOD_DARK,
                             (cx + offset, cy - self.h//3 + 4),
                             (cx + offset, cy + self.h//3 - 4), 1)

        # Deck
        pygame.draw.rect(surface, (155, 107, 62),
                         (cx - self.w//2 + 6, cy - self.h//4, self.w - 12, self.h//2))

        # Mast
        pygame.draw.line(surface, C_WOOD_DARK,
                         (cx, cy - self.h//4), (cx, cy - self.h//2 - 10), 3)

        # Sail
        sail_pts = [
            (cx,              cy - self.h//2 - 8),
            (cx + self.w//2 - 2, cy - self.h//3 + 4),
            (cx,              cy - self.h//4 + 2),
        ]
        pygame.draw.polygon(surface, (240, 232, 208), sail_pts)
        pygame.draw.polygon(surface, (200, 184, 152), sail_pts, 1)

        # Skull on sail
        f = pygame.font.SysFont("segoeuisymbol,symbola,seguiemj", 12)
        sk = f.render("X", True, (60, 60, 60))
        surface.blit(sk, (cx + 4, cy - self.h//3 + 5))

        # Flag
        pygame.draw.polygon(surface, (20, 20, 20), [
            (cx,      cy - self.h//2 - 8),
            (cx + 12, cy - self.h//2 - 2),
            (cx,      cy - self.h//2 + 4),
        ])
