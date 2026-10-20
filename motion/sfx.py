"""Efeitos sonoros sintetizados para o Reels da Achiev, sincronizados com reel.html."""
import sys, wave
import numpy as np

SR = 48000
DUR = 23.0
rng = np.random.default_rng(7)
mix = np.zeros((int(SR * DUR) + SR, 2))


def env(n, a, d):
    """envelope ataque linear + decaimento exponencial (segundos)"""
    t = np.arange(n) / SR
    e = np.exp(-t / d)
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    return e


def lowpass(x, cut):
    """passa-baixa de um polo com corte fixo ou variando (array)"""
    cut = np.broadcast_to(cut, x.shape)
    a = np.exp(-2 * np.pi * cut / SR)
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s = (1 - a[i]) * x[i] + a[i] * s
        y[i] = s
    return y


def add(t, sig, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(mix): return
    sig = sig[: len(mix) - i] * gain
    mix[i:i + len(sig), 0] += sig * (1 - pan) ** .5
    mix[i:i + len(sig), 1] += sig * (1 + pan) ** .5


def sine(freq, n):
    ph = 2 * np.pi * np.cumsum(np.broadcast_to(freq, (n,))) / SR
    return np.sin(ph)


def pop(f=600, d=.07):
    n = int(SR * .25); t = np.arange(n) / SR
    fr = f * (1 + .8 * np.exp(-t / .012))
    return sine(fr, n) * env(n, .002, d)


def tick(f=3200):
    n = int(SR * .04)
    nz = rng.standard_normal(n) * env(n, .0005, .004)
    return (sine(f, n) * env(n, .001, .012) * .6 + (nz - lowpass(nz, 2500)) * .5)


def key():
    n = int(SR * .05)
    nz = rng.standard_normal(n) * env(n, .0005, .006)
    return (nz - lowpass(nz, 1800)) * .7 + sine(rng.uniform(1800, 2600), n) * env(n, .001, .008) * .25


def chime(f=880, d=1.1):
    n = int(SR * 2.2)
    s = sine(f, n) + .5 * sine(f * 2.01, n) * np.exp(-np.arange(n) / SR / .35) + .35 * sine(f * 1.5, n)
    return s * env(n, .004, d) * .5


def whoosh(dur=.7, f0=300, f1=4000, peak=.6):
    n = int(SR * dur); t = np.linspace(0, 1, n)
    nz = rng.standard_normal(n)
    cut = f0 + (f1 - f0) * np.sin(np.pi * t) ** 1.2
    band = lowpass(nz, cut) - lowpass(nz, cut * .35)
    e = np.where(t < peak, (t / peak) ** 2, ((1 - t) / (1 - peak)) ** 1.5)
    return band * e * 2.2


def thud(f=90):
    n = int(SR * .45); t = np.arange(n) / SR
    body = sine(f * (1 + 1.2 * np.exp(-t / .03)), n) * env(n, .002, .12)
    nz = lowpass(rng.standard_normal(n), 900) * env(n, .001, .03)
    return body + nz * .8


def boing(f=520):
    n = int(SR * .5); t = np.arange(n) / SR
    fr = f * (1 + .5 * np.exp(-t / .08)) * (1 + .04 * np.sin(2 * np.pi * 14 * t))
    return sine(fr, n) * env(n, .003, .16) * .8


def riser(dur=1.3):
    n = int(SR * dur); t = np.linspace(0, 1, n)
    nz = rng.standard_normal(n)
    hp = nz - lowpass(nz, 400 + 5000 * t)
    tone = sine(220 * 2 ** (2 * t), n) * .25
    return (lowpass(hp, 7000) * .6 + tone) * t ** 2.2


def pad(t0, t1, freqs, gain):
    n = int(SR * (t1 - t0)); t = np.arange(n) / SR
    s = sum(sine(f * (1 + .0015 * np.sin(2 * np.pi * .2 * t + k)), n) for k, f in enumerate(freqs)) / len(freqs)
    fade = np.minimum(1, np.minimum(t / 1.2, (t1 - t0 - t) / 1.0))
    add(t0, lowpass(s, 2500) * np.clip(fade, 0, 1), gain)


# trilha suave de fundo (acordes), mais brilhante a partir do orçamento
pad(0.0, 9.2, [220.0, 277.18, 329.63, 415.30], .11)      # Amaj7
pad(9.0, 14.6, [196.0, 246.94, 293.66, 369.99], .11)     # Gmaj7
pad(14.4, 23.0, [261.63, 329.63, 392.0, 493.88], .13)    # Cmaj7

# 1 notificação
add(.40, chime(988, .9), .5); add(.62, chime(1318, .8), .32, .2)
add(1.55, whoosh(.9, 200, 2500, .5), .25)
# 2 planta + busca
add(2.0, pop(520), .55)
for i in range(10): add(2.3 + i * .14, tick(2600 + i * 90), .12, (i % 3 - 1) * .3)
for i in range(34): add(2.3 + i * (1.1 / 34) + rng.uniform(-.004, .004), key(), .22, rng.uniform(-.3, .3))
for i in range(26): add(4.0 + i * (.6 / 26) + rng.uniform(-.004, .004), key(), .22, rng.uniform(-.3, .3))
add(4.35, whoosh(1.0, 150, 6000, .75), .55)
# 3 casa: paredes e móveis
for i in range(7): add(5.3 + i * .14, thud(80 + i * 6), .42, (i % 2 - .5) * .4)
for i in range(14): add(6.5 + i * .12 + .05, pop(380 + i * 22, .06), .32, ((i * 37) % 7 - 3) / 6)
for i in range(4): add(7.9 + i * .2, pop(900 + i * 120, .05), .3)
# 4 soluções
add(8.95, whoosh(.7, 300, 3000, .45), .3)
add(9.2, pop(480, .09), .55)
for i in range(4):
    add(9.9 + i * .5, tick(2200), .25)
    add(9.9 + i * .5 + .17, chime(660 * 2 ** (i * 4 / 12), .25), .35)
add(11.85, whoosh(.6, 400, 3500, .4), .3)
# 5 ambientes
add(12.2, pop(560, .08), .5)
for i in range(1, 5): add(12.6 + i * .38 - .1, tick(2800), .28); add(12.6 + i * .38 - .08, pop(700 + i * 60, .04), .18)
add(14.2, whoosh(.5, 400, 3000, .4), .28)
# 6 orçamento
add(13.2, riser(1.3), .45)
add(14.45, thud(60), .6); add(14.45, chime(523, 1.6), .35)
add(15.0, pop(600), .5)
for i in range(30): add(15.4 + i * (.9 / 30) + rng.uniform(-.004, .004), key(), .22, rng.uniform(-.3, .3))
add(15.6, whoosh(.5, 300, 2500, .5), .25)
for i in range(5): add(15.8 + i * .08, pop(620 + i * 90, .05), .32, (i - 2) / 3)
add(16.4, boing(560), .45)
add(16.85, whoosh(.6, 300, 5000, .6), .35)
# 7 central de contato
for i, a in enumerate([17.2, 17.3, 17.42, 17.54, 17.64, 17.76]): add(a + .03, pop(420 + i * 70, .07), .42, (i % 2 - .5) * .5)
add(17.2, thud(70), .45)
add(18.45, chime(1046.5, 1.4), .45); add(18.6, chime(1568, 1.2), .3, -.2); add(18.75, chime(2093, 1.0), .2, .2)

# 8 fechamento com o logo
add(19.95, whoosh(.8, 200, 5000, .55), .45)
for i in range(5): add(20.35 + i * .09 + .42, thud(110 + i * 14), .35, (i - 2) / 3); add(20.35 + i * .09 + .44, tick(2400 + i * 200), .2)
add(21.2, thud(55), .55)
add(21.25, chime(784, 2.0), .45); add(21.35, chime(1174.7, 1.8), .32, -.25); add(21.45, chime(1568, 1.6), .25, .25)
for i in range(8): add(21.55 + i * .07, chime(2093 * 2 ** (i / 12), .35), .07, (i % 2 - .5) * .6)

out = mix[: int(SR * DUR)]
out = np.tanh(out * 1.3) / np.tanh(1.3)          # leve saturação para colar a mixagem
out *= .89 / max(1e-9, np.abs(out).max())
fade = np.ones(len(out)); fade[-int(SR * .6):] = np.linspace(1, 0, int(SR * .6))
out *= fade[:, None]
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype("<i2").tobytes())
print("ok", sys.argv[1])
