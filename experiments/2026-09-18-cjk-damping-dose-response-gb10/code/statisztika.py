#!/usr/bin/env python3
"""A runbook §5 statisztikai protokollja, egy helyen — csak `math`-tal.

Miért nem scipy. A mérés a measurement-host HOST pythonjában is futtatható kell hogy legyen (a
konténer csak a kiszolgálóhoz kell), és a csomagnak reprodukálhatónak kell lennie
függőségek nélkül. Minden eljárás zárt alakban vagy felezéssel van megoldva, és
öntesztek ellenőrzik ismert értékekhez.

### Az eljárások és miért éppen ezek

`wilson`         Arányok 95 %-os CI-je. Nulla és teljes találatnál is értelmes, a
                 normális közelítéssel ellentétben — a mi karainknál pontosan ez a
                 helyzet (0/M kockázat, ~100 % pass-rate).

`poisson_felso`  ⛔ A `0/M` ÖNMAGÁBAN NEM EREDMÉNY. Egy nulla esemény melletti felső
                 korlát nélkül a „nincs kockázat” állítás a mintanagyságot hallgatja el.
                 Ez adja a „< X/M” számot a tényleges pozíciószámmal.

`mcnemar`        Karok párosított összevetése UGYANAZOKON az itemeken. A független
                 kétmintás próba itt téves lenne: az itemek nehézsége közös, és a
                 párosítás pont ezt a varianciát viszi ki.

`parositott_kulonbseg`  A nem-inferioritási döntéshez: a pass-rate különbségének
                 pontbecslése és CI-je párosított mintán. A runbook −2 pontos margója
                 ezen a CI-n olvasható le.

`holm`           Nyolc kontroll-ellenes összevetés × két elsődleges végpont. Korrekció
                 nélkül a véletlen találat gyakorlatilag biztos.
"""
import math

Z95 = 1.959963984540054


# ---------------------------------------------------------------- arányok
def wilson(k, n, z=Z95):
    """Wilson-féle CI egy arányra. Visszaad: (pont, also, felso)."""
    if n == 0:
        return (0.0, 0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    kozep = (p + z * z / (2 * n)) / d
    fel = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, kozep - fel), min(1.0, kozep + fel))


# ---------------------------------------------------------------- Poisson
def _poisson_cdf(k, lam):
    """P(X ≤ k | λ). Logaritmikus tagokkal, hogy nagy λ-nál se csorduljon alá."""
    ossz = 0.0
    for i in range(k + 1):
        ossz += math.exp(-lam + i * math.log(lam) - math.lgamma(i + 1)) if lam > 0 else (1.0 if i == 0 else 0.0)
    return min(1.0, ossz)


def poisson_felso(k, alfa=0.05):
    """Egyoldali 95 %-os EXACT felső korlát a λ intenzitásra k megfigyelt esemény mellett.

    A definíció: a legnagyobb λ, amire P(X ≤ k | λ) ≥ alfa — felezéssel megoldva.
    k=0-ra az ismert zárt alak −ln(alfa) = 2,9957 (alfa=0,05).
    """
    if k == 0:
        return -math.log(alfa)
    lo, hi = 0.0, max(10.0, 2.0 * (k + 10))
    while _poisson_cdf(k, hi) > alfa:
        hi *= 2
    for _ in range(200):
        kozep = (lo + hi) / 2
        if _poisson_cdf(k, kozep) > alfa:
            lo = kozep
        else:
            hi = kozep
    return (lo + hi) / 2


def kockazat_felso_per_millio(esemeny, pozicio, alfa=0.05):
    """A Han-kockázat felső korlátja millió pozícióra vetítve.

    Ez az a szám, ami a „0,0/M” mellé KÖTELEZŐ: megmondja, mit zár ki a mérés.
    """
    if pozicio <= 0:
        return float('inf')
    return 1e6 * poisson_felso(esemeny, alfa) / pozicio


# ---------------------------------------------------------------- párosított
def _binom_ketoldali(b, n):
    """Kétoldali exact binomiális p-érték p=0,5 mellett (az előjelpróba magja)."""
    if n == 0:
        return 1.0
    def tag(i):
        return math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
                        - n * math.log(2))
    megf = tag(b)
    # numerikus tűrés: az azonos valószínűségű farokelemek is beszámítanak
    return min(1.0, sum(tag(i) for i in range(n + 1) if tag(i) <= megf * (1 + 1e-9)))


