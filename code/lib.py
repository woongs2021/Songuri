import math, numpy as np, skia
from scipy.ndimage import gaussian_filter

W, H, FPS = 1920, 1080, 30
BOIL = 0  # set per frame (hand-drawn line boil, 10fps)

# ---------- palette ----------
IVORY = (240, 238, 230); PAPER = (250, 249, 245)
CLAY = (217, 119, 87); CLAY_D = (184, 92, 62); CLAY_L = (242, 223, 211)
DARK = (20, 20, 19); INK = (42, 34, 30)
NAVY = (26, 32, 50); NAVY2 = (40, 50, 76); NAVY3 = (58, 70, 104)
MOON = (246, 229, 180); MOON_D = (226, 204, 150)
SPW = (250, 246, 236); SPG = (150, 190, 118); SPP = (242, 166, 182)
SP_COLS = [SPW, SPG, SPP]
WOOD = (196, 146, 92); WOOD_L = (238, 214, 168); WOOD_D = (140, 96, 58)
STRAW = (222, 196, 132); STRAW_D = (176, 148, 88)
CELADON = (158, 186, 170); CELADON_D = (110, 140, 124)

def col(c, a=255):
    return skia.ColorSetARGB(int(max(0, min(255, a))), int(c[0]), int(c[1]), int(c[2]))

def lerp(a, b, t): return a + (b - a) * t
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def eout(t): return 1 - (1 - t) ** 3
def ein(t): return t ** 3
def eio(t): return 3 * t * t - 2 * t * t * t
def eback(t, s=1.9):
    t = t - 1
    return t * t * ((s + 1) * t + s) + 1
def lerpc(a, b, t): return tuple(lerp(a[i], b[i], t) for i in range(3))

def hn(i):
    x = math.sin(i * 127.1 + 311.7) * 43758.5453
    return (x - math.floor(x)) * 2 - 1

# ---------- hand-drawn geometry ----------
def subdiv(pts, closed, step=22):
    out = []
    n = len(pts)
    rng = n if closed else n - 1
    for i in range(rng):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % n]
        d = math.hypot(x1 - x0, y1 - y0)
        k = max(1, int(d / step))
        for j in range(k):
            out.append((lerp(x0, x1, j / k), lerp(y0, y1, j / k)))
    if not closed: out.append(pts[-1])
    return out

def wob_path(pts, closed=False, amp=2.0, seed=0, step=22, boil=True):
    ps = subdiv(pts, closed, step)
    b = BOIL if boil else 0
    q = []
    for k, (x, y) in enumerate(ps):
        s = seed * 977 + k * 13 + b * 7919
        q.append((x + hn(s) * amp, y + hn(s + 5) * amp))
    p = skia.Path()
    if len(q) < 2: return p
    if closed:
        m0 = ((q[-1][0] + q[0][0]) / 2, (q[-1][1] + q[0][1]) / 2)
        p.moveTo(*m0)
        for i in range(len(q)):
            a = q[i]; nb = q[(i + 1) % len(q)]
            p.quadTo(a[0], a[1], (a[0] + nb[0]) / 2, (a[1] + nb[1]) / 2)
        p.close()
    else:
        p.moveTo(*q[0])
        for i in range(1, len(q) - 1):
            a = q[i]; nb = q[i + 1]
            p.quadTo(a[0], a[1], (a[0] + nb[0]) / 2, (a[1] + nb[1]) / 2)
        p.lineTo(*q[-1])
    return p

def P(color, a=255, stroke=None, cap=True):
    p = skia.Paint(Color=col(color, a), AntiAlias=True)
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        if cap:
            p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    return p

def ink(c, pts, color=INK, w=4, closed=False, seed=0, amp=2.0, a=255, double=True, step=22):
    c.drawPath(wob_path(pts, closed, amp, seed, step), P(color, a, w))
    if double:
        c.drawPath(wob_path(pts, closed, amp * 1.2, seed + 71, step), P(color, a * 0.35, max(1, w * 0.5)))

def shape(c, pts, fill, stroke=INK, w=4, seed=0, amp=2.0, a=255, sa=255, double=True):
    if fill is not None:
        c.drawPath(wob_path(pts, True, amp * 0.6, seed + 3), P(fill, a))
    if stroke is not None:
        ink(c, pts, stroke, w, True, seed, amp, sa, double)

