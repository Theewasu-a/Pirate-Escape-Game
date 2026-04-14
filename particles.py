"""
particles.py - Particle effects system
"""
import pygame
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


class FloatingText:
    def __init__(self, x, y, text, color=(240,192,64), font_size=16, lifetime=80):
        self.x, self.y   = x, y
        self.vy          = -1.2
        self.text        = text
        self.color       = color
        self.lifetime    = lifetime
        self.max_lifetime= lifetime
        self._font = pygame.font.SysFont("consolas,monospace", font_size, bold=True)

    def update(self, dt):
        self.y        += self.vy * (dt * 0.06)
        self.lifetime -= dt * 0.06

    def is_dead(self): return self.lifetime <= 0

    def draw(self, surface):
        rendered = self._font.render(self.text, True, self.color)
        s = pygame.Surface(rendered.get_size(), pygame.SRCALPHA)
        s.blit(rendered, (0,0))
        s.set_alpha(max(0, int(255 * self.lifetime / self.max_lifetime)))
        surface.blit(s, (int(self.x)-s.get_width()//2, int(self.y)))


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
