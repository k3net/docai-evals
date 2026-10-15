#!/usr/bin/env python3
"""A 03-as kör blogposztjának ábrái (docai.hu, „Az általános döntési adapter, amely nem lett általános”), a 00/01
tanulmány ábráinak palettájával és segédfüggvényeivel (publikacio/abrak/abrak.py).

    python3 kor03/publikacio/abrak03.py      # SVG-k ide, PNG-k a png/ alá (fej nélküli Chrome, 1,5625×)

Mind MÉRT ADAT, a kor03/eredmenyek/F4 gépi kimeneteiből:
  1 · kockázat–lefedettség a három kitartott csoporton (abra_adat03.json, a Sparkon a kiolvasásokból számolva)
  2 · az „egyik sem” felismerése forrásonként (f4_elemzes03.json leíró blokkja, f4_leiro03.json)
  3 · lefedettség azonos, 95 %-os pontosságon, a kétlépcsős döntéssel (f4_ketlepcso03.json; feltáró)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "publikacio/abrak"))
from abrak import AKC, AKC2, BG, DIM, FG, FONT, GRID, OK, VESZ, arrow, fej, line, pct, pct_range, txt  # noqa: E402

F4R = ROOT / "kor03/eredmenyek/F4"
G3 = ("k03v2_g3_s1", "k03v2_g3_s2", "k03v2_g3_s3")
L3 = {"ho-termek": ("l3mixse_h2_s1", "l3mixse_h2_s2", "l3mixse_h2_s3"),
      "ho-routing": ("k01_l3mixse_p30_s1", "k01_l3mixse_p30_s2", "k01_l3mixse_p30_s3")}
REF = "#9aa4b1"  # a feladatspecifikus adapter (referencia) jele

T = {
    "hu": {
        "f1_cim": "Három ismeretlen feladat: az adapter többet dönt, de több hibával",
        "f1_al": "kockázat–lefedettség a kitartott csoportokon · vízszintesen a gép által besorolt tételek aránya, "
                 "függőlegesen a hibaarány a besoroltak közt · lejjebb = jobb · szaggatott vonal: 95 % pontosság",
        "panels": [("termékpárosítás", "4524 pontozott item"), ("eszközválasztás", "7416 pontozott item"),
                   ("számlaellenőrzés", "2200 pontozott item")],
        "xt": "automatikusan besorolt", "yt": "hibaarány", "cel": "95 %", "plafon": "plafon",
        "l1": "kalibrált alapmodell (L1★)", "g3": "általános adapter (G3, 3 seed)",
        "mp": "a validáción választott 95 %-os küszöb munkapontja", "mp_cim": "pontosság a munkaponton",
        "f1_foot": "Az adapter munkapontjai mindhárom csoportban a 95 %-os pontossági vonal fölött vannak: a validáción "
                   "választott küszöb az ismeretlen feladatokon túl engedékeny. A számlaellenőrzésen az adapter görbéi a lefedettség "
                   "felső felében az alapmodellé alatt futnak, a pontossága mégis 90,5 %, mert a küszöb ott is laza.",
        "f2_cim": "Az „egyik sem” felismerése: ahol az adapter rontott, és az egy hely, ahol javított",
        "f2_al": "az „egyik sem” esetek aránya, amelyekre a modell legvalószínűbb válasza X, küszöbtől függetlenül",
        "rows": [("termékpárosítás · a jó cikk nincs a listán", "hasonló, de nem azonos cikk maradt"),
                 ("eszközválasztás · BFCL irrelevancia", "a kérésre nincs illő eszköz"),
                 ("eszközválasztás · BFCL-live irrelevancia", "valós felhasználói kérések"),
                 ("eszközválasztás · When2Call „nem megválaszolható”", "közeli, de nem illő eszközök"),
                 ("számlaellenőrzés · „egyik tételsor sem hibás”", "természetes „egyik sem”")],
        "f2_l1": "kalibrált alapmodell (L1★)", "f2_g3": "általános adapter (G3, 3 seed tartománya)",
        "f2_ref": "a saját feladatán tanított adapter (az októberi adapterek)",
        "f2_foot": "A tanító „egyik sem” esetek negyede más feladathoz tartozó kérés volt; a saját családjain az "
                   "adapter ezt 15 %-ról 94 %-ra tanulta meg, az eszközválasztásra mégsem vitte át.",
        "f3_cim": "Azonos, 95 %-os pontosságon az adapter nem nyer",
        "f3_al": "automatikusan besorolt tételek aránya, ha a küszöböt magán a teszten igazítjuk 95 %-os pontossághoz "
                 "(felső becslés, élesben nem tehető meg)",
        "f3_groups": ["termékpárosítás", "eszközválasztás", "számlaellenőrzés"],
        "f3_rows": ["kalibrált alapmodell (L1★)", "általános adapter (G3)", "kétlépcsős: X az alapmodellből, opció az adapterből"],
        "f3_x": "automatikusan besorolt 95 %-os pontosságon",
        "f3_foot": "Az adapter magabiztos „egyik sem”-hibái a rangsor elején vannak, ezért az eszközválasztásban a "
                   "95 % szinte elérhetetlen. A kétlépcsős döntés utólagos, feltáró elemzés.",
        "dec": ",", "pct": " %",
    },
    "en": {
        "f1_cim": "Three unseen tasks: the adapter decides more, with more errors",
        "f1_al": "risk–coverage on the held-out groups · horizontally the share of items the machine assigns, "
                 "vertically the error rate among them · lower = better · dashed line: 95% precision",
        "panels": [("product matching", "4,524 scored items"), ("tool selection", "7,416 scored items"),
                   ("invoice checking", "2,200 scored items")],
        "xt": "assigned automatically", "yt": "error rate", "cel": "95%", "plafon": "ceiling",
        "l1": "calibrated base model (L1★)", "g3": "general adapter (G3, 3 seeds)",
        "mp": "operating point of the 95% threshold chosen on validation", "mp_cim": "precision at the operating point",
        "f1_foot": "The adapter's operating points sit above the 95% precision line in all three groups: the validation "
                   "threshold is too permissive on unseen tasks. On invoice checking the adapter's curves run below the "
                   "base model's in the upper half of coverage, yet its precision is 90.5%, because the threshold is loose there too.",
        "f2_cim": "Recognising “none of these”: where the adapter hurt, and the one place it helped",
        "f2_al": "share of “none of these” items whose most likely answer is X, independent of any threshold",
        "rows": [("product matching · the right article is not listed", "a similar but different article remains"),
                 ("tool selection · BFCL irrelevance", "no tool fits the request"),
                 ("tool selection · BFCL-live irrelevance", "real user requests"),
                 ("tool selection · When2Call “cannot answer”", "close but unsuitable tools"),
                 ("invoice checking · “no line item is wrong”", "natural “none of these”")],
        "f2_l1": "calibrated base model (L1★)", "f2_g3": "general adapter (G3, range of 3 seeds)",
        "f2_ref": "adapter trained on that task (our October adapters)",
        "f2_foot": "A quarter of the training “none of these” items were requests belonging to another task; on its own "
                   "families the adapter learned this from 15% to 94%, but did not carry it to tool selection.",
        "f3_cim": "At the same 95% precision, the adapter does not win",
        "f3_al": "share of items assigned automatically when the threshold is tuned on the test itself for 95% precision "
                 "(an upper bound; not possible in production)",
        "f3_groups": ["product matching", "tool selection", "invoice checking"],
        "f3_rows": ["calibrated base model (L1★)", "general adapter (G3)", "two-stage: X from base, option from adapter"],
        "f3_x": "assigned automatically at 95% precision",
        "f3_foot": "The adapter's confident “none of these” errors sit at the top of its ranking, so in tool selection "
                   "95% is almost out of reach. The two-stage decision is a post-hoc, exploratory analysis.",
        "dec": ".", "pct": "%",
    },
}


def rng(vals):
    return min(vals), max(vals)


# ─────────────────────────────── 1 · kockázat–lefedettség, három panel
def fig1(A, L):
    t = T[L]
    W, H = 1200, 640
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         fej(W, t["f1_cim"], t["f1_al"])]
    XMAX, YMAX, PW, PH, Y0 = 0.9, 0.30, 320, 300, 150
    for k, (g, x0) in enumerate((("ho-termek", 90), ("ho-routing", 465), ("ho-uj", 840))):
        r = A[g]
        sx = lambda c, x0=x0: x0 + c / XMAX * PW  # noqa: E731
        sy = lambda v: Y0 + PH - min(v, YMAX) / YMAX * PH  # noqa: E731
        cim, n = t["panels"][k]
        o.append(txt(x0, Y0 - 26, cim, 15, FG, weight="600"))
        o.append(txt(x0 + PW, Y0 - 26, n, 12, DIM, "end"))
        for v in (0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30):
            o.append(line(x0, sy(v), x0 + PW, sy(v), GRID))
            if k == 0:
                o.append(txt(x0 - 10, sy(v) + 4, pct(v, L), 11, DIM, "end"))
        for c in (0, 0.2, 0.4, 0.6, 0.8):
            o.append(line(sx(c), Y0 + PH, sx(c), Y0 + PH + 5, DIM))
            o.append(txt(sx(c), Y0 + PH + 20, pct(c, L), 11, DIM, "middle"))
        o.append(txt(x0 + PW / 2, Y0 + PH + 42, t["xt"], 12, DIM, "middle"))
        if k == 0:
            o.append(f'<text x="{x0 - 56}" y="{Y0 + PH / 2}" font-family="{FONT}" font-size="12" fill="{DIM}" '
                     f'text-anchor="middle" transform="rotate(-90 {x0 - 56} {Y0 + PH / 2})">{t["yt"]}</text>')
        px = sx(r["plafon"])
        o.append(line(px, Y0, px, Y0 + PH, DIM, 1.2, "2 4"))
        o.append(txt(px - 5, Y0 + 14, t["plafon"], 11, DIM, "end"))
        o.append(line(x0, sy(0.05), x0 + PW, sy(0.05), FG, 1.2, "6 5", 0.55))
        o.append(f'<rect x="{x0 + PW - 40}" y="{sy(0.05) + 4:.1f}" width="40" height="17" fill="{BG}"/>')
        o.append(txt(x0 + PW - 4, sy(0.05) + 17, t["cel"], 11, FG, "end"))
        K = r["karok"]
        for key, color, sw in [(s, AKC2, 1.7) for s in G3] + [("L1", AKC, 2.8)]:
            pts = " ".join(f"{sx(c):.1f},{sy(v):.1f}" for c, v in K[key]["gorbe"] if 0.04 <= c <= XMAX)
            o.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{sw}" '
                     f'stroke-linejoin="round" stroke-opacity="{0.9 if key != "L1" else 1}"/>')
        for key, color in [(s, AKC2) for s in G3] + [("L1", AKC)]:
            m = K[key]["munkapont"]
            o.append(f'<circle cx="{sx(m["lef"]):.1f}" cy="{sy(1 - m["prec"]):.1f}" r="5.5" fill="{color}" '
                     f'stroke="{BG}" stroke-width="2"/>')
        # a munkapontok pontossága a panel alján: alapmodell / adapter (3 seed)
        p1 = K["L1"]["munkapont"]["prec"]
        p3 = [K[s]["munkapont"]["prec"] for s in G3]
        o.append(txt(x0 + 10, Y0 + 22, t["mp_cim"], 11, DIM))
        o.append(txt(x0 + 10, Y0 + 42, pct(p1, L, 1), 14, AKC, weight="600"))
        o.append(txt(x0 + 10, Y0 + 62, pct_range(*rng(p3), L, 1), 14, AKC2, weight="600"))
    ly = H - 62
    o.append(line(90, ly - 4, 120, ly - 4, AKC, 2.8) + txt(128, ly, t["l1"], 12, FG))
    o.append(line(360, ly - 4, 390, ly - 4, AKC2, 1.8) + txt(398, ly, t["g3"], 12, FG))
    o.append(f'<circle cx="662" cy="{ly - 4}" r="5.5" fill="{DIM}" stroke="{BG}" stroke-width="2"/>'
             + txt(674, ly, t["mp"], 12, FG))
    for i, s in enumerate(wrap(t["f1_foot"], 150)):
        o.append(txt(40, H - 30 + 16 * i, s, 12, DIM))
    o.append("</svg>")
    return "\n".join(o)


def wrap(s, n):
    out, cur = [], ""
    for w in s.split():
        if len(cur) + len(w) + 1 > n:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    return out + [cur]


# ─────────────────────────────── 2 · az „egyik sem” felismerése
def fig2(cells, L):
    t = T[L]
    W, H = 1200, 560
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         fej(W, t["f2_cim"], t["f2_al"])]
    X0, X1, Y0, DY = 520, 1130, 128, 66
    sx = lambda v: X0 + v * (X1 - X0)  # noqa: E731
    yb = Y0 + DY * (len(cells) - 1) + 34
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        o.append(line(sx(v), Y0 - 22, sx(v), yb, GRID))
        o.append(txt(sx(v), yb + 18, pct(v, L), 11, DIM, "middle"))
    for i, (cell, (cim, al)) in enumerate(zip(cells, t["rows"])):
        y = Y0 + i * DY
        if i in (1, 4):
            o.append(line(40, y - 33, X1, y - 33, GRID, 1, "3 4"))
        o.append(txt(40, y - 2, cim, 14, FG, weight="600"))
        ns = f"{cell['n']:,}".replace(",", " " if L == "hu" else ",")
        o.append(txt(40, y + 16, f"{al} · n = {ns}", 12, DIM))
        b, g3 = cell["L1"], cell["G3"]
        mean = sum(g3) / len(g3)
        col = OK if mean > b else VESZ
        o.append(arrow(sx(b), sx(mean), y + 4, col))
        lo, hi = rng(g3)
        o.append(f'<rect x="{sx(lo) - 3:.1f}" y="{y - 3:.1f}" width="{sx(hi) - sx(lo) + 6:.1f}" height="14" rx="7" '
                 f'fill="{AKC2}"/>')
        if cell.get("ref"):
            rlo, rhi = rng(cell["ref"])
            rx = sx((rlo + rhi) / 2)
            o.append(f'<path d="M {rx:.1f} {y - 6:.1f} L {rx + 8:.1f} {y + 4:.1f} L {rx:.1f} {y + 14:.1f} '
                     f'L {rx - 8:.1f} {y + 4:.1f} z" fill="{BG}" stroke="{REF}" stroke-width="2"/>')
            o.append(txt(rx, y - 12, pct_range(rlo, rhi, L), 11, REF, "middle"))
        o.append(f'<circle cx="{sx(b):.1f}" cy="{y + 4:.1f}" r="7.5" fill="{AKC}" stroke="{BG}" stroke-width="2"/>')
        up = mean > b
        o.append(txt(sx(b) + (-12 if up else 12), y + 9, pct(b, L), 13, AKC, "end" if up else "start", "600"))
        o.append(txt(sx(hi if up else lo) + (12 if up else -12), y + 9, pct_range(lo, hi, L), 13, AKC2,
                     "start" if up else "end", "600"))
    ly = H - 66
    o.append(f'<circle cx="48" cy="{ly - 4}" r="6.5" fill="{AKC}"/>' + txt(62, ly, t["f2_l1"], 12, FG))
    o.append(f'<rect x="300" y="{ly - 10}" width="30" height="12" rx="6" fill="{AKC2}"/>' + txt(340, ly, t["f2_g3"], 12, FG))
    o.append(f'<path d="M 655 {ly - 12} L 663 {ly - 4} L 655 {ly + 4} L 647 {ly - 4} z" fill="{BG}" stroke="{REF}" '
             f'stroke-width="2"/>' + txt(672, ly, t["f2_ref"], 12, FG))
    for i, s in enumerate(wrap(t["f2_foot"], 150)):
        o.append(txt(40, H - 30 + 16 * i, s, 12, DIM))
    o.append("</svg>")
    return "\n".join(o)


# ─────────────────────────────── 3 · lefedettség azonos pontosságon
def fig3(K2, L):
    t = T[L]
    W, H = 1200, 520
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         fej(W, t["f3_cim"], t["f3_al"])]
    X0, X1, Y0, GH, BH, XMAX = (330 if L == "hu" else 380), 1100, 120, 112, 22, 0.8
    sx = lambda v: X0 + v / XMAX * (X1 - X0)  # noqa: E731
    yb = Y0 + GH * 3 - 24
    for v in (0, 0.2, 0.4, 0.6, 0.8):
        o.append(line(sx(v), Y0 - 18, sx(v), yb, GRID))
        o.append(txt(sx(v), yb + 18, pct(v, L), 11, DIM, "middle"))
    o.append(txt((X0 + X1) / 2, yb + 38, t["f3_x"], 12, DIM, "middle"))
    cols = (AKC, AKC2, OK)
    for gi, g in enumerate(("ho-termek", "ho-routing", "ho-uj")):
        P = K2["pont"][g]
        y0 = Y0 + gi * GH
        if gi:
            o.append(line(40, y0 - 22, X1, y0 - 22, GRID, 1, "3 4"))
        o.append(txt(40, y0 + 4, t["f3_groups"][gi], 15, FG, weight="600"))
        rows = [[P["L1"]["lef_azonos_95_precizitason"]],
                [P[a]["lef_azonos_95_precizitason"] for a in G3],
                [P[f"kapu:{a}"]["lef_azonos_95_precizitason"] for a in G3]]
        for ri, (vals, col) in enumerate(zip(rows, cols)):
            y = y0 - 12 + ri * (BH + 6)
            lo, hi = rng(vals)
            o.append(f'<rect x="{X0}" y="{y}" width="{max(sx(lo) - X0, 1.5):.1f}" height="{BH}" rx="3" fill="{col}"/>')
            if hi > lo:
                o.append(f'<rect x="{sx(lo):.1f}" y="{y}" width="{sx(hi) - sx(lo):.1f}" height="{BH}" rx="3" '
                         f'fill="{col}" fill-opacity="0.45"/>')
            o.append(txt(sx(hi) + 10, y + BH - 6, pct_range(lo, hi, L, 1), 13, FG, weight="600"))
            if gi == 0:
                o.append(txt(X0 - 12, y + BH - 6, t["f3_rows"][ri], 12, col, "end", "600"))
    for i, s in enumerate(wrap(t["f3_foot"], 150)):
        o.append(txt(40, H - 30 + 16 * i, s, 12, DIM))
    o.append("</svg>")
    return "\n".join(o)


def render(name, svg):
    p = HERE / f"{name}.svg"
    p.write_text(svg, encoding="utf-8")
    (HERE / "png").mkdir(exist_ok=True)
    w, h = (int(v) for v in re.search(r'width="(\d+)" height="(\d+)"', svg).groups())
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                    "--force-device-scale-factor=1.5625", f"--window-size={w},{h}",
                    f"--screenshot={HERE / 'png' / f'{name}.png'}", p.as_uri()],
                   check=True, capture_output=True, timeout=120)
    subprocess.run(["pngquant", "--force", "--quality=85-98", "--ext", ".png", str(HERE / "png" / f"{name}.png")],
                   check=True)


def cells_egyik_sem(E, Lr):
    """Az X-fedés sorai: pont_minden_reteg (típusonként) és a leíró bontás (forrásonként)."""
    P = E["leiro"]["pont_minden_reteg"]
    tip = lambda g, a, typ: P[g][a]["x_fedes_tipusonkent"][typ]  # noqa: E731
    bont = Lr["bontas"]["ho-routing"]
    src = lambda k, a: bont[k][a]["x_fedes"]  # noqa: E731
    seeds = lambda k: [bont[k]["G3_seedenkent"][s]["x_fedes"] for s in bont[k]["G3_seedenkent"]]  # noqa: E731
    return [
        {"n": tip("ho-termek", "L1", "gold-drop")["n"], "L1": tip("ho-termek", "L1", "gold-drop")["x_fedes"],
         "G3": [tip("ho-termek", s, "gold-drop")["x_fedes"] for s in G3],
         "ref": [tip("ho-termek", a, "gold-drop")["x_fedes"] for a in L3["ho-termek"]]},
        {"n": bont["bfcl_irrelevance"]["L1"]["n_x"], "L1": src("bfcl_irrelevance", "L1"), "G3": seeds("bfcl_irrelevance"),
         "ref": [src("bfcl_irrelevance", "L3-spec")]},
        {"n": bont["bfcl_live_irrelevance"]["L1"]["n_x"], "L1": src("bfcl_live_irrelevance", "L1"),
         "G3": seeds("bfcl_live_irrelevance"), "ref": [src("bfcl_live_irrelevance", "L3-spec")]},
        {"n": bont["w2c_teszt"]["L1"]["n_x"], "L1": src("w2c_teszt", "L1"), "G3": seeds("w2c_teszt"),
         "ref": [src("w2c_teszt", "L3-spec")]},
        {"n": tip("ho-uj", "L1", "natural")["n"], "L1": tip("ho-uj", "L1", "natural")["x_fedes"],
         "G3": [tip("ho-uj", s, "natural")["x_fedes"] for s in G3]},
    ]


def main():
    A = json.loads((F4R / "abra_adat03.json").read_text(encoding="utf-8"))
    E = json.loads((F4R / "f4_elemzes03.json").read_text(encoding="utf-8"))
    Lr = json.loads((F4R / "f4_leiro03.json").read_text(encoding="utf-8"))
    K2 = json.loads((F4R / "f4_ketlepcso03.json").read_text(encoding="utf-8"))
    cells = cells_egyik_sem(E, Lr)
    render("1_kockazat_lefedettseg", fig1(A, "hu"))
    render("1_risk_coverage_en", fig1(A, "en"))
    render("2_egyik_sem", fig2(cells, "hu"))
    render("2_none_of_these_en", fig2(cells, "en"))
    render("3_azonos_pontossag", fig3(K2, "hu"))
    render("3_equal_precision_en", fig3(K2, "en"))
    # a számok, amelyeket az ábrák mutatnak, ellenőrzéshez
    print(json.dumps({"egyik_sem": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in c.items() if k != "G3"}
                                    | {"G3": [round(x, 3) for x in c["G3"]]} for c in cells]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