def circle_pts(cx, cy, r, n=None, a0=0, a1=2 * math.pi):
    if n is None: n = max(14, int(abs(a1 - a0) * r / 16))
    return [(cx + r * math.cos(lerp(a0, a1, i / n)), cy + r * math.sin(lerp(a0, a1, i / n))) for i in range(n + (0 if abs(a1 - a0 - 2 * math.pi) < 1e-6 else 1))]

def ellipse_pts(cx, cy, rx, ry, rot=0, n=None, a0=0, a1=2 * math.pi):
    if n is None: n = max(16, int(abs(a1 - a0) * max(rx, ry) / 16))
    full = abs(a1 - a0 - 2 * math.pi) < 1e-6
    out = []
    cr, sr = math.cos(rot), math.sin(rot)
    for i in range(n + (0 if full else 1)):
        a = lerp(a0, a1, i / n)
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return out

def rect_pts(x, y, w, h): return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]

def xform(pts, cx, cy, rot=0, s=1.0, sx=None, sy=None):
    sx = s if sx is None else sx; sy = s if sy is None else sy
    cr, sr = math.cos(rot), math.sin(rot)
    return [(cx + (x * sx) * cr - (y * sy) * sr, cy + (x * sx) * sr + (y * sy) * cr) for x, y in pts]

def partial(pts, frac):
    n = max(2, int(len(pts) * clamp(frac)))
    return pts[:n]

# ---------- fonts / text ----------
FONT_XL = skia.Typeface.MakeFromFile('fonts/NotoSerifKR-ExtraLight.otf')
FONT_L = skia.Typeface.MakeFromFile('fonts/NotoSerifKR-Light.otf')
_fc = {}
def font(size, light=False):
    k = (int(size), light)
    if k not in _fc:
        f = skia.Font(FONT_L if light else FONT_XL, int(size))
        f.setEdging(skia.Font.Edging.kAntiAlias); f.setSubpixel(True)
        _fc[k] = f
    return _fc[k]

def text(c, s, x, y, size, color=INK, a=255, align='c', light=False, spacing=0, jitter=True, shadow=None):
    f = font(size, light)
    ws = [f.measureText(ch) + spacing for ch in s]
    tw = sum(ws) - spacing
    x0 = x - tw / 2 if align == 'c' else (x - tw if align == 'r' else x)
    jx = hn(BOIL * 3 + len(s)) * 0.8 if jitter else 0
    jy = hn(BOIL * 5 + len(s)) * 0.8 if jitter else 0
    if spacing == 0:
        if shadow:
            c.drawString(s, x0 + jx + 3, y + jy + 4, f, P(shadow[0], shadow[1]))
        c.drawString(s, x0 + jx, y + jy, f, P(color, a))
    else:
        cx = x0
        for ch, w in zip(s, ws):
            if shadow: c.drawString(ch, cx + jx + 3, y + jy + 4, f, P(shadow[0], shadow[1]))
            c.drawString(ch, cx + jx, y + jy, f, P(color, a)); cx += w
    return tw

def text_w(s, size, light=False, spacing=0):
    f = font(size, light)
    return sum(f.measureText(ch) + spacing for ch in s) - spacing

# ---------- paper texture ----------
def make_paper():
    rng = np.random.default_rng(7)
    h, w = H + 40, W + 40
    low = gaussian_filter(rng.standard_normal((h // 4, w // 4)), 12)
    low = np.kron(low, np.ones((4, 4)))[:h, :w]
    low = low / (np.abs(low).max() + 1e-6)
    mid = gaussian_filter(rng.standard_normal((h, w)), 1.6)
    mid /= np.abs(mid).max()
    fine = rng.standard_normal((h, w))
    g = 128 + low * 14 + mid * 18 + fine * 7
    # fibers
    for _ in range(900):
        x, y = rng.integers(0, w), rng.integers(0, h)
        ang = rng.uniform(0, math.pi); L = rng.integers(8, 40)
        for k in range(L):
            xx = int(x + k * math.cos(ang)); yy = int(y + k * math.sin(ang))
            if 0 <= xx < w and 0 <= yy < h: g[yy, xx] += rng.choice([-10, 10])
    g = np.clip(g, 0, 255).astype(np.uint8)
    arr = np.dstack([g, g, g, np.full_like(g, 255)])
    return skia.Image.fromarray(arr)

PAPER_IMG = None
def paper_overlay(c, strength=150):
    global PAPER_IMG
    if PAPER_IMG is None: PAPER_IMG = make_paper()
    p = skia.Paint(); p.setBlendMode(skia.BlendMode.kOverlay); p.setAlphaf(strength / 255)
    ox = -((BOIL % 3) * 7) - 5; oy = -((BOIL % 2) * 6) - 5
    c.drawImage(PAPER_IMG, ox, oy, skia.SamplingOptions(), p)

def vignette(c, a=90):
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * 0.72,
                                        [col(DARK, 0), col(DARK, 0), col(DARK, a)], [0, 0.55, 1.0])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))

