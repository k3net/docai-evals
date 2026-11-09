#!/usr/bin/env python3
"""A 05–08-as körök blogcikkének ábrái (docai.hu), HU és EN.

    python3 kor08/publikacio/abrak08.py      # SVG-k ide, PNG-k a png/ alá (fej nélküli Chrome, 1,5625×)

Minden szám MÉRT ADAT, futás közben a gépi kimenetekből olvasva (nincs beírt eredmény):
  1 · a lánc lépései egy valódi (szintetikus) tesztételen: kor08/adat/G2/k3, a láncrekord és a döntés lent, PELDA
  2 · hány ügyet zár le a rendszer: kor07/eredmenyek/F5/elemzes.json (k2)
  3 · a lánc a csapdatételeken: kor08/eredmenyek/G5/k2 és J/k2
  4 · a fej az ellenpróbák után: kor08/eredmenyek/{G5,M,N}/k1, a szöveges modellek: G5_utolagos/felszin, M/felszin, N/szoveg.json

Paletta: a korábbi ábrák kék–narancs párja, a sötét módra léptetve (a dataviz-validátoron átment: #4190d0, #c97a2e).
Kék = a modell magában, narancs = amit hozzátettünk. Az azonosítás sosem csak szín: közvetlen felirat és alak is van.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ER = ROOT / "kor08/eredmenyek"
sys.path.insert(0, str(ROOT / "publikacio/abrak"))
from abrak import BG, FG, GRID, line, txt  # noqa: E402

KEK, NAR, SEM = "#4190d0", "#c97a2e", "#aab2bd"
DIM = "#a3adb9"
SZ = "szabaly.koltsegelszamolas"
BA = "penzugy.bankparositas"
HI = "muszaki.hibaelharitas"

# A tesztétel: kor08/adat/G2/k3/items/penzugy.bankparositas.jsonl, id ...:G2K3:hu:MATCH:0000;
# a döntések a G5 pontozásából (cache/k08/pecset/pontoz/{n,l}G2K3_...json, keret4, B1-4 q).
PELDA = {"id": "penzugy.bankparositas:G2K3:hu:MATCH:0000", "osszeg": 688135, "arany": 50, "teljes": 1376270,
         "rossz": "E-2026/6126", "jo": "E-2026/1626", "q_nelkul": 0.665, "q_lanccal": 0.967, "kizart": 4, "marad": 1}

T = {
    "hu": {
        "dec": ",", "ezer": " ",
        "f1_cim": "A lánc: a modell csak idéz és dönt, a számolást kód végzi",
        "f1_al": "egy tétel a tesztből, végig a láncon (szintetikus adat)",
        "f1_tet": "A tétel szövege", "f1_szov": "Összeg: 688 135 Ft · Megjegyzés: a tétel egy számla bruttó összegének 50%-os részlete.",
        "modell": "MODELL", "kod": "KÓD",
        "lep": [("Kinyerés", ["Kigyűjti az adatokat,", "mindet szó szerinti", "idézettel."], "688 135 Ft és 50%"),
                ("Ellenőrzés", ["Az idézet ott van-e a", "szövegben? Kiolvasható-e", "belőle az érték?"], "mindkettő rendben"),
                ("Számítás", ["A részlet arányából", "kiszámolja a teljes", "összeget."], "1 376 270 Ft"),
                ("Összevetés", ["Csak azt zárja ki, ami", "bizonyítottan ellentmond", "az adatoknak."], "4 számla kizárva"),
                ("Döntés", ["A megmaradt jelöltek", "közül választ, a kód", "eredményeivel."], "E-2026/1626")],
        "f1_e1": "Lánc nélkül a modell:", "f1_e1b": "E-2026/6126 · 688 135 Ft", "f1_e1c": "hibás, 67%-os bizonyossággal",
        "f1_e2": "Lánccal a modell:", "f1_e2b": "E-2026/1626 · 1 376 270 Ft", "f1_e2c": "helyes, 97%-os bizonyossággal",
        "f2_cim": "Hány ügyet zárhat le a gép, ha kevés hibát engedünk meg?",
        "f2_al": "a helyesen lezárt ügyek aránya, 5% körüli megengedett hibánál · három feladat átlaga, friss szintetikus teszt, 3000 tétel",
        "f2_rows": [("a modell a saját bizonyosságával", "válasz: egy opció vagy „egyik sem”"),
                    ("ugyanez, az „egyik sem” válaszok hátrasorolva", "egyszerű szabály, tanítás nélkül"),
                    ("négyféle válasz a promptban", "opció, nincs megfelelő, hiányzó adat, kívül esik"),
                    ("ellenőrző fej a régi prompt mellett", "500 példán tanítva a célfeladatról"),
                    ("ellenőrző fej a négyféle válasz mellett", "500 példán tanítva a célfeladatról")],
        "f2_leg": ("a modell magában", "a modell és az ellenőrző fej"),
        "f2_hat": "felső korlát: 80%",
        "f2_foot": ["A tételek ötödénél hiányzó adat vagy feladaton kívüli kérés a jó válasz: ezeket nem lehet lezárni, csak jelezni, ezért 80% a felső korlát.",
                    "A vékony vonal a 95%-os bizonytalansági sáv. A küszöböt külön, 1500 tételes mintán választottuk."],
        "f3_cim": "Ha a számítást kód végzi, a csapdatételek szinte eltűnnek",
        "f3_al": "helyes válaszok aránya azokon a tételeken, ahol a jó válaszhoz számolni kell · szintetikus teszt, előre rögzített mérés",
        "f3_p": ("Első mérés", "Javító kör, friss tételek"),
        "f3_rows": [("banki párosítás", "részfizetés"), ("hibaelhárítás", "mértékegység-váltás"), ("költségelszámolás", "nettó és bruttó, deviza")],
        "f3_n": "{} tétel",
        "f3_leg": ("ugyanaz a modell, lánc nélkül", "a modell lánccal, valódi kinyeréssel"),
        "f3_foot": "A vékony vonal a 95%-os bizonytalansági sáv. A lánc egyik mérésben sem zárta ki a helyes választ, és nem kötött rossz számlát.",
        "f4_cim": "Az ellenőrző fej előnye minden ellenpróbával kisebb lett",
        "f4_al": "mennyire választja szét a gép a dönthető és az eldönthetetlen tételeket (AUROC) · 0,5 = pénzfeldobás, 1,0 = tökéletes",
        "f4_rows": [("1. Az eredeti teszt", ["az eldönthetetlen változat", "egyszerűen rövidebb szöveg"]),
                    ("2. Azonos hosszúságú szövegek", ["egy nem döntő mondattal,", "de más témájú szavakkal"]),
                    ("3. Minimális párok", ["ugyanazok a szavak, csak az", "más, mire vonatkozik a mondat"])],
        "f4_leg": ("csak szöveget látó modell", "a modell bizonyossága", "ellenőrző fej"),
        "f4_nyer": "a fej előnye",
        "f4_foot": ["A csak szöveget látó modell (TF-IDF-osztályozó) az első két tesztben jobb a fejnél: ott a két osztály szavai elárulják a választ. A harmadikban már nem.",
                    "A 2. sorban a szöveges modell értéke a teljes mintán mért. A szögletes zárójel a páros különbség 95%-os intervalluma."],
    },
    "en": {
        "dec": ".", "ezer": ",",
        "f1_cim": "The chain: the model only quotes and decides, code does the arithmetic",
        "f1_al": "one item from the test, through the chain (synthetic data, translated)",
        "f1_tet": "The item text", "f1_szov": "Amount: 688,135 Ft · Note: this item is a 50% instalment of the gross amount of an invoice.",
        "modell": "MODEL", "kod": "CODE",
        "lep": [("Extraction", ["Collects the data,", "each value with a", "verbatim quote."], "688,135 Ft and 50%"),
                ("Verification", ["Is the quote in the text?", "Can the value be read", "from it?"], "both pass"),
                ("Calculation", ["Works out the full", "amount from the", "instalment share."], "1,376,270 Ft"),
                ("Comparison", ["Rules out only what", "provably contradicts", "the data."], "4 invoices ruled out"),
                ("Decision", ["Picks from the remaining", "candidates, with the", "results from code."], "E-2026/1626")],
        "f1_e1": "Without the chain:", "f1_e1b": "E-2026/6126 · 688,135 Ft", "f1_e1c": "wrong, with 67% confidence",
        "f1_e2": "With the chain:", "f1_e2b": "E-2026/1626 · 1,376,270 Ft", "f1_e2c": "right, with 97% confidence",
        "f2_cim": "How many cases can the machine close if few errors are allowed?",
        "f2_al": "share of cases closed correctly, at about 5% allowed error · average of three tasks, fresh synthetic test, 3,000 items",
        "f2_rows": [("the model with its own confidence", "answer: an option or “none of these”"),
                    ("same, “none of these” answers moved last", "a simple rule, no training"),
                    ("four answer types in the prompt", "option, no match, missing data, out of scope"),
                    ("checking head with the old prompt", "trained on 500 examples of the target task"),
                    ("checking head with four answer types", "trained on 500 examples of the target task")],
        "f2_leg": ("the model alone", "the model and the checking head"),
        "f2_hat": "ceiling: 80%",
        "f2_foot": ["For a fifth of the items the right answer is missing data or an out-of-scope request: those can be flagged but not closed, hence the 80% ceiling.",
                    "The thin line is the 95% interval. The threshold was chosen on a separate sample of 1,500 items."],
        "f3_cim": "When code does the arithmetic, the trap items nearly vanish",
        "f3_al": "share of correct answers on items where the right answer needs a calculation · synthetic test, pre-registered measurement",
        "f3_p": ("First measurement", "Repair round, fresh items"),
        "f3_rows": [("bank matching", "partial payment"), ("troubleshooting", "unit conversion"), ("expense claims", "net vs gross, currency")],
        "f3_n": "{} items",
        "f3_leg": ("the same model, no chain", "the model with the chain, real extraction"),
        "f3_foot": "The thin line is the 95% interval. In neither measurement did the chain rule out the right answer or bind a wrong invoice.",
        "f4_cim": "The checking head's edge shrank with every control",
        "f4_al": "how well the machine separates decidable from undecidable items (AUROC) · 0.5 = coin flip, 1.0 = perfect",
        "f4_rows": [("1. The original test", ["the undecidable version is", "simply a shorter text"]),
                    ("2. Equal-length texts", ["with a non-deciding sentence,", "but on different topics"]),
                    ("3. Minimal pairs", ["the same words, only what the", "sentence refers to differs"])],
        "f4_leg": ("text-only model", "the model's confidence", "checking head"),
        "f4_nyer": "head's edge",
        "f4_foot": ["The text-only model (a TF-IDF classifier) beats the head in the first two tests: the words give the answer away. In the third it no longer does.",
                    "In row 2 the text-only value is measured on the full sample. Brackets show the 95% interval of the paired difference."],
    },
}


def szam(v, L, nd=3):
    return f"{v:.{nd}f}".replace(".", T[L]["dec"])


def pc(v, L, nd=1):
    return f"{100 * v:.{nd}f}".replace(".", T[L]["dec"]) + "%"


def wrap(s, n):
    out, cur = [], ""
    for w in s.split():
        if len(cur) + len(w) + 1 > n:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    return out + [cur]


def fej(W, cim, al):
    return (f'<rect width="{W}" height="100%" fill="{BG}"/>' + txt(40, 46, cim, 25, FG, weight="600") + txt(40, 74, al, 15, DIM))


def jl(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


# ─────────────────────────────── 1 · a lánc egy tételen
def fig1(L):
    t = T[L]
    W, H = 1200, 556
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', fej(W, t["f1_cim"], t["f1_al"])]
    o.append(f'<rect x="40" y="100" width="1120" height="62" rx="8" fill="none" stroke="{GRID}" stroke-width="1.5"/>')
    o.append(txt(60, 124, t["f1_tet"], 14, DIM))
    o.append(txt(60, 149, t["f1_szov"], 17, FG))
    CW, GAP, Y0, CH = 200, 30, 190, 240
    kind = ["modell", "kod", "kod", "kod", "modell"]
    for i, (cim, sorok, pelda) in enumerate(t["lep"]):
        x = 40 + i * (CW + GAP)
        col = KEK if kind[i] == "modell" else NAR
        o.append(f'<rect x="{x}" y="{Y0}" width="{CW}" height="{CH}" rx="8" fill="#20252d" stroke="{GRID}" stroke-width="1.5"/>')
        cimke = t[kind[i]]
        w = 14 + 10.5 * len(cimke)
        o.append(f'<rect x="{x + 16}" y="{Y0 + 16}" width="{w:.0f}" height="24" rx="5" fill="{col}"/>')
        o.append(txt(x + 16 + w / 2, Y0 + 33, cimke, 13, BG, "middle", "700"))
        o.append(txt(x + 16, Y0 + 72, cim, 20, FG, weight="600"))
        for j, s in enumerate(sorok):
            o.append(txt(x + 16, Y0 + 102 + j * 22, s, 15, DIM))
        o.append(line(x + 16, Y0 + 180, x + CW - 16, Y0 + 180, GRID, 1))
        o.append(txt(x + 16, Y0 + 212, pelda, 16, FG, weight="600"))
        if i < 4:
            ax, ay = x + CW + 5, Y0 + CH / 2
            o.append(line(ax, ay, ax + 12, ay, DIM, 2))
            o.append(f'<path d="M {ax + 20} {ay} L {ax + 10} {ay - 6} L {ax + 10} {ay + 6} z" fill="{DIM}"/>')
    ys = (476, 524)
    for y, c, a, b, d in ((ys[0], KEK, t["f1_e1"], t["f1_e1b"], t["f1_e1c"]), (ys[1], NAR, t["f1_e2"], t["f1_e2b"], t["f1_e2c"])):
        o.append(f'<circle cx="52" cy="{y - 6}" r="8" fill="{c}"/>')
        o.append(txt(72, y, a, 18, DIM))
        o.append(txt(300, y, b, 18, FG, weight="600"))
        o.append(txt(640, y, d, 18, FG))
    o.append("</svg>")
    return "\n".join(o)


# ─────────────────────────────── 2 · hány ügyet zár le
def fig2(k2, L):
    t = T[L]
    W, H = 1200, 590
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', fej(W, t["f2_cim"], t["f2_al"])]
    karok = [("B1-S", KEK), ("B1-N", KEK), ("B1-4S", KEK), ("B1-R", NAR), ("B1-4R", NAR)]
    X0, X1, Y0, DY, BH, XMAX = 520, 1130, 138, 62, 24, 0.8
    sx = lambda v: X0 + v / XMAX * (X1 - X0)  # noqa: E731
    yb = Y0 + DY * 5 - 8
    for v in (0, 0.2, 0.4, 0.6, 0.8):
        o.append(line(sx(v), Y0 - 16, sx(v), yb, GRID))
        o.append(txt(sx(v), yb + 20, f"{int(v * 100)}%", 13, DIM, "middle"))
    o.append(line(sx(0.8), Y0 - 16, sx(0.8), yb, DIM, 1.4, "5 5"))
    o.append(txt(sx(0.8) - 6, Y0 - 22, t["f2_hat"], 13, DIM, "end"))
    for i, (k, c) in enumerate(karok):
        y = Y0 + i * DY
        if i == 3:
            o.append(line(40, y - 13, X1, y - 13, GRID, 1, "3 4"))
        a = k2["karok"][k]
        v, (lo, hi) = a["hasznos_lef"], a["hasznos_lef_ci95"]
        o.append(txt(40, y + 10, t["f2_rows"][i][0], 17, FG, weight="600"))
        o.append(txt(40, y + 31, t["f2_rows"][i][1], 14, DIM))
        w = max(sx(v) - X0, 0)
        if w > 0:
            r = min(4, w)
            o.append(f'<path d="M {X0} {y} H {X0 + w - r:.1f} Q {X0 + w:.1f} {y} {X0 + w:.1f} {y + r} V {y + BH - r} '
                     f'Q {X0 + w:.1f} {y + BH} {X0 + w - r:.1f} {y + BH} H {X0} z" fill="{c}"/>')
        else:
            o.append(line(X0, y, X0, y + BH, c, 3))
        cy = y + BH / 2
        if hi > lo:
            o.append(line(sx(lo), cy, sx(hi), cy, FG, 1.6))
            for e in (lo, hi):
                o.append(line(sx(e), cy - 5, sx(e), cy + 5, FG, 1.6))
        lab = sx(max(v, hi)) + 12
        o.append(txt(lab, cy + 6, pc(v, L), 17, FG, weight="600"))
    ly = yb + 52
    o.append(f'<rect x="40" y="{ly - 13}" width="16" height="16" rx="3" fill="{KEK}"/>' + txt(64, ly, t["f2_leg"][0], 15, FG))
    o.append(f'<rect x="300" y="{ly - 13}" width="16" height="16" rx="3" fill="{NAR}"/>' + txt(324, ly, t["f2_leg"][1], 15, FG))
    for i, s in enumerate(t["f2_foot"]):
        o.append(txt(40, ly + 32 + i * 22, s, 14, DIM))
    o.append("</svg>")
    return "\n".join(o)


# ─────────────────────────────── 3 · a lánc a csapdatételeken
def fig3(g5, j, L):
    t = T[L]
    W, H = 1200, 560
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', fej(W, t["f3_cim"], t["f3_al"])]
    PAN = ((340, 710), (780, 1150))
    Y0, DY = 186, 92
    fam = (BA, HI, SZ)
    yb = Y0 + DY * 3 - 34
    for pi, (x0, x1) in enumerate(PAN):
        sx = lambda v, a=x0, b=x1: a + v * (b - a)  # noqa: E731
        o.append(txt(x0, Y0 - 58, t["f3_p"][pi], 18, FG, weight="600"))
        for v in (0, 0.25, 0.5, 0.75, 1.0):
            o.append(line(sx(v), Y0 - 40, sx(v), yb, GRID))
            o.append(txt(sx(v), yb + 20, f"{int(v * 100)}%", 13, DIM, "middle"))
        D = (g5 if pi == 0 else j)["csaladok"]
        for i, f in enumerate(fam):
            y = Y0 + i * DY
            p, ci = D[f]["pont"], D[f]["ci95"]
            a, b = p["nelkul"], p["kinyert"]
            o.append(line(sx(a), y, sx(b), y, DIM, 2))
            for v, (lo, hi), c in ((a, ci["nelkul"], KEK), (b, ci["kinyert"], NAR)):
                if hi > lo:
                    o.append(line(sx(lo), y, sx(hi), y, c, 5, None, 0.55))
                o.append(f'<circle cx="{sx(v):.1f}" cy="{y}" r="9" fill="{c}" stroke="{BG}" stroke-width="2"/>')
                o.append(txt(sx(v), y - 17, pc(v, L), 16, FG, "middle", "600"))
            o.append(txt(x0, y + 30, t["f3_n"].format(D[f]["n"]), 13, DIM))
    for i, (a, b) in enumerate(t["f3_rows"]):
        y = Y0 + i * DY
        o.append(txt(40, y + 2, a, 18, FG, weight="600"))
        o.append(txt(40, y + 25, b, 15, DIM))
    ly = yb + 62
    o.append(f'<circle cx="48" cy="{ly - 5}" r="8" fill="{KEK}"/>' + txt(66, ly, t["f3_leg"][0], 15, FG))
    o.append(f'<circle cx="378" cy="{ly - 5}" r="8" fill="{NAR}"/>' + txt(396, ly, t["f3_leg"][1], 15, FG))
    for i, s in enumerate(wrap(t["f3_foot"], 140)):
        o.append(txt(40, ly + 32 + i * 22, s, 14, DIM))
    o.append("</svg>")
    return "\n".join(o)


# ─────────────────────────────── 4 · a fej az ellenpróbák után
def fig4(sorok, L):
    t = T[L]
    W, H = 1200, 590
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', fej(W, t["f4_cim"], t["f4_al"])]
    X0, X1, Y0, DY = 400, 930, 176, 104
    sx = lambda v: X0 + (v - 0.5) / 0.5 * (X1 - X0)  # noqa: E731
    yb = Y0 + DY * 3 - 42
    for v in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        o.append(line(sx(v), Y0 - 44, sx(v), yb, GRID))
        o.append(txt(sx(v), yb + 20, szam(v, L, 1), 13, DIM, "middle"))
    o.append(txt(1168, Y0 - 44, t["f4_nyer"], 15, DIM, "end"))
    for i, r in enumerate(sorok):
        y = Y0 + i * DY
        cim, sub = t["f4_rows"][i]
        o.append(txt(40, y - 8, cim, 18, FG, weight="600"))
        for j, s in enumerate(sub):
            o.append(txt(40, y + 16 + j * 20, s, 15, DIM))
        o.append(line(sx(r["S"]), y, sx(r["RN"]), y, NAR, 3))
        tx = sx(r["szoveg"])
        o.append(f'<path d="M {tx:.1f} {y - 11} L {tx + 11:.1f} {y} L {tx:.1f} {y + 11} L {tx - 11:.1f} {y} z" fill="{BG}" stroke="{SEM}" stroke-width="2.4"/>')
        o.append(txt(tx, y - 19, szam(r["szoveg"], L), 16, FG, "middle", "600"))
        for v, c in ((r["S"], KEK), (r["RN"], NAR)):
            o.append(f'<circle cx="{sx(v):.1f}" cy="{y}" r="10" fill="{c}" stroke="{BG}" stroke-width="2"/>')
            o.append(txt(sx(v), y - 19, szam(v, L), 16, FG, "middle", "600"))
        o.append(txt(1168, y + 1, "+" + szam(r["delta"], L), 21, FG, "end", "700"))
        o.append(txt(1168, y + 24, f"[{szam(r['lo'], L)}; {szam(r['hi'], L)}]", 14, DIM, "end"))
    ly = yb + 56
    o.append(f'<path d="M 50 {ly - 16} L 60 {ly - 6} L 50 {ly + 4} L 40 {ly - 6} z" fill="{BG}" stroke="{SEM}" stroke-width="2.2"/>' + txt(70, ly, t["f4_leg"][0], 15, FG))
    o.append(f'<circle cx="348" cy="{ly - 6}" r="8" fill="{KEK}"/>' + txt(364, ly, t["f4_leg"][1], 15, FG))
    o.append(f'<circle cx="618" cy="{ly - 6}" r="8" fill="{NAR}"/>' + txt(634, ly, t["f4_leg"][2], 15, FG))
    for i, s in enumerate(t["f4_foot"]):
        o.append(txt(40, ly + 32 + i * 22, s, 14, DIM))
    o.append("</svg>")
    return "\n".join(o)


# ─────────────────────────────── linkelőnézet (og:image), 1200×630
LOGO = Path.home() / "projects/docai_web/public/images/docai_logo_white.png"
OG = {"hu": {"cim": ("Amit ki lehet számolni,", "azt ne tanítsd meg"), "al": "helyes válaszok aránya a számolást igénylő tételeken",
             "leg": ("lánc nélkül", "a számítást kód végzi"), "foot": "szintetikus teszt, előre rögzített mérés · docai.hu/blog"},
      "en": {"cim": ("What you can compute,", "don’t train"), "al": "share of correct answers on items that need a calculation",
             "leg": ("no chain", "code does the arithmetic"), "foot": "synthetic test, pre-registered measurement · docai.hu/en/blog"}}


def og(g5, L):
    import base64
    t, o2 = T[L], OG[L]
    W, H = 1200, 630
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    if LOGO.exists():
        b64 = base64.b64encode(LOGO.read_bytes()).decode()
        o.append(f'<image href="data:image/png;base64,{b64}" x="{W - 60 - 148}" y="46" width="148" height="42"/>')
    o.append(txt(60, 92, o2["cim"][0], 50, FG, weight="700"))
    o.append(txt(60, 152, o2["cim"][1], 50, FG, weight="700"))
    o.append(txt(60, 200, o2["al"], 24, DIM))
    X0, X1, Y0, DY = 430, 1110, 300, 92
    sx = lambda v: X0 + v * (X1 - X0)  # noqa: E731
    for i, f in enumerate((BA, HI, SZ)):
        y = Y0 + i * DY
        o.append(txt(60, y + 10, t["f3_rows"][i][0], 30, FG, weight="600"))
        p = g5["csaladok"][f]["pont"]
        o.append(line(sx(p["nelkul"]), y, sx(p["kinyert"]), y, DIM, 3))
        for v, c in ((p["nelkul"], KEK), (p["kinyert"], NAR)):
            o.append(f'<circle cx="{sx(v):.1f}" cy="{y}" r="15" fill="{c}" stroke="{BG}" stroke-width="3"/>')
            o.append(txt(sx(v), y - 25, pc(v, L), 26, FG, "middle", "700"))
    ly = H - 34
    o.append(f'<circle cx="70" cy="{ly - 7}" r="11" fill="{KEK}"/>' + txt(90, ly, o2["leg"][0], 22, FG))
    o.append(f'<circle cx="300" cy="{ly - 7}" r="11" fill="{NAR}"/>' + txt(320, ly, o2["leg"][1], 22, FG))
    o.append(txt(W - 60, ly, o2["foot"], 19, DIM, "end"))
    o.append("</svg>")
    return "\n".join(o)


def render(name, svg, scale=1.5625):
    p = HERE / f"{name}.svg"
    p.write_text(svg, encoding="utf-8")
    (HERE / "png").mkdir(exist_ok=True)
    w, h = (int(v) for v in re.search(r'width="(\d+)" height="(\d+)"', svg).groups())
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                    f"--force-device-scale-factor={scale}", f"--window-size={w},{h}",
                    f"--screenshot={HERE / 'png' / f'{name}.png'}", p.as_uri()],
                   check=True, capture_output=True, timeout=120)
    subprocess.run(["pngquant", "--force", "--quality=85-98", "--ext", ".png", str(HERE / "png" / f"{name}.png")], check=True)


def fej_sorok():
    """A 4. ábra három sora: a fej (L-RN), az alany (L-S), a legjobb csak szöveget látó modell, a páros különbség."""
    out = []
    forras = ((ER / "G5/k1/g5_k1.json", lambda: jl(ER / "G5_utolagos/felszin/felszin.json")[SZ]["pont"]["karakter"]),
              (ER / "M/k1/g5_k1.json", lambda: jl(ER / "M/felszin/illesztes.json")[SZ]["friss_karakter"]),
              (ER / "N/k1/g5_k1.json", lambda: jl(ER / "N/szoveg.json")["friss_szó"]))
    for p, sz in forras:
        d = jl(p)["csaladok"][SZ]
        par = d["parok"]["L-RN − L-S"]["K1a"]
        out.append({"RN": d["karok"]["L-RN"]["K1a"]["auroc"], "S": d["karok"]["L-S"]["K1a"]["auroc"], "szoveg": sz(),
                    "delta": par["delta"], "lo": par["ci95"][0], "hi": par["ci95"][1]})
    return out


def main():
    k2 = jl(ROOT / "kor07/eredmenyek/F5/elemzes.json")["k2"]
    g5, j = jl(ER / "G5/k2/g5_k2.json"), jl(ER / "J/k2/g5_k2.json")
    sorok = fej_sorok()
    for L, s in (("hu", "hu"), ("en", "en")):
        render(f"1_lanc_{s}", fig1(L))
        render(f"2_lezart_{s}", fig2(k2, L))
        render(f"3_csapda_{s}", fig3(g5, j, L))
        render(f"4_fej_{s}", fig4(sorok, L))
        render(f"og_{s}", og(g5, L), scale=1)
    print(json.dumps({"fej": sorok, "k2": {k: (round(k2["karok"][k]["hasznos_lef"], 4), [round(x, 4) for x in k2["karok"][k]["hasznos_lef_ci95"]])
                                           for k in ("B1-S", "B1-N", "B1-4S", "B1-R", "B1-4R")}}, ensure_ascii=False, indent=0))


if __name__ == "__main__":
    main()
