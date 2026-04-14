"""
ui.py - HUD and screen rendering
"""
import pygame, math
from constants import (
    SCREEN_W, SCREEN_H,
    C_OCEAN_DEEP, C_OCEAN_FOAM, C_OCEAN_LIGHT,
    C_GOLD, C_GOLD_DARK, C_RED, C_RED_LIGHT, C_GREEN,
    C_WHITE, C_GRAY,
    LANES, CHASE_DURATION_MS,
    SPEED_START, MAX_SPEED_CRASH,
)


def _font(size, bold=False):
    return pygame.font.SysFont("consolas,couriernew,monospace", size, bold=bold)

def _title_font(size):
    return pygame.font.SysFont("georgia,timesnewroman,serif", size, bold=True)


def draw_panel(surface, rect, border_color=C_OCEAN_FOAM, alpha=210):
    p = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    p.fill((*C_OCEAN_DEEP, alpha))
    surface.blit(p, rect.topleft)
    pygame.draw.rect(surface, border_color, rect, 2, border_radius=6)


def draw_button(surface, rect, text, color=C_GOLD, hovered=False):
    bg = pygame.Surface(rect.size, pygame.SRCALPHA)
    bg.fill((*color, 80 if hovered else 30))
    surface.blit(bg, rect.topleft)
    pygame.draw.rect(surface, color, rect, 2, border_radius=4)
    f = _font(13, bold=True)
    t = f.render(text, True, color)
    surface.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))


