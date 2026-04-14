"""
objects.py - Game object classes
"""

import pygame
import random
import math
from constants import (
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
        sh = pygame.Surface((int(self.size*1.6), int(self.size*0.6)), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0,0,0,60), sh.get_rect())
        surface.blit(sh, (cx-int(self.size*0.8)+2, cy+int(self.size*0.35)))
        pts = [(cx+px, cy+py) for px,py in self.points_rel]
        pygame.draw.polygon(surface, self.color, pts)
        hl = pygame.Surface((int(self.size*0.8), int(self.size*0.5)), pygame.SRCALPHA)
        pygame.draw.ellipse(hl, (255,255,255,40), hl.get_rect())
        surface.blit(hl, (cx-int(self.size*0.5), cy-int(self.size*0.42)))


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
    Spawns from BOTTOM of screen and drives in the bottom area.
    Does NOT chase/ram the player.  It simply occupies a lane near
    the bottom so the player has to avoid it while still dodging rocks.
    Catching = player crashes a 2nd time while chase timer is running.
    """

    def __init__(self, lane: int):
        self.lane = lane
        self.x    = float(LANES[lane])
        # Start just below the visible screen
        self.y    = float(SCREEN_H + 60)
        # Drive up to the patrol row, then idle there
        self.patrol_y = float(SCREEN_H - 90)   # bottom patrol lane
        self.arrived  = False
        self.w = 40
        self.h = 58

    @property
    def rect(self):
        return pygame.Rect(int(self.x)-20, int(self.y)-28, 40, 56)

    def update_position(self, speed: float, dt: int):
        """
        Move up to patrol_y quickly, then hold position.
        Follow the world scroll (same speed as obstacles) once arrived.
        """
        if not self.arrived:
            # Rush up onto screen
            self.y -= speed * dt * 0.06 * 2.0
            if self.y <= self.patrol_y:
                self.y       = self.patrol_y
                self.arrived = True
        # Once on screen, stay fixed on screen (don't scroll away)

    def is_offscreen(self): return False   # police stays until chase ends

    def draw(self, surface, tick):
        cx, cy = int(self.x), int(self.y)
        flash = (tick // 8) % 2 == 0

        # Hull — bow points UP
        hull_pts = [
            (cx-18, cy+24),
            (cx-20, cy-20),
            (cx+20, cy-20),
            (cx+18, cy+24),
            (cx,    cy+32),
        ]
        pygame.draw.polygon(surface, C_POLICE_BLUE, hull_pts)
        pygame.draw.polygon(surface, (20,40,120), hull_pts, 2)

        pygame.draw.rect(surface, C_WHITE, (cx-18, cy-2, 36, 6))
        pygame.draw.rect(surface, C_RED,   (cx-18, cy+4, 36, 4))

        lc = C_RED_LIGHT if flash else (68,68,255)
        rc = (68,68,255) if flash else C_RED_LIGHT
        pygame.draw.rect(surface, lc, (cx-10, cy-22, 8, 6))
        pygame.draw.rect(surface, rc, (cx+ 2, cy-22, 8, 6))

        f = pygame.font.SysFont("consolas,monospace", 9, bold=True)
        t = f.render("POLICE", True, C_WHITE)
        surface.blit(t, (cx-t.get_width()//2, cy-10))
