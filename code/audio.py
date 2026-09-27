import numpy as np, math, wave
from scipy.signal import lfilter, butter, sosfilt
import scenes

SR = 44100
DUR = 50.0
N = int(SR * DUR)
music = np.zeros((N, 2)); sfx = np.zeros((N, 2))
rng = np.random.default_rng(11)

def add(buf, t, sig, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i < 0: return
    sig = sig[: N - i]
    l = gain * math.cos((pan + 1) * math.pi / 4); r = gain * math.sin((pan + 1) * math.pi / 4)
    buf[i:i + len(sig), 0] += sig * l * 1.414; buf[i:i + len(sig), 1] += sig * r * 1.414

def tt(d): return np.arange(int(d * SR)) / SR
def envd(d, dec, att=0.003):
    x = tt(d); return np.minimum(1, x / att) * np.exp(-x / dec)
def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], btype='band', fs=SR, output='sos'), x)
def lp(x, f): return sosfilt(butter(2, f, btype='low', fs=SR, output='sos'), x)
def hp(x, f): return sosfilt(butter(2, f, btype='high', fs=SR, output='sos'), x)
def noise(d): return rng.standard_normal(int(d * SR))
def sine(f, d, ph=0):
    x = tt(d)
    if callable(f): return np.sin(2 * np.pi * np.cumsum(f(x)) / SR)
    return np.sin(2 * np.pi * f * x + ph)

def pluck(f, d=1.2, bright=0.6, decay=0.996):
    L = max(2, int(SR / f))
    exc = rng.uniform(-1, 1, L)
    exc = lp(np.concatenate([exc, np.zeros(10)]), 1500 + 6000 * bright)[:L]
    x = np.zeros(int(d * SR)); x[:L] = exc
    a = np.zeros(L + 2); a[0] = 1; a[L] = -decay / 2; a[L + 1] = -decay / 2
    y = lfilter([1], a, x)
    y *= np.minimum(1, tt(d) / 0.002)
    # slight 농현-like bend at the tail
    return y / (np.abs(y).max() + 1e-9)

def bell(f, d=1.0, dec=0.5):
    x = tt(d)
    return (np.sin(2 * np.pi * f * x) + 0.4 * np.sin(2 * np.pi * f * 2.76 * x) * np.exp(-x / (dec * 0.4)) + 0.2 * np.sin(2 * np.pi * f * 5.4 * x) * np.exp(-x / (dec * 0.2))) * envd(d, dec, 0.002)

def deong():  # 장구 덩: low body + slap
    d = 0.5
    low = sine(lambda x: 60 + 70 * np.exp(-x / 0.04), d) * envd(d, 0.18)
    slap = bp(noise(d), 300, 1400) * envd(d, 0.03)
    return 0.9 * low + 0.35 * slap
def deok():  # 채편 덕: bright crack
    d = 0.2
    return 0.5 * bp(noise(d), 1800, 6000) * envd(d, 0.025) + 0.3 * sine(720, d) * envd(d, 0.02)
def gi():
    return 0.5 * deok()

def gong(f=98, d=4.0):
    x = tt(d)
    parts = [(1, 1.0), (1.52, 0.5), (2.03, 0.35), (2.74, 0.25), (3.3, 0.15)]
    s = sum(a * np.sin(2 * np.pi * f * p * x * (1 + 0.004 * np.exp(-x))) for p, a in parts)
    return s * np.minimum(1, x / 0.04) * np.exp(-x / 1.4) * (1 + 0.15 * np.sin(2 * np.pi * 3.2 * x))

def whoosh(d=0.35, lo=400, hi=4000, up=True):
    n = noise(d); x = tt(d)
    out = np.zeros_like(n); seg_n = 8
    for k in range(seg_n):
        a, b = int(k * len(n) / seg_n), int((k + 1) * len(n) / seg_n)
        u = k / seg_n if up else 1 - k / seg_n
        fc = lo * (hi / lo) ** u
        out[a:b] = bp(n, fc * 0.7, min(fc * 1.4, SR / 2 - 100))[a:b]
    return out * np.sin(np.pi * x / d) ** 2