# ── HUD ─────────────────────────────────────────────────────
def draw_hud(surface, score: float, coins: int, distance_km: float,
             speed: float, powerups: list, chase_timer: int, tick: int):
    draw_panel(surface, pygame.Rect(0, 0, SCREEN_W, 56), C_OCEAN_FOAM, alpha=200)

    km_str = f"{distance_km:.2f} km"
    labels = [
        ("COINS", str(coins),        C_GOLD),
        ("DIST",  km_str,            C_GREEN),
        ("SCORE", str(int(score)),   C_OCEAN_FOAM),
    ]
    for i, (lbl, val, color) in enumerate(labels):
        x = 16 + i * 118
        surface.blit(_font(9).render(lbl, True, C_GRAY),             (x, 6))
        surface.blit(_font(16, bold=True).render(val, True, color),  (x, 18))

    # Powerup indicators — right side
    if powerups:
        PU_COLORS = {"SHIELD":(68,170,255),"SPEED":(255,255,68),
                     "MAGNET":(255,68,255),"x2 COINS":(68,255,136)}
        for i, pu in enumerate(powerups):
            t = _font(9, bold=True).render(pu, True, PU_COLORS.get(pu, C_WHITE))
            surface.blit(t, (SCREEN_W - 78, 4 + i*14))

    # Chase bar
    if chase_timer > 0:
        progress = chase_timer / CHASE_DURATION_MS
        bx, by = SCREEN_W//2 - 100, 62
        pygame.draw.rect(surface, C_OCEAN_DEEP, (bx-2, by-2, 204, 16), border_radius=4)
        pygame.draw.rect(surface, C_RED,        (bx,   by,   int(200*progress), 12), border_radius=3)
        pygame.draw.rect(surface, C_RED_LIGHT,  (bx,   by,   200, 12), 1, border_radius=3)
        if (tick//15) % 2 == 0:
            ct = _font(9, bold=True).render("! POLICE CHASE !", True, C_RED_LIGHT)
            surface.blit(ct, (SCREEN_W//2 - ct.get_width()//2, by+1))


# ── Speed bar ───────────────────────────────────────────────
def draw_speed_bar(surface, speed: float):
    bx, by, bw, bh = 10, SCREEN_H - 18, SCREEN_W - 20, 10
    ratio = max(0.0, min(1.0, (speed - SPEED_START) / (MAX_SPEED_CRASH - SPEED_START)))
    color = C_GREEN if ratio < 0.50 else C_GOLD if ratio < 0.80 else C_RED_LIGHT
    pygame.draw.rect(surface, C_OCEAN_DEEP, (bx-1, by-1, bw+2, bh+2), border_radius=4)
    pygame.draw.rect(surface, color,        (bx,   by,   int(bw*ratio), bh), border_radius=3)
    pygame.draw.rect(surface, C_OCEAN_FOAM, (bx,   by,   bw,  bh), 1, border_radius=3)
    st = _font(8).render("SPEED", True, C_GRAY)
    surface.blit(st, (SCREEN_W//2 - st.get_width()//2, by+1))


# ── Announcement ────────────────────────────────────────────
def draw_announce(surface, text: str, alpha: int):
    f   = _title_font(42)
    txt = f.render(text, True, C_GOLD)
    s   = pygame.Surface(txt.get_size(), pygame.SRCALPHA)
    s.blit(txt, (0,0))
    s.set_alpha(alpha)
    surface.blit(s, (SCREEN_W//2 - s.get_width()//2, SCREEN_H//2 - s.get_height()//2))


# ── Water background ────────────────────────────────────────
def draw_water(surface, wave_offset: float):
    surface.fill(C_OCEAN_DEEP)
    for i in range(14):
        y     = int((wave_offset*(0.5+i*0.07) + i*52) % SCREEN_H)
        alpha = 20 + i*4
        for x in range(0, SCREEN_W, 8):
            wy = int(y + math.sin(x*0.025 + wave_offset*0.04 + i)*3)
            if 0 <= wy < SCREEN_H:
                s = pygame.Surface((6,1), pygame.SRCALPHA)
                s.fill((*C_OCEAN_FOAM, alpha))
                surface.blit(s, (x, wy))
    for lx in LANES:
        for y in range(0, SCREEN_H, 30):
            s = pygame.Surface((1,14), pygame.SRCALPHA)
            s.fill((*C_OCEAN_FOAM, 12))
            surface.blit(s, (lx, y))


# ── Menu ────────────────────────────────────────────────────
def draw_menu(surface, wave_offset, buttons, mouse_pos):
    draw_water(surface, wave_offset)
    tf = _title_font(52)
    for i, word in enumerate(["PIRATE","ESCAPE"]):
        t = tf.render(word, True, C_GOLD)
        surface.blit(t, (SCREEN_W//2 - t.get_width()//2, 90 + i*58))
    sk = pygame.font.SysFont("segoeuisymbol,symbola,serif", 48).render("X", True, C_GOLD_DARK)
    surface.blit(sk, (SCREEN_W//2 - sk.get_width()//2, 44))
    sub = _font(13).render("Sail fast · Dodge rocks · Escape the law!", True, C_OCEAN_FOAM)
    surface.blit(sub, (SCREEN_W//2 - sub.get_width()//2, 214))
    pygame.draw.line(surface, C_OCEAN_FOAM, (SCREEN_W//4, 240), (SCREEN_W*3//4, 240), 1)
    ctrl = _font(11).render("<- -> Arrow Keys / A-D to steer", True, C_GRAY)
    surface.blit(ctrl, (SCREEN_W//2 - ctrl.get_width()//2, 250))
    for key, rect in buttons.items():
        draw_button(surface, rect, key, hovered=rect.collidepoint(mouse_pos))


# ── Game Over ───────────────────────────────────────────────
def draw_gameover(surface, stats: dict, buttons, mouse_pos, is_highscore=False):
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((*C_OCEAN_DEEP, 220))
    surface.blit(ov, (0,0))

    t = _title_font(36).render("GAME  OVER", True, C_RED_LIGHT)
    surface.blit(t, (SCREEN_W//2 - t.get_width()//2, 80))

    r = _font(13).render(stats.get("reason",""), True, C_OCEAN_FOAM)
    surface.blit(r, (SCREEN_W//2 - r.get_width()//2, 126))

    if is_highscore:
        hs = _font(14, bold=True).render("* NEW HIGH SCORE! *", True, C_GOLD)
        surface.blit(hs, (SCREEN_W//2 - hs.get_width()//2, 152))

    panel = pygame.Rect(SCREEN_W//2 - 170, 178, 340, 152)
    draw_panel(surface, panel)

    km_val = stats.get("distance_km", 0)
    rows = [
        [("SCORE",   str(int(stats.get("score",0))),     C_GOLD),
         ("COINS",   str(stats.get("coins",0)),           C_GOLD)],
        [("DIST",    f"{km_val:.2f} km",                  C_GREEN),
         ("CRASHES", str(stats.get("collisions",0)),      C_RED_LIGHT)],
        [("TIME",    str(stats.get("time",0)) + "s",      C_OCEAN_FOAM),
         ("",        "",                                   C_WHITE)],
    ]
    lf = _font(9); vf = _font(17, bold=True)
    for ri, row in enumerate(rows):
        for ci, (label, value, color) in enumerate(row):
            if not label: continue
            x = panel.x + 30 + ci*160
            y = panel.y + 14 + ri*46
            surface.blit(lf.render(label, True, C_GRAY),       (x, y))
            surface.blit(vf.render(value, True, color),         (x, y+14))

    pygame.draw.line(surface, C_OCEAN_FOAM,
                     (SCREEN_W//4, 342), (SCREEN_W*3//4, 342), 1)
    for key, rect in buttons.items():
        draw_button(surface, rect, key, hovered=rect.collidepoint(mouse_pos))


# ── Leaderboard ─────────────────────────────────────────────
def draw_leaderboard(surface, entries, buttons, mouse_pos):
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((*C_OCEAN_DEEP, 230))
    surface.blit(ov, (0,0))

    t = _title_font(32).render("LEADERBOARD", True, C_GOLD)
    surface.blit(t, (SCREEN_W//2 - t.get_width()//2, 30))

    headers = ["#","SCORE","COINS","KM","TIME"]
    col_xs  = [36, 110,    210,    300, 380]
    hf = _font(10, bold=True)
    for hdr, x in zip(headers, col_xs):
        surface.blit(hf.render(hdr, True, C_OCEAN_FOAM), (x, 90))
    pygame.draw.line(surface, C_OCEAN_FOAM, (24, 108), (SCREEN_W-24, 108), 1)

    medal_colors = [C_GOLD, (192,192,192), (205,127,50)]
    rf = _font(13)
    for i, entry in enumerate(entries[:8]):
        y     = 116 + i*34
        color = medal_colors[i] if i < 3 else C_WHITE
        ranks = ["1st","2nd","3rd"]
        row   = [ranks[i] if i < 3 else str(i+1),
                 str(entry.score), str(entry.coins),
                 f"{entry.distance:.2f}", f"{entry.time}s"]
        for val, x in zip(row, col_xs):
            surface.blit(rf.render(val, True, color), (x, y))

    if not entries:
        et = _font(13).render("No scores yet - set sail!", True, C_GRAY)
        surface.blit(et, (SCREEN_W//2 - et.get_width()//2, 200))

    pygame.draw.line(surface, C_OCEAN_FOAM,
                     (SCREEN_W//4, SCREEN_H-110), (SCREEN_W*3//4, SCREEN_H-110), 1)
    for key, rect in buttons.items():
        draw_button(surface, rect, key, hovered=rect.collidepoint(mouse_pos))
