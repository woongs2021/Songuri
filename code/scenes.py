import math, numpy as np, skia
import lib
from lib import *

# ================= STORYBOARD (seconds) =================
T_TITLE, T_MISSION, T_G0, GL, T_NEOL, T_MOON, T_END = 4.0, 7.5, 11.0, 4.5, 38.0, 45.5, 50.0
GAMES = ['윷놀이', '제기차기', '투호', '팽이치기', '연날리기', '강강술래']
ANCH = [(1180, 640), (1010, 380), (1350, 470), (1040, 660), (1340, 300), (960, 620)]
HUD_ICON = (92, 76)
EVENTS = []   # (time, name, param)
IMPACTS = []  # (time, strength)
def ev(t, n, p=0): EVENTS.append((t, n, p))
def imp(t, s): IMPACTS.append((t, s))

# reward arrivals
ARR = []
for i in range(6):
    R = T_G0 + i * GL + 3.5
    ev(R, 'burst'); ev(R + 0.05, 'plus')
    for j in range(10):
        a = R + 0.25 + j * 0.04 + 0.35
        ARR.append(a); ev(a, 'get', i * 10 + j)
ARR.sort()
def count_at(t): return sum(1 for a in ARR if a <= t)

# ================= camera =================
class Cam:
    def __init__(self, zoom=1.0, cx=W / 2, cy=H / 2, rot=0.0):
        self.zoom, self.cx, self.cy, self.rot = zoom, cx, cy, rot
    def apply(self, c, t):
        sx, sy = shake(t)
        c.translate(W / 2 + sx, H / 2 + sy); c.rotate(self.rot + sx * 0.03); c.scale(self.zoom, self.zoom)
        c.translate(-self.cx, -self.cy)
    def scr(self, x, y):
        return ((x - self.cx) * self.zoom + W / 2, (y - self.cy) * self.zoom + H / 2)

def shake(t):
    sx = sy = 0.0
    for ti, s in IMPACTS:
        d = t - ti
        if 0 <= d < 0.6:
            k = s * math.exp(-d * 9)
            sx += hn(int(t * 60) * 3 + int(ti * 10)) * k
            sy += hn(int(t * 60) * 7 + int(ti * 10) + 1) * k
    return sx, sy

def flash(c, t, t0, dur=0.25, color=PAPER, amax=230):
    d = t - t0
    if 0 <= d < dur: c.drawRect(skia.Rect(0, 0, W, H), P(color, amax * (1 - d / dur)))

def speedlines(c, t, n=26, color=INK, a=90, cx=W / 2, cy=H / 2, inner=420, seed=0):
    for k in range(n):
        ang = hn(seed + k * 3 + int(t * 15)) * math.pi
        r0 = inner + (hn(seed + k * 5 + int(t * 15)) + 1) * 120
        x0, y0 = cx + math.cos(ang) * r0, cy + math.sin(ang) * r0
        x1, y1 = cx + math.cos(ang) * 1400, cy + math.sin(ang) * 1400
        c.drawLine(x0, y0, x1, y1, P(color, a, 3 + (k % 3)))

rng = np.random.default_rng(3)
STARS = [(rng.uniform(0, W), rng.uniform(0, H * 0.75), rng.uniform(4, 11), rng.uniform(0, 6.28)) for _ in range(70)]

def night_bg(c, t, top=NAVY, bot=NAVY2):
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)], [col(top), col(bot)])
    c.drawRect(skia.Rect(-400, -600, W + 400, H + 400), skia.Paint(Shader=sh))

def stars(c, t, a=255, dy=0.0):
    for i, (x, y, s, ph) in enumerate(STARS):
        tw = 0.6 + 0.4 * math.sin(t * 4 + ph)
        yy = (y + dy) % (H + 200) - 100
        star(c, x, yy, s * tw, MOON, a * (0.5 + 0.5 * tw))

def village(c, y0=900, seed=0):
    shape(c, [(-300, y0), (200, y0 - 120), (620, y0 - 60), (1000, y0 - 150), (1420, y0 - 70), (1800, y0 - 140), (2300, y0 - 40), (2300, H + 400), (-300, H + 400)], NAVY3, INK, 4, seed)
    for i, (x, w) in enumerate([(300, 220), (560, 180), (1360, 240), (1640, 190)]):
        yy = y0 - 40 + (i % 2) * 20
        hanok_roof(c, x, yy, w, (30, 36, 56), seed + i)
        c.drawRect(skia.Rect(x - 20, yy + 20, x + 14, yy + 48), P((246, 205, 130), 220))

def ground(c, y=820, color=INK, seed=0):
    ink(c, [(-300, y), (W + 300, y)], color, 4, seed=seed, amp=2.5)

# ================= HUD =================
def hud(c, t):
    if t < 9.8 or t > T_MOON + 2.3: return
    k = eout(seg(t, 9.8, 10.2)) * (1 - ein(seg(t, T_MOON + 1.9, T_MOON + 2.3)))
    oy = -160 * (1 - k)
    n = count_at(t)
    last = max([a for a in ARR if a <= t], default=-9)
    pop = 1 + 0.35 * math.exp(-(t - last) * 14) if t - last < 0.5 else 1
    c.save(); c.translate(0, oy)
    # left panel
    shape(c, rect_pts(36, 26, 360, 100), PAPER, INK, 3, seed=900, amp=1.5, a=225)
    draw_songpyeon(c, HUD_ICON[0], HUD_ICON[1] + 6, 58 * pop, SPW, seed=901)
    text(c, '송편', 134, 84, 30, INK, align='l', light=True)
    c.save(); c.translate(300, 90); c.scale(pop, pop)
    text(c, f'× {n}', 0, 0, 56, CLAY_D, light=True)
    c.restore()
    # right panel: moon gauge
    f = 0.5 + 0.5 * n / 60
    shape(c, rect_pts(1414, 26, 470, 100), PAPER, INK, 3, seed=902, amp=1.5, a=225)
    mx, my, mr = 1470, 76, 30
    c.drawCircle(mx, my, mr, P(NAVY2))
    c.save(); c.clipRect(skia.Rect(mx + mr - 2 * mr * f, my - mr, mx + mr, my + mr))
    c.drawCircle(mx, my, mr, P(MOON)); c.restore()
    ink(c, circle_pts(mx, my, mr), INK, 2.5, True, seed=903, amp=0.8, double=False)
    text(c, '달 채우기', 1520, 64, 26, INK, align='l', light=True)
    text(c, f'{int(round(f * 100))}%', 1860, 66, 34, CLAY_D, align='r', light=True)
    bx, by, bw = 1520, 86, 340
    c.drawRoundRect(skia.Rect(bx, by, bx + bw, by + 16), 8, 8, P(NAVY2, 60))
    c.drawRoundRect(skia.Rect(bx, by, bx + bw * f, by + 16), 8, 8, P(CLAY))
    ink(c, rect_pts(bx, by, bw, 16), INK, 2, True, seed=904, amp=0.8, double=False)
    c.restore()