def mcnemar(b, c):
    """McNemar-próba két párosított bináris karra.

    `b` = az A kar átment, a B elbukott; `c` = fordítva. A konkordáns párok nem
    hordoznak információt — ezért nem is szerepelnek.

    Kis n-nél (b+c < 25) EXACT binomiális, különben folytonossági korrekcióval
    közelített khí-négyzet. A runbook „kis n-nél exact” előírása így teljesül.
    """
    n = b + c
    if n == 0:
        return {'b': b, 'c': c, 'p': 1.0, 'mod': 'nincs diszkordáns pár'}
    if n < 25:
        return {'b': b, 'c': c, 'p': _binom_ketoldali(b, n), 'mod': 'exact'}
    khi = (abs(b - c) - 1) ** 2 / n
    return {'b': b, 'c': c, 'p': math.erfc(math.sqrt(khi / 2)), 'mod': 'khí² (korrigált)'}


def parositott_kulonbseg(b, c, n, z=Z95):
    """A pass-rate KÜLÖNBSÉGE párosított mintán: pontbecslés és CI.

    diff = (b − c) / n, ahol n az összes item. A szórás a diszkordáns párokból jön
    (Wald, párosított arányokra). Ez az a CI, amin a −2 pontos nem-inferioritási margó
    leolvasható: ha a CI alsó vége a margó FÖLÖTT van, a kar nem-inferior.
    """
    if n == 0:
        return (0.0, -1.0, 1.0)
    diff = (b - c) / n
    var = ((b + c) - (b - c) ** 2 / n) / (n * n)
    se = math.sqrt(max(var, 0.0))
    return (diff, diff - z * se, diff + z * se)


# ---------------------------------------------------------------- Holm
def holm(p_ertekek):
    """Holm–Bonferroni korrekció. Bemenet: {nev: p}, kimenet: {nev: korrigált p}.

    A monotonitás kikényszerítve: a korrigált p-k nem csökkenhetnek a rendezésben.
    """
    tetelek = sorted(p_ertekek.items(), key=lambda kv: kv[1])
    m = len(tetelek)
    ki, elozo = {}, 0.0
    for i, (nev, p) in enumerate(tetelek):
        kor = min(1.0, (m - i) * p)
        kor = max(kor, elozo)
        ki[nev] = kor
        elozo = kor
    return ki


# ---------------------------------------------------------------- önteszt
if __name__ == '__main__':
    # Wilson — ismert érték: 0/36 → [0; 0,0964]
    p, lo, hi = wilson(0, 36)
    assert abs(hi - 0.09639) < 1e-4, hi
    p, lo, hi = wilson(36, 36)
    assert abs(lo - 0.90361) < 1e-4, lo
    # szimmetria
    assert abs(wilson(30, 100)[1] - (1 - wilson(70, 100)[2])) < 1e-12

    # Poisson — k=0-ra a zárt alak
    assert abs(poisson_felso(0) - 2.99573) < 1e-4, poisson_felso(0)
    # k=1 → 4,7439 (a khí²-táblázat szerinti exact érték)
    assert abs(poisson_felso(1) - 4.74386) < 1e-4, poisson_felso(1)
    assert abs(poisson_felso(5) - 10.51303) < 1e-4, poisson_felso(5)
    # monoton
    assert poisson_felso(0) < poisson_felso(1) < poisson_felso(2)
    # 0 esemény 340 000 pozícióban → „< 8,8/M”
    assert abs(kockazat_felso_per_millio(0, 340_000) - 8.811) < 1e-2

    # McNemar — exact, ismert eset: b=0, c=6 → p = 2·(1/2)⁶ = 0,03125
    m = mcnemar(0, 6)
    assert m['mod'] == 'exact' and abs(m['p'] - 0.03125) < 1e-9, m
    assert mcnemar(3, 3)['p'] == 1.0
    assert mcnemar(0, 0)['p'] == 1.0
    # nagy n-nél khí²: b=30, c=10 → khí² = (20−1)²/40 = 9,025 → p ≈ 0,00266
    m = mcnemar(30, 10)
    assert m['mod'].startswith('khí') and abs(m['p'] - 0.002664) < 1e-5, m

    # párosított különbség
    d, lo, hi = parositott_kulonbseg(2, 8, 150)
    assert abs(d - (-0.04)) < 1e-12
    assert lo < d < hi
    # nincs eltérés → a CI a nullát fedi
    d, lo, hi = parositott_kulonbseg(0, 0, 150)
    assert d == 0.0 and lo == 0.0 and hi == 0.0

    # Holm — ismert példa
    h = holm({'a': 0.01, 'b': 0.02, 'c': 0.04})
    assert abs(h['a'] - 0.03) < 1e-12 and abs(h['b'] - 0.04) < 1e-12 \
        and abs(h['c'] - 0.04) < 1e-12, h
    # monotonitás kikényszerítve
    h = holm({'a': 0.04, 'b': 0.0001})
    assert h['b'] <= h['a']
    assert all(0 <= v <= 1 for v in h.values())

    print('statisztikai önteszt: minden állítás teljesül')