def glow(c, x, y, r, color, a=180):
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y), r, [col(color, a), col(color, 0)])
    c.drawCircle(x, y, r, skia.Paint(Shader=sh, AntiAlias=True))

# ---------- pixel sprite: 송구리 (original raccoon dog) ----------
BASE = [
 "....KK........KK........",
 "...KFFK......KFFK.......",
 "...KFMFKKKKKKFMFK.......",
 "...KFFFFFFFFFFFFK.......",
 "..KFFFFFFFFFFFFFFK......",
 "..KFMMMMFFFFMMMMFK......",
 "..KMMWKMLLLLMWKMMK......",
 "..KMMKKMLLLLMKKMMK......",
 "..KFMMMLLLLLLMMMFK......",
 "..KFFPLLLNNLLLPFFK......",
 "...KFFLLLLLLLLFFK.......",
 "....KKFFFFFFFFKK........",
 "...KOOOoLLLLoOOOK.......",
 "...KOOOoLLLLoOOOK.......",
 "...KOOOoLLLLoOOOK.......",
 "...KOOOoLLLLoOOOK.......",
 "...KOOOOOOOOOOOOK.......",
 "...KFFFFFFFFFFFFK.......",
 "........................",
 "........................",
 "........................",
]
TAIL = [  # placed at col 18,row 9
 "..KK.",
 ".KTTK",
 ".KDDK",
 ".KTTK",
 "KDDK.",
 "KTTK.",
 "KDDK.",
 "KTK..",
 "KK...",
]
PAL = {
 'K': (42, 33, 28), 'F': (156, 136, 116), 'M': (58, 46, 40), 'L': (240, 228, 208),
 'W': (255, 255, 255), 'N': (26, 20, 17), 'P': (232, 150, 138), 'O': CLAY, 'o': CLAY_D,
 'T': (186, 162, 136), 'D': (70, 56, 46),
}
PALS = {
 'song': {},
 'green': {'O': (126, 163, 104), 'o': (92, 127, 76)},
 'pink': {'O': (231, 150, 166), 'o': (192, 112, 130)},
 'navy': {'O': (84, 100, 150), 'o': (60, 72, 112)},
 'gold': {'O': (224, 182, 92), 'o': (180, 140, 62)},
}

def _put(g, x, y, ch):
    if 0 <= y < len(g) and 0 <= x < len(g[0]): g[y][x] = ch

def _arm(g, pts):
    for (x, y) in pts:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if g[y + dy][x + dx] == '.': _put(g, x + dx, y + dy, 'K')
    for (x, y) in pts: _put(g, x, y, 'F')

def make_grid(pose):
    g = [list(r) for r in BASE]
    for j, r in enumerate(TAIL):
        for i, ch in enumerate(r):
            if ch != '.': _put(g, 17 + i, 11 + j, ch)
    
    # legs
    if pose == 'jump':
        legs = [(4, 18), (5, 18), (13, 18), (14, 18), (3, 19), (4, 19), (14, 19), (15, 19)]
    elif pose == 'kick':
        legs = [(11, 18), (12, 18), (11, 19), (12, 19), (5, 18), (4, 18), (3, 18), (2, 18), (1, 17)]
    else:
        legs = [(5, 18), (6, 18), (5, 19), (6, 19), (11, 18), (12, 18), (11, 19), (12, 19)]
    _arm(g, legs)
    # arms
    if pose in ('idle', 'kick'):
        _arm(g, [(2, 12), (2, 13), (2, 14)]); _arm(g, [(17, 12), (17, 13), (17, 14)])
    elif pose == 'up' or pose == 'jump':
        _arm(g, [(2, 11), (1, 10), (1, 9), (1, 8), (1, 7)])
        _arm(g, [(17, 11), (18, 10), (18, 9), (18, 8), (18, 7)])
    elif pose == 'point':
        _arm(g, [(2, 12), (2, 13), (2, 14)])
        _arm(g, [(17, 11), (18, 10), (19, 9), (20, 8), (21, 7)])
    elif pose == 'throw':
        _arm(g, [(2, 12), (2, 13), (2, 14)])
        _arm(g, [(17, 11), (18, 10), (18, 9), (18, 8), (19, 7)])
    # re-outline tail where overwritten is fine
    return g