def reward(c, t, i):
    R = T_G0 + i * GL + 3.5
    if not (R <= t < R + 1.0): return
    ax, ay = ANCH[i]
    d = t - R
    # +10
    k = eback(seg(d, 0, 0.25))
    a = 255 * (1 - seg(d, 0.75, 1.0))
    c.save(); c.translate(ax, ay - 150 - 40 * d); c.scale(k, k)
    text(c, '+10', 0, 0, 96, CLAY, a=a, shadow=(DARK, 40 * a / 255))
    c.restore()
    for j in range(10):
        ang = j * 2 * math.pi / 10 + 0.3
        bx, by = ax + math.cos(ang) * 150, ay + math.sin(ang) * 110
        s0 = R + 0.25 + j * 0.04
        if d < 0.25:
            u = eout(d / 0.25); x, y = lerp(ax, bx, u), lerp(ay, by, u); sc = 70 * u
        elif t < s0:
            x, y, sc = bx, by + math.sin(t * 20 + j) * 4, 70
        else:
            u = seg(t, s0, s0 + 0.35)
            if u >= 1: continue
            e = ein(u) if False else u * u
            x = lerp(bx, HUD_ICON[0], e); y = lerp(by, HUD_ICON[1], e) - math.sin(u * math.pi) * 140
            sc = lerp(70, 40, u)
        draw_songpyeon(c, x, y, sc, SP_COLS[j % 3], rot=math.sin(t * 9 + j) * 0.5, seed=j + 30)

def card(c, t, i):
    d = t - (T_G0 + i * GL)
    if not (0 <= d < 0.55): return
    edge = -200 + eio(seg(d, 0.36, 0.55)) * (W + 500)
    c.save()
    pth = skia.Path(); pth.moveTo(edge + 200, 0); pth.lineTo(W + 10, 0); pth.lineTo(W + 10, H); pth.lineTo(edge - 100, H); pth.close()
    c.clipPath(pth, skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect(0, 0, W, H), P(CLAY))
    paper_overlay(c, 170)
    s = 1.12 - 0.12 * eout(seg(d, 0, 0.3))
    c.translate(W / 2, H / 2); c.scale(s, s)
    text(c, f'ROUND {i + 1}', 0, -110, 40, PAPER, spacing=14, light=True)
    ink(c, [(-120, -80), (120, -80)], PAPER, 2, seed=i, amp=1)
    text(c, GAMES[i], 0, 60, 170, PAPER)
    for k in range(3):
        draw_songpyeon(c, -90 + k * 90, 170, 56, SP_COLS[k], seed=k + i * 5)
    c.restore()
    ink(c, [(edge + 200, 0), (edge - 100, H)], INK, 5, seed=77, amp=3)

# ================= SCENE: OPENING (0-4) =================
ev(0.0, 'gong'); ev(0.05, 'draw'); ev(0.9, 'pop'); ev(2.4, 'boom'); imp(2.4, 18); ev(2.45, 'boing'); ev(3.2, 'sparkle'); imp(3.2, 6)
def s_open(c, t):
    c.clear(col(IVORY))
    z = 1.0 + 0.1 * eout(seg(t, 3.2, 3.35)) - 0.04 * seg(t, 3.35, 4.0)
    cam = Cam(z, 960, 540); c.save(); cam.apply(c, t)
    cx, cy, r = 960, 470, 170
    if t < 2.4:
        pul = 1 + 0.06 * math.exp(-((t - 1.5) % 0.5) * 8) * (t > 1.4)
        sq = seg(t, 2.1, 2.4)
        c.save(); c.translate(cx, cy); c.scale(pul * (1 + 0.25 * sq), pul * (1 - 0.2 * sq)); c.translate(-cx, -cy)
        pts = circle_pts(cx, cy, r, a0=-math.pi / 2, a1=1.5 * math.pi)
        glow(c, cx, cy, r * 1.8, MOON, 120 * seg(t, 0.8, 1.2))
        if t > 0.85: c.drawCircle(cx, cy, r, P(MOON, 255 * seg(t, 0.85, 1.1)))
        ink(c, partial(pts, eio(seg(t, 0.05, 0.9))), CLAY, 8, seed=1, amp=2.2)
        k = eback(seg(t, 0.9, 1.25))
        if k > 0:
            draw_songpyeon(c, cx, cy + 15, 170 * k, CLAY_L, seed=4, lw=6)
        for m in range(5):
            kk = eback(seg(t, 1.2 + m * 0.08, 1.45 + m * 0.08))
            ang = -math.pi / 2 + (m - 2) * 0.55
            if kk > 0: sparkle(c, cx + math.cos(ang) * (r + 55), cy + math.sin(ang) * (r + 55), 16 * kk, CLAY)
        c.restore()
    else:
        d = t - 2.4
        for m in range(14):
            ang = m * 2 * math.pi / 14
            rr = r + eout(seg(d, 0, 0.6)) * 600
            a = 255 * (1 - seg(d, 0.3, 0.6))
            a0, a1 = ang, ang + 0.3
            ink(c, circle_pts(cx + math.cos(ang) * (rr - r), cy + math.sin(ang) * (rr - r), r, a0=a0, a1=a1, n=5), CLAY, 8, seed=m, a=a)
        for m in range(10):
            ang = m * 0.63 + 0.2
            u = eout(seg(d, 0, 0.7))
            if d < 0.8:
                draw_songpyeon(c, cx + math.cos(ang) * 520 * u, cy + math.sin(ang) * 360 * u + 300 * d * d, 60, SP_COLS[m % 3], rot=d * 8 + m, seed=m, a=255 * (1 - seg(d, 0.55, 0.8)))
        k = eback(seg(d, 0, 0.4), 2.4)
        pose = 'jump' if d < 0.55 else ('point' if t > 3.15 else 'idle')
        hop = -math.sin(seg(d, 0, 0.55) * math.pi) * 120
        sy = 1 - 0.18 * math.exp(-max(0, d - 0.55) * 14) if d > 0.55 else 1
        draw_char(c, cx, 690 + hop, px=13 * k, pose=pose, sx=1 / sy if d > 0.55 else 1, sy=sy)
        if t > 3.15:
            kk = eback(seg(t, 3.15, 3.4))
            sparkle(c, cx + 150, 390, 36 * kk, CLAY); sparkle(c, cx + 210, 450, 18 * kk, MOON_D)
            text(c, '2026 한가위', cx, 820, 44, INK, a=255 * seg(t, 3.2, 3.5), light=True, spacing=6)
    c.restore()
    paper_overlay(c)
    flash(c, t, 2.4, 0.3)