def pad(freqs, d, att=1.0, rel=1.0):
    x = tt(d)
    s = sum(np.sin(2 * np.pi * f * x) + 0.5 * np.sin(2 * np.pi * f * 1.003 * x) + 0.25 * np.sin(2 * np.pi * f * 2 * x) for f in freqs)
    e = np.minimum(1, x / att) * np.minimum(1, (d - x) / rel)
    return lp(s * e, 2500) / len(freqs)

# ---------- scale (A minor pentatonic ~ 계면조 feel) ----------
A3 = 220.0
DEG = [0, 3, 5, 7, 10]
def note(deg, octv=0):
    o, k = divmod(deg, 5)
    return A3 * 2 ** ((DEG[k] + 12 * (o + octv)) / 12)

BEAT = 0.5
ROOTS = [0, 4, 2, 3]  # A G D E (pentatonic degrees)
MEL = [  # (eighth index, degree, length in eighths) over 2 bars
    (0, 5, 2), (2, 7, 1), (3, 8, 1), (4, 7, 2), (6, 5, 1), (7, 4, 1),
    (8, 5, 3), (11, 3, 1), (12, 4, 2), (14, 2, 2)]
MEL2 = [
    (0, 7, 1), (1, 8, 1), (2, 10, 2), (4, 9, 1), (5, 8, 1), (6, 7, 2),
    (8, 8, 2), (10, 7, 1), (11, 5, 1), (12, 7, 4)]