_spr = {}
def sprite(pose='idle', pal='song', blink=False):
    k = (pose, pal, blink)
    if k in _spr: return _spr[k]
    g = make_grid(pose)
    if blink:
        for y in (6, 7):
            for x in range(len(g[0])):
                if g[y][x] in 'W' or (g[y][x] == 'K' and 3 < x < 17 and y == 6): g[y][x] = 'M'
        for x in (5, 6, 13, 14): g[7][x] = 'K'
    pal_d = dict(PAL); pal_d.update(PALS[pal])
    h, w = len(g), len(g[0])
    arr = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            ch = g[y][x]
            if ch != '.':
                arr[y, x, :3] = pal_d[ch]; arr[y, x, 3] = 255
    img = skia.Image.fromarray(arr)
    _spr[k] = (img, w, h)
    return _spr[k]

NEAREST = skia.SamplingOptions(skia.FilterMode.kNearest)
def draw_char(c, x, y, px=11, pose='idle', pal='song', sx=1.0, sy=1.0, rot=0.0, flip=False, a=255, shadow=True, blink=False):
    img, w, h = sprite(pose, pal, blink)
    # anchor: feet (bottom of row 20) at body center col 9.5
    if shadow:
        c.drawOval(skia.Rect(x - 7 * px, y - px * 0.9, x + 7 * px, y + px * 0.9), P(DARK, 45 * a / 255))
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(sx * (-1 if flip else 1), sy)
    p = skia.Paint(); p.setAlphaf(a / 255)
    c.drawImageRect(img, skia.Rect(-9.5 * px, -20 * px, (w - 9.5) * px, (h - 20) * px), NEAREST, p)
    c.restore()

# ---------- songpyeon ----------
def songpyeon_pts(w=60):
    h = w * 0.64
    top = [(w / 2 * math.cos(a), -h * math.sin(a) + h * 0.2) for a in np.linspace(0, math.pi, 16)]
    bot = [(-w / 2 * math.cos(a) * 1.0, h * 0.2 + h * 0.16 * math.sin(a)) for a in np.linspace(0, math.pi, 8)][1:-1]
    return top + bot

_SP = songpyeon_pts(1.0)
def draw_songpyeon(c, x, y, size=60, color=SPW, rot=0.0, a=255, seed=0, outline=INK, lw=None):
    pts = xform([(px * size, py * size) for px, py in _SP], x, y, rot)
    lw = lw or max(1.6, size * 0.055)
    c.drawPath(wob_path(pts, True, size * 0.02, seed, step=max(6, size * 0.25)), P(color, a))
    # shading on flat side
    sh = xform([(px * size * 0.8, py * size * 0.8 + size * 0.05) for px, py in _SP[16:]] + [(size * 0.35, size * 0.12)], x, y, rot)
    ridge = xform([(size * 0.36 * math.cos(t), -size * 0.36 * math.sin(t) + size * 0.14) for t in np.linspace(0.35, math.pi - 0.35, 7)], x, y, rot)
    c.drawPath(wob_path(pts, True, size * 0.02, seed, step=max(6, size * 0.25)), P(outline, a, lw))
    # pinched ridge ticks
    for i, (rx, ry) in enumerate(ridge):
        c.drawCircle(rx, ry, max(1.0, size * 0.028), P(outline, a * 0.5))
    hl = xform([(-size * 0.2, -size * 0.14), (-size * 0.05, -size * 0.2)], x, y, rot)
    c.drawPath(wob_path(hl, False, 0.5, seed + 9, step=40), P((255, 255, 255), a * 0.9, max(1.5, size * 0.05)))