# ================= SCENE: TITLE (4-7.5) =================
TITLE = '송구리의 한가위'
for i, ch in enumerate(TITLE):
    if ch != ' ': ev(T_TITLE + 0.15 + i * 0.08, 'tick', i)
ev(T_TITLE + 0.05, 'whoosh'); ev(T_TITLE + 1.0, 'chime'); ev(T_TITLE + 3.15, 'whoosh')
def s_title(c, t):
    d = t - T_TITLE
    c.clear(col(CLAY))
    z = 1.0 + 0.05 * d / 3.5 + 0.9 * ein(seg(d, 3.15, 3.5))
    cam = Cam(z, 960, 540, rot=-3 * ein(seg(d, 3.15, 3.5))); c.save(); cam.apply(c, t)
    # floating songpyeon
    for m in range(9):
        x = (m * 237 + d * 60 * (1 + m % 3)) % 2200 - 140
        y = 150 + (m * 173) % 800 + math.sin(d * 2 + m) * 20
        if abs(y - 520) < 160 and 300 < x < 1650: y += 330
        draw_songpyeon(c, x, y, 50 + (m % 3) * 18, SP_COLS[m % 3], rot=math.sin(d + m) * 0.4, seed=m + 60, a=230)
    size = 150; tw = text_w(TITLE, size)
    x = 960 - tw / 2
    for i, ch in enumerate(TITLE):
        w = font(size).measureText(ch)
        u = seg(d, 0.15 + i * 0.08, 0.45 + i * 0.08)
        if u > 0:
            k = eback(u)
            c.save(); c.translate(x + w / 2, 520 - 70 * (1 - k)); c.scale(0.6 + 0.4 * k, 0.6 + 0.4 * k)
            text(c, ch, 0, 0, size, PAPER, a=255 * min(1, u * 3), shadow=(DARK, 50))
            c.restore()
        x += w
    ul = seg(d, 0.8, 1.2)
    if ul > 0: ink(c, partial([(960 - tw / 2 + i * tw / 20, 565 + math.sin(i) * 3) for i in range(21)], ul), PAPER, 3, seed=5)
    text(c, 'presented by Claude', 960, 650, 46, PAPER, a=255 * seg(d, 1.0, 1.4), light=True, spacing=4)
    beat = math.exp(-((d + 0.0) % 0.5) * 10)
    draw_char(c, 330, 930 - 40 * beat, px=12, pose='up' if int(d * 2) % 2 else 'idle', sy=1 - 0.08 * beat, sx=1 + 0.08 * beat)
    draw_char(c, 1600, 930 - 40 * math.exp(-((d + 0.25) % 0.5) * 10), px=9, pose='point', flip=True)
    c.restore()
    paper_overlay(c, 170)
    flash(c, t, T_TITLE, 0.2)
    if d > 3.3: c.drawRect(skia.Rect(0, 0, W, H), P(NAVY, 255 * seg(d, 3.3, 3.5)))

# ================= SCENE: MISSION (7.5-11) =================
ev(T_MISSION + 0.0, 'night'); ev(T_MISSION + 1.3, 'stamp'); imp(T_MISSION + 1.3, 16); ev(T_MISSION + 2.3, 'whoosh')
def s_mission(c, t):
    d = t - T_MISSION
    z = lerp(1.7, 1.0, eout(seg(d, 0, 1.1)))
    cam = Cam(z, 960, lerp(330, 540, eout(seg(d, 0, 1.1)))); c.save(); cam.apply(c, t)
    night_bg(c, t); stars(c, t)
    draw_moon(c, 960, 330, 190, seed=10)
    if d > 1.0:
        text(c, '?', 870, 360, 90, MOON, a=160 * seg(d, 1.0, 1.4) * (0.6 + 0.4 * math.sin(d * 6)))
    village(c, 960)
    draw_char(c, 960, 905, px=7, pose='idle', blink=(int(d * 10) % 17 == 0))
    c.restore()
    paper_overlay(c, 120); vignette(c, 110)
    u = seg(d, 1.0, 1.3)
    if u > 0:
        k = lerp(1.9, 1.0, eout(seg(d, 1.1, 1.3))) if d < 1.3 else 1
        c.save(); c.translate(960, 690); c.scale(k, k)
        a = 255 * min(1, u * 2)
        shape(c, rect_pts(-560, -110, 1120, 170), DARK, MOON, 3, seed=20, amp=2, a=a * 0.85, sa=a)
        text(c, 'MISSION', 0, -58, 30, CLAY, a=a, spacing=12, light=True)
        text(c, '송편을 모아 달을 채워라!', 0, 30, 76, PAPER, a=a)
        c.restore()
    flash(c, t, T_MISSION + 1.3, 0.2, amax=120)

# ================= GAME 1: 윷놀이 =================
G = [T_G0 + i * GL for i in range(6)]
ev(G[0] + 0.85, 'throw'); ev(G[0] + 2.1, 'clatter'); imp(G[0] + 2.1, 14); ev(G[0] + 2.4, 'stamp')
STICK_LAND = [(930, 700, 0.35), (1100, 735, -0.15), (1250, 690, 0.12), (1400, 740, -0.3)]
def draw_stick(c, x, y, ang, flip_ph, seed):
    L, Wd = 200, 40
    fc = math.cos(flip_ph)
    flat = fc > 0
    w = max(6, Wd * abs(fc))
    pts = [(-L / 2, -w / 2), (L / 2, -w / 2), (L / 2 + 8, 0), (L / 2, w / 2), (-L / 2, w / 2), (-L / 2 - 8, 0)]
    pts = xform(pts, x, y, ang)
    shape(c, pts, WOOD_L if flat else WOOD, INK, 3.5, seed=seed, amp=1.2)
    if flat and abs(fc) > 0.6:
        for m in (-1, 0, 1):
            mx, my = xform([(m * 55, 0)], x, y, ang)[0]
            s = 9
            ink(c, [(mx - s, my - s), (mx + s, my + s)], WOOD_D, 3, seed=seed + m, amp=0.5, double=False)
            ink(c, [(mx - s, my + s), (mx + s, my - s)], WOOD_D, 3, seed=seed + m + 9, amp=0.5, double=False)
    elif not flat:
        ln = xform([(-L / 2 + 20, -w * 0.15), (L / 2 - 20, -w * 0.15)], x, y, ang)
        ink(c, ln, WOOD_D, 2, seed=seed + 3, amp=0.6, double=False)

