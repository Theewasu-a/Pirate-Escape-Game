"""
particles.py - Particle effects system
"""
import pygame
import pygame.freetype
import random
import math


class Particle:
    def __init__(self, x, y, vx=0.0, vy=0.0, r=4, color=(240,192,64), lifetime=60):
        self.x, self.y   = x, y
        self.vx, self.vy = vx, vy
        self.r           = r
        self.color       = color
        self.lifetime    = lifetime
        self.max_lifetime= lifetime

    def update(self, dt):
        f = dt * 0.06
        self.x        += self.vx * f
        self.y        += self.vy * f
        self.lifetime -= f
        self.vy       += 0.04 * f

    def is_dead(self): return self.lifetime <= 0

    def draw(self, surface):
        r     = max(1, int(self.r * (self.lifetime / self.max_lifetime)))
        alpha = max(0, int(255 * self.lifetime / self.max_lifetime))
        s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (r+1, r+1), r)
        surface.blit(s, (int(self.x)-r-1, int(self.y)-r-1))


class ShardParticle:
    """Triangular shard that flies outward and spins — used for shield shatter."""
    def __init__(self, x, y, angle, speed, color, lifetime=55):
        self.x, self.y   = x, y
        self.vx          = math.cos(angle) * speed
        self.vy          = math.sin(angle) * speed
        self.rot         = random.uniform(0, math.pi*2)
        self.rot_speed   = random.uniform(-0.25, 0.25)
        self.size        = random.uniform(6, 12)
        self.color       = color
        self.lifetime    = lifetime
        self.max_lifetime= lifetime

    def update(self, dt):
        f = dt * 0.06
        self.x        += self.vx * f
        self.y        += self.vy * f
        self.rot      += self.rot_speed * f
        self.vx       *= 0.97
        self.vy       *= 0.97
        self.lifetime -= f

    def is_dead(self): return self.lifetime <= 0

    def draw(self, surface):
        alpha = max(0, int(255 * self.lifetime / self.max_lifetime))
        s = self.size
        pts = [
            (self.x + math.cos(self.rot)*s, self.y + math.sin(self.rot)*s),
            (self.x + math.cos(self.rot+2.1)*s*0.6, self.y + math.sin(self.rot+2.1)*s*0.6),
            (self.x + math.cos(self.rot-2.1)*s*0.6, self.y + math.sin(self.rot-2.1)*s*0.6),
        ]
        # Draw onto a small alpha surface
        minx = int(min(p[0] for p in pts)) - 1
        miny = int(min(p[1] for p in pts)) - 1
        w    = int(max(p[0] for p in pts)) - minx + 2
        h    = int(max(p[1] for p in pts)) - miny + 2
        if w <= 0 or h <= 0: return
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        local = [(p[0]-minx, p[1]-miny) for p in pts]
        pygame.draw.polygon(surf, (*self.color, alpha), local)
        pygame.draw.polygon(surf, (255,255,255, min(255, alpha+40)), local, 1)
        surface.blit(surf, (minx, miny))


class ShieldRing:
    """Expanding circle used on shield break."""
    def __init__(self, x, y, color):
        self.x, self.y   = x, y
        self.r           = 20
        self.max_r       = 80
        self.color       = color
        self.lifetime    = 30
        self.max_lifetime= 30

    def update(self, dt):
        f = dt * 0.06
        self.r        += 2.0 * f
        self.lifetime -= f

    def is_dead(self): return self.lifetime <= 0 or self.r > self.max_r

    def draw(self, surface):
        alpha = max(0, int(200 * self.lifetime / self.max_lifetime))
        r = int(self.r)
        s = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (r+2, r+2), r, 3)
        surface.blit(s, (int(self.x)-r-2, int(self.y)-r-2))


class FloatingText:
    def __init__(self, x, y, text, color=(240,192,64), font_size=16, lifetime=80):
        self.x, self.y   = x, y
        self.vy          = -1.2
        self.text        = text
        self.color       = color
        self.lifetime    = lifetime
        self.max_lifetime= lifetime
        self._ft = pygame.freetype.SysFont("consolas,couriernew,monospace", font_size, bold=True)

    def update(self, dt):
        self.y        += self.vy * (dt * 0.06)
        self.lifetime -= dt * 0.06

    def is_dead(self): return self.lifetime <= 0

    def draw(self, surface):
        alpha = max(0, int(255 * self.lifetime / self.max_lifetime))
        text_surf, rect = self._ft.render(self.text, (*self.color, alpha))
        surface.blit(text_surf, (int(self.x) - rect.width // 2, int(self.y)))


class ParticleSystem:
    def __init__(self):
        self._particles: list = []
        self._texts:     list = []

    def explosion(self, x, y, color=(240,192,64), count=12):
        for _ in range(count):
            a = random.uniform(0, math.pi*2)
            spd = random.uniform(1.0, 3.5)
            self._particles.append(Particle(
                x, y,
                vx=math.cos(a)*spd, vy=math.sin(a)*spd,
                r=random.uniform(2,5), color=color,
                lifetime=random.randint(35,70)
            ))

    def shield_shatter(self, x, y, color=(68,170,255)):
        """Dramatic shatter: ring wave + flying shards + sparkle particles."""
        # Expanding ring
        self._particles.append(ShieldRing(x, y, color))
        # Shards flying outward
        for i in range(14):
            a = i / 14 * math.pi * 2 + random.uniform(-0.15, 0.15)
            spd = random.uniform(2.5, 4.5)
            self._particles.append(ShardParticle(x, y, a, spd, color,
                                                 lifetime=random.randint(45, 70)))
        # Sparkle dots
        for _ in range(16):
            a = random.uniform(0, math.pi*2)
            spd = random.uniform(1.5, 3.2)
            self._particles.append(Particle(
                x, y,
                vx=math.cos(a)*spd, vy=math.sin(a)*spd,
                r=random.uniform(1.5, 3.0), color=(220, 240, 255),
                lifetime=random.randint(25, 45)
            ))

    def float_text(self, x, y, text, color=(240,192,64), font_size=16):
        self._texts.append(FloatingText(x, y, text, color, font_size))

    def update(self, dt):
        for p in self._particles: p.update(dt)
        for t in self._texts:     t.update(dt)
        self._particles = [p for p in self._particles if not p.is_dead()]
        self._texts     = [t for t in self._texts     if not t.is_dead()]

    def draw(self, surface):
        for p in self._particles: p.draw(surface)
        for t in self._texts:     t.draw(surface)

    def clear(self):
        self._particles.clear()
        self._texts.clear()
