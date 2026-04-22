"""
ui.py - HUD and screen rendering
"""
import pygame, math
from .constants import (
    SCREEN_W, SCREEN_H,
    C_OCEAN_DEEP, C_OCEAN_FOAM, C_OCEAN_LIGHT,
    C_GOLD, C_GOLD_DARK, C_RED, C_RED_LIGHT, C_GREEN,
    C_WHITE, C_GRAY,
    LANES, CHASE_DURATION_MS,
    SPEED_START, MAX_SPEED_CRASH,
)

# ── Pause overlay ────────────────────────────────────────────
def draw_pause(surface, buttons, mouse_pos):
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 160))
    surface.blit(ov, (0, 0))

    tf = _title_font(42)
    t = tf.render("PAUSED", True, C_GOLD)
    surface.blit(t, (SCREEN_W//2 - t.get_width()//2, 180))

    for key, rect in buttons.items():
        draw_button(surface, rect, key, hovered=rect.collidepoint(mouse_pos))


# ── Settings screen ──────────────────────────────────────────
def draw_settings(surface, music_vol: float, sfx_vol: float,
                  buttons, sliders, mouse_pos):
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((*C_OCEAN_DEEP, 235))
    surface.blit(ov, (0, 0))

    tf = _title_font(36)
    t = tf.render("SETTINGS", True, C_GOLD)
    surface.blit(t, (SCREEN_W//2 - t.get_width()//2, 60))
    pygame.draw.line(surface, C_OCEAN_FOAM,
                     (SCREEN_W//4, 110), (SCREEN_W*3//4, 110), 1)

    lf = _font(13, bold=True)
    vf = _font(11)

    # Music volume
    my = 160
    ml = lf.render("MUSIC VOLUME", True, C_OCEAN_FOAM)
    surface.blit(ml, (SCREEN_W//2 - ml.get_width()//2, my))
    _draw_slider(surface, sliders["music"], music_vol, C_GOLD, mouse_pos)
    mv = vf.render(f"{int(music_vol*100)}%", True, C_GOLD)
    surface.blit(mv, (sliders["music"].right + 10,
                      sliders["music"].centery - mv.get_height()//2))

    # SFX volume
    sy = 260
    sl = lf.render("SFX VOLUME", True, C_OCEAN_FOAM)
    surface.blit(sl, (SCREEN_W//2 - sl.get_width()//2, sy))
    _draw_slider(surface, sliders["sfx"], sfx_vol, C_RED_LIGHT, mouse_pos)
    sv = vf.render(f"{int(sfx_vol*100)}%", True, C_RED_LIGHT)
    surface.blit(sv, (sliders["sfx"].right + 10,
                      sliders["sfx"].centery - sv.get_height()//2))

    for key, rect in buttons.items():
        draw_button(surface, rect, key, hovered=rect.collidepoint(mouse_pos))


def _draw_slider(surface, rect, value: float, color, mouse_pos):
    """Draw a horizontal slider bar with handle."""
    # Track
    pygame.draw.rect(surface, C_GRAY, rect, border_radius=4)
    # Fill
    fill_w = int(rect.width * max(0.0, min(1.0, value)))
    if fill_w > 0:
        pygame.draw.rect(surface,
                         color,
                         pygame.Rect(rect.x, rect.y, fill_w, rect.height),
                         border_radius=4)
    pygame.draw.rect(surface, C_OCEAN_FOAM, rect, 1, border_radius=4)
    # Handle
    hx = rect.x + int(rect.width * max(0.0, min(1.0, value)))
    hy = rect.centery
    hovered = (rect.x <= mouse_pos[0] <= rect.right and
               rect.y - 4 <= mouse_pos[1] <= rect.bottom + 4)
    hr = 9 if hovered else 7
    pygame.draw.circle(surface, C_WHITE, (hx, hy), hr)
    pygame.draw.circle(surface, color,   (hx, hy), hr, 2)


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
             speed: float, powerups: list, chase_timer: int, tick: int,
             pause_btn_rect=None, mouse_pos=(0,0)):

    HUD_H = 62

    # Gradient-style background (two-tone overlay)
    bg_top = pygame.Surface((SCREEN_W, HUD_H), pygame.SRCALPHA)
    bg_top.fill((8, 18, 36, 220))
    surface.blit(bg_top, (0, 0))
    # Subtle bottom glow line
    pygame.draw.line(surface, (40, 100, 160), (0, HUD_H), (SCREEN_W, HUD_H), 2)
    # Vertical dividers
    for div_x in (130, 270):
        pygame.draw.line(surface, (40, 80, 130, 100), (div_x, 8), (div_x, HUD_H - 8), 1)

    # ── Coins block ───────────────────────────────────────────
    _hud_block(surface, 14, 8,
               icon_color=C_GOLD,
               label="COINS", value=str(coins),
               val_color=C_GOLD)

    # ── Distance block ────────────────────────────────────────
    _hud_block(surface, 148, 8,
               icon_color=C_GREEN,
               label="DIST", value=f"{distance_km:.2f} km",
               val_color=C_GREEN)

    # ── Score block ───────────────────────────────────────────
    _hud_block(surface, 284, 8,
               icon_color=C_OCEAN_FOAM,
               label="SCORE", value=str(int(score)),
               val_color=C_WHITE)

    # ── Powerup pills (bottom strip) ─────────────────────────
    if powerups:
        PU_COLORS = {
            "SHIELD":   (68, 170, 255),
            "SPEED":    (255, 220, 50),
            "MAGNET":   (220, 80, 255),
            "x2 COINS": (68, 255, 150),
        }
        px = 14
        py = HUD_H - 15
        for pu in powerups:
            col = PU_COLORS.get(pu, C_WHITE)
            pill_w = _font(8, bold=True).size(pu)[0] + 10
            pill = pygame.Surface((pill_w, 11), pygame.SRCALPHA)
            pill.fill((*col, 55))
            surface.blit(pill, (px, py))
            pygame.draw.rect(surface, col, (px, py, pill_w, 11), 1, border_radius=3)
            surface.blit(_font(8, bold=True).render(pu, True, col), (px + 5, py + 1))
            px += pill_w + 5

    # ── Pause button ──────────────────────────────────────────
    if pause_btn_rect:
        hov = pause_btn_rect.collidepoint(mouse_pos)
        # Filled rounded background
        col_bg = (50, 100, 160) if hov else (30, 60, 110)
        pygame.draw.rect(surface, col_bg, pause_btn_rect, border_radius=6)
        pygame.draw.rect(surface, (100, 170, 240), pause_btn_rect, 1, border_radius=6)
        # Two thick pause bars, centered inside the button
        cx_ = pause_btn_rect.centerx
        cy_ = pause_btn_rect.centery
        bar_h, bar_w, gap = 14, 4, 4
        for ox in (-(bar_w + gap//2), gap//2):
            pygame.draw.rect(surface, C_WHITE,
                             (cx_ + ox, cy_ - bar_h//2, bar_w, bar_h),
                             border_radius=1)

    # ── Chase bar ─────────────────────────────────────────────
    if chase_timer > 0:
        progress = chase_timer / CHASE_DURATION_MS
        bx, by = SCREEN_W//2 - 110, HUD_H + 4
        # Background track
        pygame.draw.rect(surface, (30, 10, 10), (bx-2, by-2, 224, 14), border_radius=5)
        # Fill with gradient-like color (red → orange as time runs out)
        fill_color = (
            int(200 + 55 * progress),
            int(30 * progress),
            20
        )
        pygame.draw.rect(surface, fill_color, (bx, by, int(220*progress), 10), border_radius=4)
        pygame.draw.rect(surface, C_RED_LIGHT, (bx, by, 220, 10), 1, border_radius=4)
        if (tick//12) % 2 == 0:
            ct = _font(8, bold=True).render("! POLICE CHASE !", True, (255, 100, 80))
            surface.blit(ct, (SCREEN_W//2 - ct.get_width()//2, by))


def _hud_block(surface, x, y, icon_color, label, value, val_color):
    """Draw a single HUD info block — no unicode, just colored accent + text."""
    # Colored accent bar on the left
    pygame.draw.rect(surface, icon_color, (x, y + 6, 3, 30), border_radius=1)
    ox = x + 8
    surface.blit(_font(8).render(label, True, C_GRAY), (ox, y + 4))
    surface.blit(_font(17, bold=True).render(value, True, val_color), (ox, y + 16))


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
def draw_water(surface, wave_offset: float, bg_color=None):
    surface.fill(bg_color if bg_color is not None else C_OCEAN_DEEP)
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


# ── Data Page ────────────────────────────────────────────────
_DATA_TAB_LABELS = ["SUMMARY", "TIME PLAYED", "DIST vs COINS", "COLLISION SPD"]


def get_data_tab_rects():
    """Shared tab button rects — used by both draw and click handler."""
    tab_w = (SCREEN_W - 16) // 4
    return [pygame.Rect(8 + i * tab_w, 50, tab_w - 3, 34)
            for i in range(4)]


def _draw_axes(surface, rect, x_label, y_label):
    """Draw Y/X axes with labels inside a chart rect."""
    pygame.draw.line(surface, C_OCEAN_FOAM,
                     (rect.left, rect.top), (rect.left, rect.bottom), 1)
    pygame.draw.line(surface, C_OCEAN_FOAM,
                     (rect.left, rect.bottom), (rect.right, rect.bottom), 1)
    lf = _font(9)
    xl = lf.render(x_label, True, C_OCEAN_FOAM)
    yl = lf.render(y_label, True, C_OCEAN_FOAM)
    surface.blit(xl, (rect.right - xl.get_width(), rect.bottom + 3))
    surface.blit(yl, (rect.left - yl.get_width() - 3, rect.top - 12))


def _draw_histogram(surface, rect, values, title,
                    x_label, y_label, color, bins=8):
    """Graph 1 — Histogram of time played distribution."""
    draw_panel(surface, rect, (40, 100, 160), alpha=200)
    tf = _font(12, bold=True)
    surface.blit(tf.render(title, True, C_WHITE),
                 (rect.x + 8, rect.y + 5))

    if not values:
        et = _font(11).render("No data yet", True, C_GRAY)
        surface.blit(et, (rect.centerx - et.get_width()//2, rect.centery))
        return

    pad_l, pad_r, pad_t, pad_b = 28, 10, 28, 22
    plot = pygame.Rect(rect.x + pad_l, rect.y + pad_t,
                       rect.width - pad_l - pad_r,
                       rect.height - pad_t - pad_b)

    vmin, vmax = min(values), max(values)
    if vmax == vmin:
        vmax = vmin + 1
    bin_w = (vmax - vmin) / bins
    counts = [0] * bins
    for v in values:
        idx = min(bins - 1, int((v - vmin) / bin_w))
        counts[idx] += 1
    max_c = max(counts) or 1

    # Grid lines
    for frac in (0.25, 0.5, 0.75, 1.0):
        gy = int(plot.y + plot.height * (1 - frac))
        pygame.draw.line(surface, (30, 60, 100), (plot.left+1, gy), (plot.right, gy), 1)

    bar_w = plot.width / bins
    for i, c in enumerate(counts):
        if c == 0: continue
        bh = int(plot.height * (c / max_c))
        bx = int(plot.x + i * bar_w)
        by = plot.y + plot.height - bh
        pygame.draw.rect(surface, color,        (bx+1, by, int(bar_w)-2, bh))
        lighter = tuple(min(255, cc + 70) for cc in color)
        pygame.draw.rect(surface, lighter,      (bx+1, by, int(bar_w)-2, 3))
        pygame.draw.rect(surface, (20, 40, 70), (bx+1, by, int(bar_w)-2, bh), 1)
        lf = _font(9)
        tt = lf.render(str(c), True, C_WHITE)
        surface.blit(tt, (bx + int(bar_w)//2 - tt.get_width()//2, by - 12))

    lf = _font(8)
    for frac, v in ((0.0, vmin), (0.5, (vmin+vmax)/2), (1.0, vmax)):
        lbl = f"{v:.0f}"
        lx  = int(plot.x + plot.width * frac)
        lt  = lf.render(lbl, True, C_OCEAN_FOAM)
        surface.blit(lt, (lx - lt.get_width()//2, plot.bottom + 3))

    _draw_axes(surface, plot, x_label, y_label)


def _draw_scatter(surface, rect, points, title, x_label, y_label, color):
    """Graph 2 — Scatter plot of Distance vs Coins."""
    draw_panel(surface, rect, (40, 100, 160), alpha=200)
    tf = _font(12, bold=True)
    surface.blit(tf.render(title, True, C_WHITE),
                 (rect.x + 8, rect.y + 5))

    if not points:
        et = _font(11).render("No data yet", True, C_GRAY)
        surface.blit(et, (rect.centerx - et.get_width()//2, rect.centery))
        return

    pad_l, pad_r, pad_t, pad_b = 32, 10, 28, 22
    plot = pygame.Rect(rect.x + pad_l, rect.y + pad_t,
                       rect.width - pad_l - pad_r,
                       rect.height - pad_t - pad_b)

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if xmax == xmin: xmax = xmin + 1
    if ymax == ymin: ymax = ymin + 1

    # Grid lines
    for frac in (0.25, 0.5, 0.75):
        gy = int(plot.y + plot.height * frac)
        pygame.draw.line(surface, (30, 60, 100),
                         (plot.left+1, gy), (plot.right, gy), 1)
    for frac in (0.25, 0.5, 0.75):
        gx = int(plot.x + plot.width * frac)
        pygame.draw.line(surface, (30, 60, 100),
                         (gx, plot.top), (gx, plot.bottom - 1), 1)

    # Points with glow
    glow_col = tuple(min(255, c + 80) for c in color)
    for (x, y) in points:
        px = int(plot.x + (x - xmin) / (xmax - xmin) * plot.width)
        py = int(plot.y + plot.height - (y - ymin) / (ymax - ymin) * plot.height)
        gs = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*color, 50), (7, 7), 7)
        surface.blit(gs, (px - 7, py - 7))
        pygame.draw.circle(surface, color, (px, py), 4)
        pygame.draw.circle(surface, glow_col, (px, py), 4, 1)

    lf = _font(8)
    for frac, v in ((0.0, xmin), (0.5, (xmin+xmax)/2), (1.0, xmax)):
        lbl = f"{v:.1f}"
        lx  = int(plot.x + plot.width * frac)
        lt  = lf.render(lbl, True, C_OCEAN_FOAM)
        surface.blit(lt, (lx - lt.get_width()//2, plot.bottom + 3))
    for frac, v in ((0.0, ymax), (0.5, (ymin+ymax)/2), (1.0, ymin)):
        lbl = f"{int(v)}"
        ly  = int(plot.y + plot.height * frac)
        lt  = lf.render(lbl, True, C_OCEAN_FOAM)
        surface.blit(lt, (plot.left - lt.get_width() - 3, ly - lt.get_height()//2))

    _draw_axes(surface, plot, x_label, y_label)


def _draw_boxplot(surface, rect, values, title, y_label, color):
    """Graph 3 — Boxplot of boat speed at collision."""
    draw_panel(surface, rect, (40, 100, 160), alpha=200)
    tf = _font(12, bold=True)
    surface.blit(tf.render(title, True, C_WHITE),
                 (rect.x + 8, rect.y + 5))

    if not values or len(values) < 1:
        et = _font(11).render("No collision data yet", True, C_GRAY)
        surface.blit(et, (rect.centerx - et.get_width()//2, rect.centery))
        return

    pad_l, pad_r, pad_t, pad_b = 42, 16, 28, 22
    plot = pygame.Rect(rect.x + pad_l, rect.y + pad_t,
                       rect.width - pad_l - pad_r,
                       rect.height - pad_t - pad_b)

    vs = sorted(values)
    n  = len(vs)
    def _quant(q):
        if n == 1: return vs[0]
        idx = (n - 1) * q
        lo, hi = int(idx), min(n - 1, int(idx) + 1)
        return vs[lo] + (vs[hi] - vs[lo]) * (idx - lo)

    q1, med, q3 = _quant(0.25), _quant(0.5), _quant(0.75)
    iqr = q3 - q1
    lo_fence = q1 - 1.5 * iqr
    hi_fence = q3 + 1.5 * iqr
    inliers  = [v for v in vs if lo_fence <= v <= hi_fence]
    outliers = [v for v in vs if v < lo_fence or v > hi_fence]
    w_lo = min(inliers) if inliers else vs[0]
    w_hi = max(inliers) if inliers else vs[-1]

    vmin, vmax = min(vs), max(vs)
    if vmax == vmin: vmax = vmin + 1
    span = vmax - vmin
    # padding on the axis
    vmin_p = vmin - span * 0.1
    vmax_p = vmax + span * 0.1
    if vmax_p == vmin_p: vmax_p = vmin_p + 1

    def y_of(v):
        return int(plot.y + plot.height - (v - vmin_p) / (vmax_p - vmin_p) * plot.height)

    cx = plot.centerx
    box_w = min(60, plot.width // 2)
    # Whiskers
    y_wlo, y_whi = y_of(w_lo), y_of(w_hi)
    pygame.draw.line(surface, C_WHITE, (cx, y_whi), (cx, y_wlo), 1)
    pygame.draw.line(surface, C_WHITE, (cx - box_w//3, y_whi), (cx + box_w//3, y_whi), 1)
    pygame.draw.line(surface, C_WHITE, (cx - box_w//3, y_wlo), (cx + box_w//3, y_wlo), 1)
    # Box (Q1 .. Q3)
    y_q1, y_q3 = y_of(q1), y_of(q3)
    box_rect = pygame.Rect(cx - box_w//2, y_q3, box_w, max(2, y_q1 - y_q3))
    pygame.draw.rect(surface, color, box_rect)
    pygame.draw.rect(surface, C_WHITE, box_rect, 1)
    # Median line
    y_m = y_of(med)
    pygame.draw.line(surface, C_GOLD,
                     (cx - box_w//2, y_m), (cx + box_w//2, y_m), 2)
    # Outliers
    for o in outliers:
        pygame.draw.circle(surface, C_RED_LIGHT, (cx, y_of(o)), 3, 1)

    # Axis labels (Y-axis only — X is a single category)
    lf = _font(8)
    for frac, v in ((0.0, vmax_p), (0.5, (vmin_p+vmax_p)/2), (1.0, vmin_p)):
        ly = int(plot.y + plot.height * frac)
        lt = lf.render(f"{v:.1f}", True, C_OCEAN_FOAM)
        surface.blit(lt, (plot.left - lt.get_width() - 3, ly - lt.get_height()//2))

    # Stats caption
    lf2 = _font(9)
    cap = f"n={n}   med={med:.2f}   Q1={q1:.2f}   Q3={q3:.2f}"
    ct = lf2.render(cap, True, C_OCEAN_FOAM)
    surface.blit(ct, (rect.centerx - ct.get_width()//2, rect.bottom - 14))

    _draw_axes(surface, plot, "", y_label)


def _draw_summary_table(surface, rect, sessions, collision_speeds):
    """Summary statistics table — one row per game metric."""
    import statistics as _st

    draw_panel(surface, rect, (20, 45, 90), alpha=220)

    if not sessions and not collision_speeds:
        et = _font(11).render("No data yet — set sail!", True, C_GRAY)
        surface.blit(et, (rect.centerx - et.get_width()//2, rect.centery))
        return

    # Column layout: Feature | Mean | Median | Std Dev | Min | Max
    feat_w = 134
    val_w  = (rect.width - feat_w) // 5
    cols   = [rect.x, rect.x + feat_w,
              rect.x + feat_w + val_w,
              rect.x + feat_w + val_w * 2,
              rect.x + feat_w + val_w * 3,
              rect.x + feat_w + val_w * 4]
    col_labels = ["Feature", "Mean", "Median", "Std Dev", "Min", "Max"]
    col_align  = ["left", "right", "right", "right", "right", "right"]

    row_h  = 52
    hdr_h  = 34
    y0     = rect.y + 8

    # Header band
    hdr_bg = pygame.Surface((rect.width, hdr_h), pygame.SRCALPHA)
    hdr_bg.fill((30, 70, 140, 200))
    surface.blit(hdr_bg, (rect.x, y0))
    pygame.draw.line(surface, C_OCEAN_FOAM,
                     (rect.x, y0 + hdr_h), (rect.right, y0 + hdr_h), 1)

    hf = _font(11, bold=True)
    for ci, (lbl, align) in enumerate(zip(col_labels, col_align)):
        t = hf.render(lbl, True, C_GOLD)
        if align == "left":
            tx = cols[ci] + 8
        else:
            col_right = cols[ci] + val_w - 6
            tx = col_right - t.get_width()
        surface.blit(t, (tx, y0 + (hdr_h - t.get_height()) // 2))

    # Metric rows
    def _stats(vals):
        if not vals:
            return ("—", "—", "—", "—", "—")
        mn  = min(vals)
        mx  = max(vals)
        avg = _st.mean(vals)
        med = _st.median(vals)
        sd  = _st.stdev(vals) if len(vals) > 1 else 0.0
        return avg, med, sd, mn, mx

    def _fmt(v, decimals=0):
        if v == "—":
            return "—"
        if decimals == 0:
            return f"{int(round(v)):,}"
        return f"{v:.{decimals}f}"

    rows = []
    if sessions:
        rows += [
            ("Score",        [s.score          for s in sessions], 0,  C_GOLD),
            ("Time (s)",     [s.time_played     for s in sessions], 0,  C_OCEAN_FOAM),
            ("Distance (km)",[s.distance        for s in sessions], 2,  (80, 200, 255)),
            ("Coins",        [s.coins_collected for s in sessions], 0,  (255, 210, 60)),
            ("Collisions",   [s.collisions      for s in sessions], 0,  C_RED_LIGHT),
        ]
    if collision_speeds:
        rows.append(("Crash Speed", collision_speeds, 1, (200, 120, 255)))

    vf  = _font(11)
    ff  = _font(11, bold=True)
    row_colors = [(15, 35, 70, 180), (10, 25, 55, 160)]

    for ri, (label, vals, dec, accent) in enumerate(rows):
        ry = y0 + hdr_h + ri * row_h

        # Alternating row background
        rb = pygame.Surface((rect.width, row_h), pygame.SRCALPHA)
        rb.fill((*row_colors[ri % 2][:3], row_colors[ri % 2][3]))
        surface.blit(rb, (rect.x, ry))

        # Accent left edge bar
        pygame.draw.rect(surface, accent, (rect.x, ry + 4, 3, row_h - 8), border_radius=2)

        # Row separator
        if ri > 0:
            pygame.draw.line(surface, (30, 60, 110),
                             (rect.x, ry), (rect.right, ry), 1)

        # Feature name
        lt = ff.render(label, True, C_WHITE)
        surface.blit(lt, (cols[0] + 10, ry + (row_h - lt.get_height()) // 2))

        # Stats values
        stats = _stats(vals)
        for ci, (sv, align) in enumerate(zip(stats, col_align[1:])):
            txt = _fmt(sv, dec)
            t   = vf.render(txt, True, accent)
            col_right = cols[ci + 1] + val_w - 6
            tx  = col_right - t.get_width()
            surface.blit(t, (tx, ry + (row_h - t.get_height()) // 2))

    # Sessions count footer
    n = len(sessions) if sessions else 0
    nf = _font(9)
    nt = nf.render(f"Based on {n} session{'s' if n != 1 else ''}", True, C_GRAY)
    surface.blit(nt, (rect.right - nt.get_width() - 8,
                      rect.y + rect.height - nt.get_height() - 6))


def draw_data_page(surface, sessions, collision_speeds, buttons, mouse_pos, tab=0):
    surface.fill(C_OCEAN_DEEP)

    # ── Header (title only) ──────────────────────────────────
    hdr = pygame.Surface((SCREEN_W, 46), pygame.SRCALPHA)
    hdr.fill((8, 18, 36, 235))
    surface.blit(hdr, (0, 0))

    t = _title_font(24).render("DATA  ANALYSIS", True, C_GOLD)
    surface.blit(t, (SCREEN_W//2 - t.get_width()//2, 8))

    # ── Tabs ─────────────────────────────────────────────────
    tab_rects = get_data_tab_rects()
    for i, (rect, label) in enumerate(zip(tab_rects, _DATA_TAB_LABELS)):
        active = (i == tab)
        col    = C_GOLD if active else C_OCEAN_FOAM
        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        bg.fill((*col, 45 if active else 12))
        surface.blit(bg, rect.topleft)
        pygame.draw.rect(surface, col, rect, 2 if active else 1, border_radius=5)
        if active:
            pygame.draw.rect(surface, col,
                             (rect.x + 2, rect.bottom - 3, rect.width - 4, 3),
                             border_radius=2)
        tt = _font(10, bold=active).render(label, True, col)
        surface.blit(tt, (rect.centerx - tt.get_width()//2,
                          rect.centery  - tt.get_height()//2))

    # ── Graph (full area, single tab) ────────────────────────
    graph_rect = pygame.Rect(8, 92, SCREEN_W - 16, 500)

    times = [s.time_played for s in sessions] if sessions else []
    pts   = [(s.distance, s.coins_collected) for s in sessions] if sessions else []

    if tab == 0:
        _draw_summary_table(surface, graph_rect, sessions, collision_speeds)
    elif tab == 1:
        _draw_histogram(surface, graph_rect, times,
                        f"Session Duration Distribution  ({len(times)} sessions)",
                        "Duration (s)", "Sessions", (100, 180, 255), bins=8)
    elif tab == 2:
        _draw_scatter(surface, graph_rect, pts,
                      f"Distance vs Coins  ({len(pts)} sessions)",
                      "Distance (km)", "Coins", C_GOLD)
    else:
        _draw_boxplot(surface, graph_rect, collision_speeds,
                      f"Speed at Collision  (n={len(collision_speeds)})",
                      "Speed (u/s)", (204, 68, 34))

    pygame.draw.line(surface, (40, 80, 130),
                     (SCREEN_W//4, SCREEN_H - 110),
                     (SCREEN_W*3//4, SCREEN_H - 110), 1)
    for key, rect in buttons.items():
        draw_button(surface, rect, key, hovered=rect.collidepoint(mouse_pos))
# ── Boat Shop ────────────────────────────────────────────────
# ── Boat shop layout constants ────────────────────────────────
_SHOP_PANEL_X      = 140
_SHOP_PANEL_Y      = 62
_SHOP_PANEL_W      = 200
_SHOP_PANEL_H      = 248
_SHOP_PANEL_BOTTOM = _SHOP_PANEL_Y + _SHOP_PANEL_H  # 310
_SHOP_NAME_Y       = 318
_SHOP_PRICE_Y      = 340
_SHOP_DESC_Y       = 360   # 3 lines × 14px
_SHOP_COLOR_Y      = 412   # first color row
_SHOP_COLOR_ROW_H  = 28
_SHOP_SWATCH_X0    = 65    # x start for first swatch (after label)
_SHOP_SWATCH_W     = 28
_SHOP_SWATCH_H     = 18
_SHOP_SWATCH_GAP   = 6


def get_shop_color_rects(boat: dict) -> dict:
    """Return {label: pygame.Rect} for every color swatch in this boat's palette.
    Keys: 'hull_0', 'hull_1', ..., 'sail_0', 'sail_1', ...
    Used by BOTH draw_boat_shop and the click handler so positions always match.
    """
    rects = {}
    y = _SHOP_COLOR_Y
    hp = boat.get("hull_palette")
    sp = boat.get("sail_palette")
    if hp:
        for ci in range(len(hp)):
            x = _SHOP_SWATCH_X0 + ci * (_SHOP_SWATCH_W + _SHOP_SWATCH_GAP)
            rects[f"hull_{ci}"] = pygame.Rect(x, y, _SHOP_SWATCH_W, _SHOP_SWATCH_H)
        y += _SHOP_COLOR_ROW_H
    if sp:
        for ci in range(len(sp)):
            x = _SHOP_SWATCH_X0 + ci * (_SHOP_SWATCH_W + _SHOP_SWATCH_GAP)
            rects[f"sail_{ci}"] = pygame.Rect(x, y, _SHOP_SWATCH_W, _SHOP_SWATCH_H)
    return rects


def draw_boat_shop(surface, catalog, owned, selected, wallet,
                   current_idx, color_pick, buttons, mouse_pos, tick=0):
    from .player_boat import (
        _draw_starter, _draw_sloop, _draw_galleon, _draw_manowar,
    )
    _DRAW_FN = {
        "starter": _draw_starter,
        "sloop":   _draw_sloop,
        "galleon": _draw_galleon,
        "manowar": _draw_manowar,
    }

    # ── Background ────────────────────────────────────────────
    surface.fill(C_OCEAN_DEEP)
    wave_limit = SCREEN_H - 140
    for i in range(10):
        y = (i * 68) % wave_limit
        al = 12 + i * 2
        for x in range(0, SCREEN_W, 10):
            wy = y + int(math.sin(x * 0.03 + i) * 3)
            if 0 <= wy < wave_limit:
                s = pygame.Surface((6, 1), pygame.SRCALPHA)
                s.fill((*C_OCEAN_FOAM, al))
                surface.blit(s, (x, wy))

    # ── Title bar ─────────────────────────────────────────────
    bar = pygame.Surface((SCREEN_W, 52), pygame.SRCALPHA)
    bar.fill((8, 18, 36, 220))
    surface.blit(bar, (0, 0))
    pygame.draw.line(surface, (40, 100, 160), (0, 52), (SCREEN_W, 52), 2)

    tf = _title_font(30)
    t = tf.render("BOAT  SHOP", True, C_GOLD)
    surface.blit(t, (SCREEN_W//2 - t.get_width()//2, 10))

    # Wallet: coin circle + number
    pygame.draw.circle(surface, C_GOLD, (SCREEN_W - 68, 26), 9)
    pygame.draw.circle(surface, C_GOLD_DARK, (SCREEN_W - 68, 26), 9, 2)
    wt = _font(12, bold=True).render(str(wallet), True, C_GOLD)
    surface.blit(wt, (SCREEN_W - 54, 20))

    # ── Boat preview panel ────────────────────────────────────
    boat        = catalog[current_idx]
    is_owned    = boat["id"] in owned
    is_selected = boat["id"] == selected

    PANEL_CX = SCREEN_W // 2
    PANEL_CY = _SHOP_PANEL_Y + _SHOP_PANEL_H // 2   # vertical center of panel

    panel = pygame.Rect(_SHOP_PANEL_X, _SHOP_PANEL_Y, _SHOP_PANEL_W, _SHOP_PANEL_H)
    p_bg = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
    p_bg.fill((10, 28, 58, 200))
    surface.blit(p_bg, panel.topleft)
    pygame.draw.rect(surface, (30, 70, 130), panel, 1, border_radius=8)

    # Animated water ripples inside panel
    for i in range(6):
        wy = panel.y + 20 + i * 48
        for x in range(panel.x + 4, panel.right - 4, 8):
            wwy = wy + int(math.sin(x * 0.04 + tick * 0.04 + i) * 2)
            if panel.y < wwy < panel.bottom:
                s = pygame.Surface((6, 1), pygame.SRCALPHA)
                s.fill((*C_OCEAN_FOAM, 18))
                surface.blit(s, (x, wwy))

    # Resolve current hull/sail colors for preview
    hp = boat.get("hull_palette")
    sp = boat.get("sail_palette")
    hull_c = tuple(hp[min(color_pick.get("hull_idx", 0), len(hp)-1)]) if hp else None
    sail_c = tuple(sp[min(color_pick.get("sail_idx", 0), len(sp)-1)]) if sp else None
    from .constants import C_WOOD
    if hull_c is None: hull_c = C_WOOD
    if sail_c is None: sail_c = (245, 238, 215)

    # Animated sway / bob
    sway = math.sin(tick * 0.03) * 0.06
    bob  = int(math.sin(tick * 0.04) * 1.5)
    fn   = _DRAW_FN.get(boat["id"], _draw_starter)
    fn(surface, PANEL_CX, PANEL_CY + bob, 48, 74, tick, sway, hull_c, sail_c)

    # ── Info below preview panel (always centered for all boats) ─
    # Name
    nf = _title_font(18)
    nt = nf.render(boat["name"], True, C_WHITE)
    surface.blit(nt, (SCREEN_W//2 - nt.get_width()//2, _SHOP_NAME_Y))

    # Price / ownership badge
    if boat["price"] == 0:
        badge_text = "FREE";   badge_col = C_GREEN
    elif is_owned:
        badge_text = "OWNED";  badge_col = (80, 200, 120)
    elif wallet >= boat["price"]:
        badge_text = f"{boat['price']} coins"; badge_col = C_GOLD
    else:
        badge_text = f"{boat['price']} coins"; badge_col = C_RED_LIGHT

    bt = _font(10, bold=True).render(badge_text, True, badge_col)
    bx = SCREEN_W//2 - bt.get_width()//2
    by = _SHOP_PRICE_Y
    pill = pygame.Surface((bt.get_width() + 10, bt.get_height() + 4), pygame.SRCALPHA)
    pill.fill((*badge_col, 35))
    surface.blit(pill, (bx - 5, by - 2))
    pygame.draw.rect(surface, badge_col,
                     (bx - 5, by - 2, bt.get_width() + 10, bt.get_height() + 4),
                     1, border_radius=3)
    surface.blit(bt, (bx, by))

    # Description lines (centered)
    af = _font(9)
    ay = _SHOP_DESC_Y
    for line in boat["desc"].split("\n"):
        al = af.render(line, True, C_OCEAN_FOAM)
        surface.blit(al, (SCREEN_W//2 - al.get_width()//2, ay))
        ay += 14

    # ── Color pickers — positions from get_shop_color_rects ──
    swatch_rects = get_shop_color_rects(boat)
    if hp:
        lbl = _font(9, bold=True).render("HULL", True, C_GRAY)
        surface.blit(lbl, (16, _SHOP_COLOR_Y + 1))
        for ci, col in enumerate(hp):
            rect     = swatch_rects[f"hull_{ci}"]
            is_pick  = (ci == color_pick.get("hull_idx", 0))
            if is_pick:
                glow = pygame.Surface((rect.width + 8, rect.height + 4), pygame.SRCALPHA)
                glow.fill((*col, 60))
                surface.blit(glow, (rect.x - 4, rect.y - 2))
            pygame.draw.rect(surface, col, rect, border_radius=4)
            border_col = C_WHITE if is_pick else (50, 80, 120)
            pygame.draw.rect(surface, border_col, rect, 2 if is_pick else 1, border_radius=4)

    sail_row_y = _SHOP_COLOR_Y + (_SHOP_COLOR_ROW_H if hp else 0)
    if sp:
        lbl = _font(9, bold=True).render("SAIL", True, C_GRAY)
        surface.blit(lbl, (16, sail_row_y + 1))
        for ci, col in enumerate(sp):
            rect     = swatch_rects[f"sail_{ci}"]
            is_pick  = (ci == color_pick.get("sail_idx", 0))
            if is_pick:
                glow = pygame.Surface((rect.width + 8, rect.height + 4), pygame.SRCALPHA)
                glow.fill((*col, 60))
                surface.blit(glow, (rect.x - 4, rect.y - 2))
            pygame.draw.rect(surface, col, rect, border_radius=4)
            border_col = C_WHITE if is_pick else (50, 80, 120)
            pygame.draw.rect(surface, border_col, rect, 2 if is_pick else 1, border_radius=4)

    # ── Selected badge ────────────────────────────────────────
    if is_selected:
        sel_y = _SHOP_COLOR_Y
        if hp: sel_y += _SHOP_COLOR_ROW_H
        if sp: sel_y += _SHOP_COLOR_ROW_H
        st = _font(10, bold=True).render("* SELECTED *", True, C_GREEN)
        surface.blit(st, (SCREEN_W//2 - st.get_width()//2, sel_y + 4))

    # ── Button area solid backdrop (stops wave bleed) ─────────
    btn_area_top = SCREEN_H - 140
    btn_bg = pygame.Surface((SCREEN_W, 140), pygame.SRCALPHA)
    btn_bg.fill((*C_OCEAN_DEEP, 230))
    surface.blit(btn_bg, (0, btn_area_top))
    pygame.draw.line(surface, (30, 70, 130), (20, btn_area_top), (SCREEN_W - 20, btn_area_top), 1)

    # ── Dot indicators (ONE set, correctly centered) ───────────
    dot_y = btn_area_top + 14
    n = len(catalog)
    for i in range(n):
        dx  = SCREEN_W//2 - ((n - 1) * 20)//2 + i * 20
        col = C_GOLD if i == current_idx else (50, 85, 130)
        r   = 5 if i == current_idx else 3
        pygame.draw.circle(surface, col, (dx, dot_y), r)
        if i == current_idx:
            pygame.draw.circle(surface, C_GOLD, (dx, dot_y), r, 1)

    # ── Buttons ───────────────────────────────────────────────
    for key, rect in buttons.items():
        if key in ("<", ">"):
            hov = rect.collidepoint(mouse_pos)
            bg  = pygame.Surface(rect.size, pygame.SRCALPHA)
            bg.fill((*C_OCEAN_DEEP, 200 if hov else 160))
            surface.blit(bg, rect.topleft)
            pygame.draw.rect(surface, C_OCEAN_FOAM, rect, 1, border_radius=6)
            at = _font(20, bold=True).render(key, True, C_WHITE)
            surface.blit(at, (rect.centerx - at.get_width()//2,
                               rect.centery - at.get_height()//2))
        elif key in ("BUY", "SELECT", "OWNED", "PLAY"):
            if   key == "OWNED":  col = C_GRAY
            elif key == "SELECT": col = C_GREEN
            elif key == "PLAY":   col = C_GOLD
            else: col = C_GOLD if wallet >= boat["price"] else C_RED_LIGHT
            draw_button(surface, rect, key, color=col,
                        hovered=rect.collidepoint(mouse_pos))
        else:
            draw_button(surface, rect, key, hovered=rect.collidepoint(mouse_pos))


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