def g_yut(c, t):
    d = t - G[0]
    c.clear(col(IVORY))
    punch = eout(seg(d, 2.1, 2.3))
    cam = Cam(1.0 + 0.18 * punch, lerp(960, 1160, punch), lerp(540, 620, punch)); c.save(); cam.apply(c, t)
    ground(c, 830, seed=1)
    # 멍석 (straw mat)
    mat = [(820, 640), (1500, 640), (1560, 800), (760, 800)]
    shape(c, mat, STRAW, INK, 4, seed=2)
    for k in range(1, 9):
        y = lerp(640, 800, k / 9)
        ink(c, [(lerp(820, 760, k / 9) + 10, y), (lerp(1500, 1560, k / 9) - 10, y)], STRAW_D, 2, seed=k + 3, amp=1.2, double=False)
    # 윷판 hint on mat corner: small circle of dots
    pose = 'throw' if 0.6 < d < 1.1 else ('up' if d > 2.4 else 'idle')
    draw_char(c, 470, 830, px=12, pose=pose, sy=1 - 0.1 * math.exp(-max(0, d - 2.4) * 10) * (d > 2.4))
    for k, (lx, ly, la) in enumerate(STICK_LAND):
        t0, t1 = 0.9, 2.1 - 0.04 * k
        if d < t0:
            if d > 0.5:
                hx, hy = 560, 560
                draw_stick(c, hx + k * 6 - 10, hy + k * 10, 1.4, 0.3, seed=k)
            continue
        u = seg(d, t0, t1)
        x = lerp(580, lx, u); y = lerp(560, ly, u) - math.sin(u * math.pi) * 480
        if u < 1:
            ang = la + (1 - u) * (6 + k)
            ph = (1 - u) * (14 + k * 3)
        else:
            bounce = math.exp(-(d - t1) * 12) * math.sin((d - t1) * 40) * 0.08
            ang = la + bounce; ph = 0.0
            y -= abs(math.sin((d - t1) * 25)) * 30 * math.exp(-(d - t1) * 10)
        draw_stick(c, x, y, ang, ph, seed=k * 10)
    if d > 2.4:
        k = lerp(2.0, 1.0, eout(seg(d, 2.4, 2.6)))
        c.save(); c.translate(1170, 520); c.scale(k, k)
        text(c, '윷!', 0, 0, 170, CLAY_D, shadow=(DARK, 40))
        c.restore()
        
    c.restore()
    text(c, '네 가락이 모두 젖혀지면 윷 — 네 칸 전진', 960, 1010, 34, INK, a=255 * seg(d, 2.6, 2.9) * (1 - seg(d, 3.3, 3.5)), light=True)
    paper_overlay(c)
    flash(c, t, G[0] + 2.1, 0.15, amax=140)

# ================= GAME 2: 제기차기 =================
KICKS = [G[1] + 0.75 + j * 0.34 for j in range(8)]
for j, k in enumerate(KICKS): ev(k, 'kick', j); imp(k, 3 + j * 0.6)
FOOT = (900, 790)
def g_jegi(c, t):
    d = t - G[1]
    c.clear(col(CLAY_L))
    z = 1.0 + 0.012 * sum(1 for k in KICKS if k <= t)
    cam = Cam(z, 960, 560); c.save(); cam.apply(c, t)
    ground(c, 840, seed=11)
    kicking = any(0 <= t - k < 0.12 for k in KICKS)
    draw_char(c, 1000, 840, px=13, pose='kick' if kicking else 'idle', flip=False)
    # jegi position
    prev = [k for k in KICKS if k <= t]
    if not prev:
        u = seg(d, 0.2, 0.75); jx, jy = lerp(1100, FOOT[0], u), lerp(250, FOOT[1], u * u); vy = 1
    elif len(prev) < len(KICKS):
        k0 = prev[-1]; k1 = KICKS[len(prev)]
        u = (t - k0) / (k1 - k0)
        jx = FOOT[0] + math.sin(u * math.pi) * 20; jy = FOOT[1] - 4 * 330 * u * (1 - u); vy = u - 0.5
    else:
        u = t - prev[-1]; jx = FOOT[0] + u * 200; jy = FOOT[1] - 1600 * u + 900 * u * u; vy = -1
    # draw jegi: coin + paper tassel (strands trail above)
    for m in range(9):
        ang = -math.pi / 2 + (m - 4) * 0.16 + math.sin(t * 25 + m) * 0.08
        ln = 115 + (m % 3) * 14
        ex, ey = jx + math.cos(ang) * ln, jy + math.sin(ang) * ln * (1.0 if vy >= 0 else 0.85)
        mx, my = (jx + ex) / 2 + math.sin(t * 30 + m) * 8, (jy + ey) / 2
        ink(c, [(jx, jy), (mx, my), (ex, ey)], [PAPER, CLAY, SPP][m % 3], 7, seed=m, amp=1.2, double=False)
        ink(c, [(jx, jy), (mx, my), (ex, ey)], INK, 1.5, seed=m + 40, amp=1.2, double=False, a=120)
    c.drawCircle(jx, jy + 4, 21, P((176, 140, 70)))
    c.drawRect(skia.Rect(jx - 5, jy - 1, jx + 5, jy + 9), P(INK))
    ink(c, circle_pts(jx, jy + 4, 21), INK, 3, True, seed=5, amp=0.8, double=False)
    if prev and kicking:
        for m in range(6):
            a = m * 1.05
            ink(c, [(FOOT[0] + math.cos(a) * 40, FOOT[1] + math.sin(a) * 40), (FOOT[0] + math.cos(a) * 75, FOOT[1] + math.sin(a) * 75)], CLAY_D, 4, seed=m, double=False)
    c.restore()
    n = len(prev)
    if n:
        k = 1 + 0.4 * math.exp(-(t - prev[-1]) * 12)
        c.save(); c.translate(1480, 480); c.scale(k, k)
        text(c, str(n), 0, 0, 260, CLAY_D, shadow=(DARK, 35))
        c.restore()
        text(c, '번 연속!', 1480, 560, 44, INK, light=True)
    text(c, '발 안쪽으로 차서 땅에 떨어뜨리지 않기', 960, 1010, 34, INK, a=255 * seg(d, 0.6, 0.9) * (1 - seg(d, 3.3, 3.5)), light=True)
    paper_overlay(c)

# ================= GAME 3: 투호 =================
THROWS = [G[2] + 0.8, G[2] + 1.55, G[2] + 2.3]
for k in THROWS: ev(k, 'throw'); ev(k + 0.55, 'tok'); imp(k + 0.55, 8)
POT = (1350, 830)
MOUTH = (1350, 470)
def draw_pot(c, seed=0):
    x, y = POT
    body = [(x - 150, y - 150), (x - 120, y - 40), (x - 80, y), (x + 80, y), (x + 120, y - 40), (x + 150, y - 150),
            (x + 110, y - 250), (x + 38, y - 290), (x + 30, y - 350), (x + 46, y - 360), (x - 46, y - 360), (x - 30, y - 350), (x - 38, y - 290), (x - 110, y - 250)]
    shape(c, body, CELADON, INK, 4.5, seed=seed)
    ink(c, [(x - 132, y - 190), (x + 132, y - 190)], CELADON_D, 3, seed=seed + 1)
    ink(c, [(x - 138, y - 120), (x + 138, y - 120)], CELADON_D, 3, seed=seed + 2)
    for sgn in (-1, 1):  # 귀 (ears)
        ear = [(x + sgn * 38, y - 300), (x + sgn * 72, y - 300), (x + sgn * 72, y - 346), (x + sgn * 60, y - 352), (x + sgn * 50, y - 346), (x + sgn * 50, y - 320), (x + sgn * 38, y - 320)]
        shape(c, ear, CELADON, INK, 3.5, seed=seed + 5 + sgn)
    shape(c, ellipse_pts(x, y - 360, 46, 12), (60, 70, 66), INK, 3, seed=seed + 9)