def groove(t0, t1, drums=1.0, mel=1.0, bass=1.0, density=1.0):
    bar = 0
    t = t0
    while t < t1 - 0.01:
        b = int(round(t / 2.0))
        root = ROOTS[b % 4]
        # drums: 덩 . 덕 기 덕 덩 덕 .
        pat = ['D', None, 'K', 'g', 'K', 'D', 'K', None]
        for e, p in enumerate(pat):
            te = t + e * 0.25
            if te >= t1: break
            if drums > 0:
                if p == 'D': add(music, te, deong(), 0.55 * drums, -0.1)
                elif p == 'K' and density > 0.5: add(music, te, deok(), 0.45 * drums, 0.25)
                elif p == 'g' and density > 0.8: add(music, te, gi(), 0.35 * drums, 0.3)
        if bass > 0:
            for e in (0, 3, 4, 6):
                te = t + e * 0.25
                if te < t1:
                    f = note(root, -1)
                    add(music, te, pluck(f, 0.6, 0.2, 0.99) * 0.9 + 0.4 * sine(f, 0.6) * envd(0.6, 0.25), 0.4 * bass, 0)
        if mel > 0:
            m = MEL if (b // 2) % 2 == 0 else MEL2
            half = b % 2
            for (e, dg, ln) in m:
                if (e >= 8) != bool(half): continue
                te = t + (e - 8 * half) * 0.25
                if te < t1:
                    add(music, te, pluck(note(dg + root - 0 if False else dg), 0.25 * ln + 0.6, 0.7), 0.32 * mel, 0.2 if e % 2 else -0.2)
        t += 2.0

# ---------- arrangement ----------
add(music, 0.0, gong(98, 4.0), 0.5)
add(music, 0.0, pad([note(0), note(2), note(4)], 4.0, 1.5, 1.0), 0.25)
for i, dg in enumerate([5, 7, 8, 10, 12]):
    add(music, 1.0 + i * 0.25, pluck(note(dg), 1.2, 0.8), 0.25, -0.3 + i * 0.15)
groove(4.0, 7.5, drums=0.8, mel=1.0, bass=0.8, density=0.7)
add(music, 7.5, pad([note(0), note(3), note(5)], 3.5, 0.8, 0.8), 0.3)
add(music, 7.5, gong(110, 3.5), 0.25)
groove(8.0, 11.0, drums=0.5, mel=0.0, bass=0.7, density=0.4)
groove(11.0, 38.0, drums=1.0, mel=1.0, bass=1.0, density=1.0)
groove(38.0, 42.0, drums=1.0, mel=0.8, bass=1.0, density=1.0)
groove(42.0, 42.8, drums=1.2, mel=0.0, bass=0.6, density=1.0)
add(music, 42.8, pad([note(0), note(4), note(7)], 2.9, 0.5, 0.5), 0.35)
add(music, 45.5, pad([note(0), note(2), note(5)], 2.3, 1.2, 0.2), 0.35)
for i in range(8):
    add(music, 45.6 + i * 0.25, pluck(note(5 + i), 0.8, 0.8), 0.18, -0.4 + i * 0.1)
FT = scenes.FULL_T
groove(FT, 49.4, drums=1.1, mel=1.2, bass=1.0, density=1.0)
add(music, FT, pad([note(0), note(2), note(4), note(7)], DUR - FT, 0.05, 1.2), 0.35)
add(music, 49.4, gong(98, 0.6), 0.4)
for i, dg in enumerate([0, 2, 4, 5, 7]):
    add(music, 49.4 + i * 0.02, pluck(note(dg, 1), 0.6, 0.6), 0.2)

# ---------- SFX ----------
def sfx_get(i):
    j = i % 10
    f = note(5 + j % 8)
    s = 0.6 * sine(f * 2, 0.18) * envd(0.18, 0.06) + 0.4 * sine(f * 3, 0.18) * envd(0.18, 0.04)
    s2 = np.concatenate([np.zeros(int(0.045 * SR)), 0.5 * sine(f * 2 * 1.498, 0.2) * envd(0.2, 0.08)])
    out = np.zeros(max(len(s), len(s2))); out[:len(s)] += s; out[:len(s2)] += s2
    return out

def S(*parts):
    n = max(len(p) for p in parts); out = np.zeros(n)
    for p in parts: out[:len(p)] += p
    return out

def mk(name, p):
    if name == 'get': return sfx_get(p), 0.35, 0.5
    if name == 'plus': return sum(bell(note(k, 1), 1.0, 0.4) for k in (5, 7, 9)) / 2, 0.35, 0
    if name == 'burst': return S(sine(lambda x: 300 + 1500 * x / 0.12, 0.12) * envd(0.12, 0.05), 0.3 * hp(noise(0.1), 2000) * envd(0.1, 0.02)), 0.45, 0
    if name == 'pop': return sine(lambda x: 250 + 900 * np.minimum(1, x / 0.08), 0.2) * envd(0.2, 0.07), 0.6, 0
    if name == 'boom':
        return S(0.9 * sine(lambda x: 45 + 60 * np.exp(-x / 0.08), 1.2) * envd(1.2, 0.45), 0.5 * lp(noise(1.0), 900) * envd(1.0, 0.2)), 0.85, 0
    if name == 'boing': return sine(lambda x: 220 + 500 * np.minimum(1, x / 0.25) + 30 * np.sin(x * 60), 0.35) * envd(0.35, 0.15), 0.4, 0
    if name == 'sparkle':
        out = np.zeros(int(0.8 * SR))
        for k, dg in enumerate([10, 12, 14, 15]):
            b = bell(note(dg), 0.6, 0.2); i0 = int(k * 0.05 * SR); out[i0:i0 + len(b)] += b[:len(out) - i0]
        return out, 0.25, 0.3
    if name == 'draw': return bp(noise(0.9), 2500, 7000) * (0.5 + 0.5 * np.abs(np.sin(tt(0.9) * 40))) * np.sin(np.pi * tt(0.9) / 0.9), 0.18, -0.2
    if name == 'tick': return S(sine(1100 + p * 60, 0.06) * envd(0.06, 0.015), 0.3 * bp(noise(0.05), 2000, 5000) * envd(0.05, 0.01)), 0.35, -0.5 + p * 0.12
    if name == 'chime': return bell(note(10), 1.4, 0.6) + 0.6 * bell(note(12), 1.4, 0.6), 0.25, 0
    if name == 'whoosh': return whoosh(0.4), 0.35, 0
    if name == 'night': return whoosh(1.2, 300, 1500), 0.15, 0
    if name == 'stamp': return S(0.9 * sine(lambda x: 70 + 120 * np.exp(-x / 0.03), 0.5) * envd(0.5, 0.15), 0.4 * lp(noise(0.2), 1500) * envd(0.2, 0.04)), 0.8, 0
    if name == 'throw': return whoosh(0.3, 800, 5000), 0.3, -0.3
    if name == 'clatter':
        out = np.zeros(int(0.6 * SR))
        for k, (dt, f) in enumerate([(0, 900), (0.05, 1150), (0.09, 820), (0.16, 1300), (0.24, 1000), (0.33, 1200)]):
            s = S(sine(f, 0.1) * envd(0.1, 0.02), 0.4 * bp(noise(0.08), 1500, 4000) * envd(0.08, 0.012))
            i0 = int(dt * SR); out[i0:i0 + len(s)] += s * (1 - k * 0.1)
        return out, 0.6, 0.2
    if name == 'kick': return S(sine(lambda x: 380 + 250 * np.exp(-x / 0.02), 0.12) * envd(0.12, 0.03), 0.3 * bp(noise(0.05), 1000, 3000) * envd(0.05, 0.01)), 0.55, -0.1
    if name == 'tok':
        return S(sine(700, 0.1) * envd(0.1, 0.02), 0.5 * bell(1320, 0.6, 0.25)), 0.5, 0.4
    if name == 'whip': return S(hp(noise(0.15), 2500) * envd(0.15, 0.015), 0.3 * whoosh(0.15, 1000, 6000)), 0.6, 0.1
    if name == 'wind': return whoosh(1.6, 200, 1200), 0.3, 0.3
    if name == 'chant':
        out = np.zeros(int(1.2 * SR))
        for k, (dg, d) in enumerate([(5, 0.22), (5, 0.22), (7, 0.22), (8, 0.5)]):
            f = note(dg); x = tt(d)
            s = sum(np.sin(2 * np.pi * f * h * x * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * x))) / h for h in range(1, 6))
            s = lp(s, 1800) * np.minimum(1, x / 0.03) * np.minimum(1, (d - x) / 0.05)
            i0 = int(sum(dd for _, dd in [(5, 0.22), (5, 0.22), (7, 0.22), (8, 0.5)][:k]) * SR)
            out[i0:i0 + len(s)] += s
        return out, 0.22, 0
    if name == 'land': return S(0.8 * sine(lambda x: 55 + 60 * np.exp(-x / 0.03), 0.35) * envd(0.35, 0.1), 0.3 * sine(420, 0.1) * envd(0.1, 0.02)), 0.7, 0
    if name == 'jump': return sine(lambda x: 250 + (p * 1.5) * np.minimum(1, x / 0.25), 0.3) * envd(0.3, 0.12), 0.3, 0
    if name == 'riser': x = tt(0.65); return (0.5 * sine(lambda y: 200 + 1200 * (y / 0.65) ** 2, 0.65) + 0.4 * whoosh(0.65, 400, 6000)) * (x / 0.65), 0.4, 0
    if name == 'launch': return S(mk('boom', 0)[0], whoosh(1.2, 300, 6000)), 0.7, 0
    if name == 'fill': return pluck(note(7 + (p // 3) % 8, 1), 0.4, 0.8), 0.12, -0.3 + ((p * 7) % 10) / 15
    if name == 'firework':
        out = 0.6 * lp(noise(0.3), 1200) * envd(0.3, 0.06)
        cr = np.zeros(int(0.9 * SR))
        for k in range(28):
            i0 = int(rng.uniform(0.1, 0.85) * SR); s = hp(noise(0.01), 3000) * envd(0.01, 0.003)
            cr[i0:i0 + len(s)] += s[:len(cr) - i0] * rng.uniform(0.3, 1)
        cr[:len(out)] += out
        return cr, 0.35, 0
    if name == 'ending': return sum(bell(note(k, 1), 2.0, 0.9) for k in (0, 2, 4, 7)) / 2, 0.3, 0
    return None, 0, 0

for (t, name, p) in scenes.EVENTS:
    s, g, pan = mk(name, p)
    if s is not None:
        add(sfx, t, s, g, pan)

mix = music * 0.55 + sfx * 0.8
# gentle stereo room: short delay
dl = int(0.021 * SR)
mix[dl:, 0] += 0.12 * mix[:-dl, 1]; mix[dl:, 1] += 0.12 * mix[:-dl, 0]
fade = np.minimum(1, (DUR - np.arange(N) / SR) / 0.35)[:, None]
mix *= fade
mix = mix / (np.abs(mix).max() + 1e-9) * 1.4
mix = np.tanh(mix) * 0.92
with wave.open('audio.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('audio ok', mix.shape, len(scenes.EVENTS), 'events')