# ---------- moon ----------
def half_path(cx, cy, r, left=False):
    p = skia.Path()
    if left:
        p.addArc(skia.Rect(cx - r, cy - r, cx + r, cy + r), 90, 180)
    else:
        p.addArc(skia.Rect(cx - r, cy - r, cx + r, cy + r), -90, 180)
    p.close()
    return p

def draw_moon(c, cx, cy, r, full=0.0, glow_a=120, empty_outline=True, seed=0):
    glow(c, cx, cy, r * 1.9, MOON, glow_a * (0.55 + 0.45 * full))
    # lit right half
    c.save(); c.clipPath(half_path(cx, cy, r + 3), skia.ClipOp.kIntersect, True)
    c.drawCircle(cx, cy, r, P(MOON))
    for i, (dx, dy, rr) in enumerate([(0.35, -0.3, 0.14), (0.55, 0.25, 0.1), (0.2, 0.45, 0.08), (0.62, -0.05, 0.06)]):
        shape(c, circle_pts(cx + dx * r, cy + dy * r, rr * r), MOON_D, MOON_D, 2, seed + i, 1.2, a=140, sa=160, double=False)
    c.restore()
    if full > 0:
        c.save(); c.clipPath(half_path(cx, cy, r + 3, True), skia.ClipOp.kIntersect, True)
        c.drawCircle(cx, cy, r, P(MOON, 255 * full))
        c.restore()
    ink(c, circle_pts(cx, cy, r, a0=-math.pi / 2, a1=math.pi / 2), INK, 4, seed=seed + 50, amp=1.6)
    if empty_outline and full < 1:
        p = P(MOON, 200 * (1 - full), 4)
        p.setPathEffect(skia.DashPathEffect.Make([16, 14], (BOIL * 3) % 30))
        c.drawPath(wob_path(circle_pts(cx, cy, r, a0=math.pi / 2, a1=3 * math.pi / 2), False, 1.2, seed + 60), p)
    if full >= 1:
        ink(c, circle_pts(cx, cy, r, a0=math.pi / 2, a1=3 * math.pi / 2), INK, 4, seed=seed + 51, amp=1.6)

# ---------- decor ----------
def star(c, x, y, s, color=MOON, a=255):
    ink(c, [(x - s, y), (x + s, y)], color, max(1.5, s * 0.25), seed=int(x), amp=0.4, a=a, double=False)
    ink(c, [(x, y - s), (x, y + s)], color, max(1.5, s * 0.25), seed=int(y), amp=0.4, a=a, double=False)

def sparkle(c, x, y, s, color=PAPER, a=255):
    p = skia.Path(); p.moveTo(x, y - s); p.quadTo(x, y, x + s, y); p.quadTo(x, y, x, y + s)
    p.quadTo(x, y, x - s, y); p.quadTo(x, y, x, y - s); p.close()
    c.drawPath(p, P(color, a))

def cloud(c, x, y, s, fill=PAPER, stroke=INK, a=255, seed=0):
    pts = []
    bumps = [(-1.0, 0.1, 0.45), (-0.5, -0.25, 0.55), (0.1, -0.4, 0.6), (0.65, -0.15, 0.5), (1.0, 0.12, 0.38)]
    for bx, by, br in bumps:
        pass
    # union via path ops
    path = skia.Path()
    for i, (bx, by, br) in enumerate(bumps):
        path.addCircle(x + bx * s, y + by * s, br * s)
    path.addRect(skia.Rect(x - 1.0 * s, y - 0.1 * s, x + 1.0 * s, y + 0.45 * s))
    pp = skia.Simplify(path)
    c.drawPath(pp, P(fill, a))
    c.drawPath(pp, P(stroke, a * 0.8, 3))

def hanok_roof(c, x, y, w, color, seed=0):
    h = w * 0.28
    pts = [(x - w * 0.55, y - h * 0.1), (x - w * 0.42, y - h * 0.35), (x - w * 0.25, y - h * 0.9),
           (x + w * 0.25, y - h * 0.9), (x + w * 0.42, y - h * 0.35), (x + w * 0.55, y - h * 0.1),
           (x + w * 0.4, y), (x - w * 0.4, y)]
    shape(c, pts, color, None, 0, seed)
    c.drawRect(skia.Rect(x - w * 0.36, y, x + w * 0.36, y + h * 0.9), P(color))