def draw_arrow(c, x, y, ang, seed=0):
    L = 200
    tip = (x + math.cos(ang) * L / 2, y + math.sin(ang) * L / 2)
    tail = (x - math.cos(ang) * L / 2, y - math.sin(ang) * L / 2)
    ink(c, [tail, tip], WOOD_D, 5, seed=seed, amp=0.8)
    for s in (-1, 1):
        fx = tail[0] + math.cos(ang) * 40 + math.cos(ang + s * 2.5) * 26
        fy = tail[1] + math.sin(ang) * 40 + math.sin(ang + s * 2.5) * 26
        shape(c, [tail, (tail[0] + math.cos(ang) * 45, tail[1] + math.sin(ang) * 45), (fx, fy)], CLAY, INK, 2.5, seed=seed + s)

def g_tuho(c, t):
    d = t - G[2]
    c.clear(col(IVORY))
    cam = Cam(1.0 + 0.04 * sum(1 for k in THROWS if k + 0.55 <= t), 1000, 560); c.save(); cam.apply(c, t)
    ground(c, 830, seed=21)
    # rules hint: distance marker
    ink(c, [(620, 850), (1180, 850)], INK, 2, seed=22, amp=1, a=120)
    pose = 'throw' if any(0 <= t - k < 0.2 for k in THROWS) else 'idle'
    draw_char(c, 470, 830, px=12, pose=pose)
    stuck = []
    for i, k in enumerate(THROWS):
        u = (t - k) / 0.55
        if u < 0:
            continue
        if u < 1:
            sx, sy = 580, 580
            x = lerp(sx, MOUTH[0], u); y = lerp(sy, MOUTH[1] - 20, u) - math.sin(u * math.pi) * 330
            dx = MOUTH[0] - sx; dy = (MOUTH[1] - 20 - sy) - math.cos(u * math.pi) * math.pi * 330
            ang = math.atan2(dy, dx)
            draw_arrow(c, x, y, ang, seed=i)
        else:
            stuck.append(i)
    for i in stuck:  # arrows behind front of pot: draw sticking out
        ang = math.pi / 2 - 0.12 + i * 0.12
        draw_arrow(c, MOUTH[0] - 8 + i * 8, MOUTH[1] - 60, ang, seed=i)
    draw_pot(c, seed=30)
    for i in stuck:
        dd = t - THROWS[i] - 0.55
        if dd < 0.6:
            k = eback(seg(dd, 0, 0.2))
            c.save(); c.translate(MOUTH[0] + 230, MOUTH[1] - 140 - dd * 60); c.scale(k, k)
            text(c, '명중!', 0, 0, 80, CLAY_D, a=255 * (1 - seg(dd, 0.4, 0.6)))
            c.restore()
    c.restore()
    text(c, '항아리 입구에 화살을 던져 넣기', 960, 1010, 34, INK, a=255 * seg(d, 0.6, 0.9) * (1 - seg(d, 3.3, 3.5)), light=True)
    if d > 2.95:
        k = eback(seg(d, 2.95, 3.15))
        c.save(); c.translate(760, 330); c.scale(k, k); text(c, '3발 모두 명중', 0, 0, 90, INK); c.restore()
    paper_overlay(c)

# ================= GAME 4: 팽이치기 =================
WHIPS = [G[3] + 0.9, G[3] + 1.6, G[3] + 2.3, G[3] + 2.8]
for k in WHIPS: ev(k, 'whip'); imp(k, 9)
TOP = (1060, 720)
def spin_speed(t):
    return 6 + 9 * sum(1 for k in WHIPS if k <= t)
def g_top(c, t):
    d = t - G[3]
    c.clear(col(IVORY))
    cam = Cam(1.0 + 0.03 * sum(1 for k in WHIPS if k <= t), 960, 580); c.save(); cam.apply(c, t)
    shape(c, ellipse_pts(960, 760, 620, 150), (214, 226, 230), INK, 4, seed=40)
    for m in range(5):
        x = 500 + m * 190
        ink(c, [(x, 730 + m * 9), (x + 80, 720 + m * 9)], (170, 190, 198), 2, seed=m, double=False)
    ang = sum(spin_speed(G[3] + s / 30) / 30 for s in range(int(d * 30)))
    x = TOP[0] + math.cos(d * 3) * 40; y = TOP[1] + math.sin(d * 3) * 10
    tilt = math.sin(d * 7) * 0.08
    sp = spin_speed(t)
    c.drawOval(skia.Rect(x - 70, y + 105, x + 70, y + 125), P(DARK, 50))
    for m in range(int(sp / 8)):
        rr = 110 + m * 25
        ink(c, ellipse_pts(x, y + 20, rr, rr * 0.3, a0=ang * 0.3 + m, a1=ang * 0.3 + m + 1.2), INK, 2.5, seed=m, double=False, a=160)
    c.save(); c.translate(x, y); c.rotate(math.degrees(tilt))
    cone = [(-75, 0), (75, 0), (40, 55), (8, 110), (-8, 110), (-40, 55)]
    shape(c, cone, WOOD, INK, 4, seed=41)
    ink(c, [(-60, 20), (60, 20)], CLAY, 5, seed=42, double=False)
    ink(c, [(-45, 45), (45, 45)], NAVY2, 5, seed=43, double=False)
    c.drawOval(skia.Rect(-75, -20, 75, 20), P(WOOD_L))
    for m in range(6):
        a0 = ang + m * math.pi / 3
        p = skia.Path(); p.moveTo(0, 0)
        p.arcTo(skia.Rect(-75, -20, 75, 20), math.degrees(a0), 60, False); p.close()
        c.drawPath(p, P([CLAY, PAPER, NAVY2][m % 3], 230))
    ink(c, ellipse_pts(0, 0, 75, 20), INK, 3.5, True, seed=44)
    c.restore()
    # 송구리 with 팽이채
    whipping = [k for k in WHIPS if 0 <= t - k < 0.25]
    draw_char(c, 640, 800, px=12, pose='throw' if whipping else 'idle')
    hx, hy = 700, 580
    sx, sy = hx + 90, hy - 170
    ink(c, [(hx, hy), (sx, sy)], WOOD_D, 7, seed=45)
    if whipping:
        u = seg(t - whipping[0], 0, 0.12)
        ex, ey = lerp(sx + 60, x - 40, u), lerp(sy - 40, y + 40, u)
        ink(c, [(sx, sy), ((sx + ex) / 2 + 60, (sy + ey) / 2 - 60 * (1 - u)), (ex, ey)], INK, 3, seed=46, double=False)
        if u >= 1:
            for m in range(7):
                a = m * 0.9
                ink(c, [(x - 40 + math.cos(a) * 30, y + 40 + math.sin(a) * 30), (x - 40 + math.cos(a) * 70, y + 40 + math.sin(a) * 70)], CLAY_D, 5, seed=m, double=False)
    else:
        ink(c, [(sx, sy), (sx + 30, sy + 90), (sx + 10, sy + 180)], INK, 3, seed=47, double=False)
    c.restore()
    text(c, '채로 쳐서 팽이가 멈추지 않게 돌리기', 960, 1010, 34, INK, a=255 * seg(d, 0.6, 0.9) * (1 - seg(d, 3.3, 3.5)), light=True)
    if d > 3.0:
        k = eback(seg(d, 3.0, 3.2)); c.save(); c.translate(1450, 380); c.rotate(-6); c.scale(k, k); text(c, '쌩쌩!', 0, 0, 130, CLAY_D, shadow=(DARK, 40)); c.restore()
    paper_overlay(c)

# ================= GAME 5: 연날리기 =================
ev(G[4] + 0.6, 'wind'); ev(G[4] + 2.2, 'whoosh'); ev(G[4] + 3.0, 'chime')
def kite_pos(d):
    u = eio(seg(d, 0.5, 2.2))
    x = lerp(620, 1340, u); y = lerp(720, 300, u)
    if d > 2.2:
        v = (d - 2.2) * 3.2
        x += math.sin(v) * 130; y += math.sin(2 * v) * 50
    return x, y
def g_kite(c, t):
    d = t - G[4]
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)], [col((214, 226, 232)), col(IVORY)])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
    cam = Cam(1.0, 960, lerp(560, 520, eio(seg(d, 0.5, 2.2)))); c.save(); cam.apply(c, t)
    for m in range(4):
        cloud(c, (m * 560 + 300 - d * 80) % 2400 - 200, 160 + (m % 2) * 200, 70 + m * 10, seed=m)
    for m in range(8):
        y = 150 + m * 90; x = (m * 330 - d * 900) % 2400 - 200
        ink(c, [(x, y), (x + 160, y - 6)], INK, 2, seed=m, a=110, double=False)
    ground(c, 890, seed=51)
    kx, ky = kite_pos(d)
    rx, ry = 520, 720
    ink(c, [(rx, ry), ((rx + kx) / 2, (ry + ky) / 2 + 120), (kx, ky + 60)], INK, 2, seed=52, double=False, amp=1)
    # 방패연
    rot = math.sin(d * 5) * 0.12
    c.save(); c.translate(kx, ky); c.rotate(math.degrees(rot))
    shape(c, rect_pts(-75, -100, 150, 200), PAPER, INK, 4, seed=53)
    c.drawCircle(0, -62, 30, P(CLAY))  # 꼭지
    ink(c, circle_pts(0, -62, 30), INK, 2.5, True, seed=54, double=False)
    c.drawRect(skia.Rect(-75, 60, 75, 100), P(NAVY2, 200))
    for ln in [[(0, -100), (0, 100)], [(-75, -100), (75, 100)], [(75, -100), (-75, 100)], [(-75, -100), (75, -100)], [(-75, 0), (75, 0)]]:
        ink(c, ln, WOOD_D, 2, seed=len(ln), double=False)
    c.drawCircle(0, 5, 26, P((214, 226, 232)))  # 방구멍
    ink(c, circle_pts(0, 5, 26), INK, 3, True, seed=55, double=False)
    c.restore()
    # 얼레 (reel) + 송구리
    draw_char(c, 430, 890, px=12, pose='up' if d > 2.3 else 'throw')
    c.save(); c.translate(rx, ry); c.rotate(d * 400 if d < 2.2 else d * 60)
    shape(c, rect_pts(-28, -28, 56, 56), WOOD_L, INK, 3, seed=56)
    ink(c, [(-28, -28), (28, 28)], WOOD_D, 3, seed=57, double=False); ink(c, [(-28, 28), (28, -28)], WOOD_D, 3, seed=58, double=False)
    c.restore()
    c.restore()
    text(c, '방패연 — 가운데 방구멍으로 바람이 빠져 날렵하게 난다', 960, 1010, 34, INK, a=255 * seg(d, 0.6, 0.9) * (1 - seg(d, 3.3, 3.5)), light=True)
    if d > 2.8:
        k = eback(seg(d, 2.8, 3.0)); c.save(); c.translate(760, 330); c.scale(k, k); text(c, '높이 높이!', 0, 0, 110, CLAY_D, shadow=(DARK, 40)); c.restore()
    paper_overlay(c)

# ================= GAME 6: 강강술래 =================
ev(G[5] + 0.6, 'chant'); ev(G[5] + 1.6, 'chant'); ev(G[5] + 2.6, 'chant')
RING_PALS = ['song', 'pink', 'green', 'gold', 'navy', 'pink', 'green', 'gold']
def g_ring(c, t):
    d = t - G[5]
    cam = Cam(1.0 + 0.05 * seg(d, 0.5, 3.4), 960, 540); c.save(); cam.apply(c, t)
    night_bg(c, t); stars(c, t, 200)
    draw_moon(c, 960, 190, 110, seed=60, glow_a=90)
    shape(c, ellipse_pts(960, 760, 700, 170), NAVY3, INK, 4, seed=61)
    base = 0.6 * d + 0.7 * d * d
    cx, cy, rx, ry = 960, 730, 430, 120
    pos = []
    for k in range(8):
        a = base + k * 2 * math.pi / 8
        x = cx + math.cos(a) * rx; y = cy + math.sin(a) * ry
        s = 0.72 + 0.28 * (math.sin(a) + 1) / 2
        pos.append((y, x, s, k))
    for k in range(8):  # hand-holding ring
        y0, x0, s0, _ = pos[k]; y1, x1, s1, _ = pos[(k + 1) % 8]
        ink(c, [(x0, y0 - 150 * s0), (x1, y1 - 150 * s1)], PAPER, 3, seed=k, a=170, double=False, amp=1.5)
    for y, x, s, k in sorted(pos):
        bob = abs(math.sin(d * 7 + k)) * 18
        draw_char(c, x, y - bob, px=10 * s, pose='up' if int(d * 4 + k) % 2 else 'idle', pal=RING_PALS[k], flip=(math.cos(base + k * 0.785) < 0))
    c.restore()
    paper_overlay(c, 120); vignette(c, 100)
    for m, w in enumerate(['강강', '술래~']):
        u = seg(d, 0.6 + m * 0.5, 0.9 + m * 0.5)
        if u > 0 and d < 3.4:
            k = eback(u); c.save(); c.translate(560 + m * 300, 380 + math.sin(d * 4 + m) * 10); c.scale(k, k)
            text(c, w, 0, 0, 100, MOON, a=255 * (1 - seg(d, 3.2, 3.4)))
            c.restore()
    text(c, '손을 잡고 둥글게 돌며 부르는 보름달 밤의 춤', 960, 1010, 34, PAPER, a=255 * seg(d, 0.6, 0.9) * (1 - seg(d, 3.3, 3.5)), light=True)

# ================= 널뛰기 (38-45.5) =================
GRAV = 3200.0
FLIGHTS = []  # (who, launch, h)
seq = [('A', 110), ('B', 170), ('A', 250), ('B', 340), ('A', 470), ('B', 400)]
tl = 0.35 - 2 * math.sqrt(2 * 110 / GRAV)
for who, h in seq:
    FLIGHTS.append((who, tl, h)); tl += 2 * math.sqrt(2 * h / GRAV)
FINAL = tl  # A launches to the moon
LANDS = [(f[0], f[1] + 2 * math.sqrt(2 * f[2] / GRAV)) for f in FLIGHTS]
for who, lt in LANDS: ev(T_NEOL + lt, 'land'); imp(T_NEOL + lt, 7)
for who, lt, h in FLIGHTS[1:]: ev(T_NEOL + lt, 'jump', h)
ev(T_NEOL + FINAL, 'launch'); imp(T_NEOL + FINAL, 22); ev(T_NEOL + FINAL - 0.6, 'riser')
PIV = (960, 792); HALF = 360; TILT = 0.16

def board_angle(d):
    a = -TILT  # right end down initially (B standing)
    for who, lt in LANDS:
        if d >= lt:
            u = eout(seg(d, lt, lt + 0.08)); tgt = TILT if who == 'A' else -TILT
            a = lerp(-tgt, tgt, u)
    if d >= FINAL: a = TILT
    return a

def end_pos(side, a):
    s = -1 if side == 'A' else 1
    return PIV[0] + s * (HALF - 45) * math.cos(a), PIV[1] + (-s) * (HALF - 45) * math.sin(a) - 12

def char_y(who, d, a):
    for w, lt, h in FLIGHTS:
        dur = 2 * math.sqrt(2 * h / GRAV)
        if w == who and lt <= d < lt + dur:
            v = math.sqrt(2 * GRAV * h); tt = d - lt
            return end_pos(who, -TILT if who == 'A' else TILT)[1] - (v * tt - 0.5 * GRAV * tt * tt), True
    if who == 'A' and d >= FINAL:
        tt = d - FINAL
        off = 900 * tt / 0.12 if tt < 0.12 else 900 + 1700 * eout(seg(tt, 0.12, 0.9))
        return end_pos('A', -TILT)[1] - off, True
    return end_pos(who, a)[1], False

def s_neol(c, t):
    d = t - T_NEOL
    if d >= 5.6: return s_sky(c, t)
    a = board_angle(d)
    ya, fa = char_y('A', d, a); yb, fb = char_y('B', d, a)
    base = PIV[1] - 60
    hmax = max(0, base - min(ya, yb))
    if d >= FINAL:
        cy = min(540, ya + 60); z = 0.8
    else:
        z = 1.0 - 0.2 * clamp(hmax / 520); cy = 560 - hmax * 0.35
    cam = Cam(z, 960, cy); c.save(); cam.apply(c, t)
    sh = skia.GradientShader.MakeLinear([skia.Point(0, -2200), skia.Point(0, 900)], [col(NAVY), col(NAVY), col((168, 118, 104))], [0, 0.55, 1])
    c.drawRect(skia.Rect(-800, -3000, W + 800, H + 600), skia.Paint(Shader=sh))
    stars(c, t, 160, dy=0)
    draw_moon(c, 1560, 120, 120, seed=70, glow_a=80)
    shape(c, [(-800, 900), (400, 820), (900, 870), (1500, 800), (2700, 880), (2700, 1600), (-800, 1600)], NAVY3, INK, 4, seed=71)
    # straw bundle + board
    shape(c, ellipse_pts(PIV[0], PIV[1] + 30, 80, 42), STRAW, INK, 4, seed=72)
    for m in range(5):
        ink(c, [(PIV[0] - 60 + m * 30, PIV[1] + 5), (PIV[0] - 70 + m * 32, PIV[1] + 60)], STRAW_D, 2, seed=m, double=False)
    ca, sa = math.cos(a), math.sin(a)
    brd = [(-HALF, -10), (HALF, -10), (HALF, 10), (-HALF, 10)]
    shape(c, xform(brd, PIV[0], PIV[1] - 5, -a), WOOD, INK, 4, seed=73)
    xa = end_pos('A', a)[0]; xb = end_pos('B', a)[0]
    for who, x, y, fl, pal in (('A', xa, ya, fa, 'song'), ('B', xb, yb, fb, 'pink')):
        land = max([lt for w, lt in LANDS if w == who and lt <= d], default=-9)
        sq = 0.22 * math.exp(-(d - land) * 14) if (not fl and d - land < 0.4) else 0
        draw_char(c, x, y, px=11, pose='jump' if fl else 'idle', pal=pal, sy=1 - sq, sx=1 + sq, flip=(who == 'B'), shadow=not fl)
    if d >= FINAL:
        for m in range(10):
            yy = ya + 100 + m * 70 + (d * 900) % 70
            draw_songpyeon(c, xa + math.sin(m * 1.7 + d * 8) * 60, yy, 44, SP_COLS[m % 3], rot=d * 6 + m, seed=m)
    c.restore()
    if d >= FINAL:
        speedlines(c, t, 30, PAPER, 110, seed=5)
        k = eback(seg(d, FINAL + 0.1, FINAL + 0.3))
        c.save(); c.translate(960, 860); c.scale(k, k); text(c, '달까지 날아올라!', 0, 0, 110, PAPER, shadow=(DARK, 80)); c.restore()
    else:
        k = sum(1 for _, lt in LANDS if lt <= d)
        text(c, '널뛰기', 170, 1000, 50, PAPER, light=True, a=220)
        text(c, '점프 ' + '▲' * k, 1760, 1000, 40, MOON, light=True, align='r')
    paper_overlay(c, 130); vignette(c, 100)
    flash(c, t, T_NEOL + FINAL, 0.25)

# ================= sky flight (43.6-45.5) =================
def s_sky(c, t):
    d = t - T_NEOL - 5.6
    night_bg(c, t, NAVY, (30, 38, 62))
    for i, (x, y, s, ph) in enumerate(STARS):
        yy = (y + d * 1400 * (0.5 + s / 11)) % (H + 200) - 100
        c.drawLine(x, yy, x, yy - 40 * s / 6, P(MOON, 160, 2))
    u = eio(seg(d, 0, 1.9))
    my = lerp(-160, 330, u); mr = lerp(120, 300, u)
    draw_moon(c, 960, my, mr, seed=80, glow_a=150)
    for m in range(4):
        yy = (m * 400 + d * 1500) % 1800 - 300
        cloud(c, 300 + m * 440, yy, 100, PAPER, INK, 200, seed=m)
    cx, cy = 960, 820 - 50 * u + math.sin(d * 8) * 8
    for m in range(18):
        ang = m * 0.7 + d * 6; rr = 120 + m * 12
        draw_songpyeon(c, cx + math.cos(ang) * rr, cy + 40 + abs(math.sin(ang)) * 40 + m * 14, 42, SP_COLS[m % 3], rot=ang, seed=m)
    draw_char(c, cx, cy + 110, px=11, pose='up', shadow=False)
    speedlines(c, t, 24, PAPER, 90, cy=H / 2 + 200, seed=9)
    paper_overlay(c, 120); vignette(c, 100)

# ================= MOON (45.5-50) =================
MC, MR = (960, 470), 300
SLOTS = []
for row in range(-12, 13):
    for colm in range(-12, 1):
        x = MC[0] + colm * 50 + (25 if row % 2 else 0); y = MC[1] + row * 42
        if x < MC[0] - 20 and math.hypot(x - MC[0], y - MC[1]) < MR - 26:
            SLOTS.append((x, y))
SLOTS.sort(key=lambda p: (-p[0] + hn(int(p[1])) * 30))
NS = len(SLOTS)
SLOT_T = [T_MOON + 0.25 + 1.75 * i / NS for i in range(NS)]
for i in range(0, NS, 3): ev(SLOT_T[i] + 0.3, 'fill', i)
FULL_T = T_MOON + 2.25
ev(FULL_T, 'boom'); imp(FULL_T, 20)
FW = [(FULL_T + 0.15, 420, 250, CLAY), (FULL_T + 0.45, 1500, 230, SPP), (FULL_T + 0.8, 300, 520, SPG), (FULL_T + 1.1, 1640, 560, MOON), (FULL_T + 1.45, 620, 160, SPP), (FULL_T + 1.7, 1320, 150, CLAY)]
for ft, *_ in FW: ev(ft, 'firework')
ev(FULL_T + 0.6, 'ending')

def firework(c, x, y, d, color):
    if d < 0 or d > 1.3: return
    u = eout(seg(d, 0, 0.7)); a = 255 * (1 - seg(d, 0.6, 1.3))
    for m in range(16):
        ang = m * 2 * math.pi / 16
        r1 = 30 + 170 * u; r0 = max(0, r1 - 90 * (1 - seg(d, 0.3, 0.9)) - 10)
        dr = 40 * d * d
        ink(c, [(x + math.cos(ang) * r0, y + math.sin(ang) * r0 + dr), (x + math.cos(ang) * r1, y + math.sin(ang) * r1 + dr)], color, 5, seed=m, a=a, double=False, amp=1)
        if d > 0.4: sparkle(c, x + math.cos(ang) * (r1 + 14), y + math.sin(ang) * (r1 + 14) + dr * 1.3, 9, color, a)

def s_moon(c, t):
    d = t - T_MOON
    z = lerp(1.08, 0.78, eio(seg(d, 1.9, 3.2)))
    cam = Cam(z, 960, lerp(500, 470, seg(d, 1.9, 3.2))); c.save(); cam.apply(c, t)
    night_bg(c, t); stars(c, t, 220)
    full = seg(t, FULL_T, FULL_T + 0.25)
    draw_moon(c, MC[0], MC[1], MR, full=full, glow_a=120 + 120 * full, seed=90)
    for i, (sx, sy) in enumerate(SLOTS):
        st = SLOT_T[i]
        if t < st: continue
        u = seg(t, st, st + 0.35)
        bx, by = 1400, 560
        x = lerp(bx, sx, eout(u)); y = lerp(by, sy, eout(u)) - math.sin(u * math.pi) * 120
        sc = 48 * (1 + 0.3 * math.sin(u * math.pi))
        draw_songpyeon(c, x, y, sc, SP_COLS[i % 3], rot=(1 - u) * 5 + hn(i) * 0.2, seed=i, lw=2)
    if full > 0:
        glow(c, MC[0], MC[1], MR * 1.2, PAPER, 90 * (1 - seg(t, FULL_T, FULL_T + 1.0)))
    for ft, fx, fy, fc in FW: firework(c, fx, fy, t - ft, fc)
    # 송구리: hover right, then hop onto the moon's top
    if t < FULL_T:
        draw_char(c, 1420, 700 + math.sin(d * 6) * 10, px=11, pose='up', shadow=False)
    else:
        u = seg(t, FULL_T, FULL_T + 0.45)
        x = lerp(1420, 960, eout(u)); y = lerp(700, MC[1] - MR + 8, u) - math.sin(u * math.pi) * 260
        land = FULL_T + 0.45
        sq = 0.2 * math.exp(-(t - land) * 12) if t > land else 0
        draw_char(c, x, y, px=11, pose='jump' if u < 1 else ('point' if t > land + 0.4 else 'up'), sy=1 - sq, sx=1 + sq, shadow=False)
    c.restore()
    paper_overlay(c, 120); vignette(c, 100)
    flash(c, t, FULL_T, 0.35)
    if t > FULL_T + 0.6:
        for i, ch in enumerate('해피 추석'):
            pass
        k = eback(seg(t, FULL_T + 0.6, FULL_T + 0.9))
        c.save(); c.translate(960, 905); c.scale(k, k)
        text(c, '해피 추석', 0, 0, 130, PAPER, shadow=(DARK, 90))
        c.restore()
        text(c, 'by Claude Opus 5.5', 960, 985, 44, MOON, a=255 * seg(t, FULL_T + 1.0, FULL_T + 1.4), light=True, spacing=5)
    if t > T_END - 0.35: c.drawRect(skia.Rect(0, 0, W, H), P(DARK, 255 * seg(t, T_END - 0.35, T_END)))

# ================= dispatcher =================
GAME_FUNCS = [g_yut, g_jegi, g_tuho, g_top, g_kite, g_ring]
def frame(c, t):
    lib.BOIL = int(t * 10)
    c.save()
    if t < T_TITLE: s_open(c, t)
    elif t < T_MISSION: s_title(c, t)
    elif t < T_G0: s_mission(c, t)
    elif t < T_NEOL:
        i = min(5, int((t - T_G0) / GL))
        GAME_FUNCS[i](c, t)
        reward(c, t, i)
        card(c, t, i)
    elif t < T_MOON: s_neol(c, t)
    else: s_moon(c, t)
    c.restore()
    hud(c, t)
    # beat-synced cut flashes
    for g in G: flash(c, t, g + 0.5, 0.12, amax=160)
