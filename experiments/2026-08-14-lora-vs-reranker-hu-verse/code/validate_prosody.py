"""F0.3 — a prozódiai mérőeszköz validálása, mielőtt bármit mérnénk vele.

Egy mérőeszközt nem elég megírni: meg kell mutatni, hogy mér. Két, egymástól
független ellenőrzés fut itt.

**(A) Szótagszámláló — külső igazsághoz mérve.** A Toldi, a Toldi estéje és a
János vitéz **felező tizenkettesben** íródott: minden sor 12 szótag. Ez
irodalomtörténeti tény, nem a mi feltevésünk, tehát alkalmas külső
igazságforrásnak. Ha a számláló helyes, ezekben a művekben a sorok döntő
többsége pontosan 12 szótagos. Kontrollként ott a Rege a csodaszarvasról
(nyolcas) és a korpusz egésze.

**(B) Rímdetektor — kontrollcsoporthoz mérve.** A valódi strófák sorpárjait
összevetjük **összekevert** kontroll-párokkal (különböző versekből, azonos
pozícióból vett sorok). Ha a detektor működik, a valódi strófákban lényegesen
gyakoribb a küszöb feletti pontszám. A küszöböt nem hasból lőjük be: az
elválasztás onnan jön, hol a legnagyobb a valódi és a véletlen közti rés.

Kimenet: `reports/02_prozodia.md`.

    python3 code/validate_prosody.py
"""

from __future__ import annotations

import json
import random
import statistics as st
import sys
from collections import Counter

from pathlib import Path

from config import CORPUS, REPORTS, RHYME_THRESHOLD, SOURCES, STRICT_RHYME_THRESHOLD

# A mérőeszköz a repó közös scripts/ mappájában lakik — ld. annotate_corpus.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from hu_prosody import count_syllables, has_digits, rhyme_score, rhyme_scheme  # noqa: E402

SEED = 20260814
# Külső igazságforrás: cím-minta → elvárt szótagszám.
METRIC_TRUTH = [
    ("felező tizenkettes", 12, ["TOLDI:", "TOLDI ESTÉJE:", "JÁNOS VITÉZ"]),
    ("ősi nyolcas", 8, ["REGE A CSODASZARVASRÓL"]),
]


def load_poems() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for key in SOURCES:
        poems = []
        for path in sorted((CORPUS / key).glob("*.json")):
            poem = json.loads(path.read_text(encoding="utf-8"))
            if poem.get("kind") == "poem":
                poems.append(poem)
        out[key] = poems
    return out


# ------------------------------------------------------------------ (A)

def validate_syllables(poems: dict[str, list[dict]]) -> list[str]:
    rows = ["## A — Szótagszámláló külső igazsághoz mérve\n",
            "| mű | elvárt | sor | pontos találat | ±1 szótagon belül | medián |",
            "|---|---:|---:|---:|---:|---:|"]
    all_poems = [p for ps in poems.values() for p in ps]

    for label, expected, patterns in METRIC_TRUTH:
        lines = [
            ln
            for p in all_poems
            if any(p["display_title"].upper().startswith(pat) for pat in patterns)
            for st_ in p["stanzas"]
            for ln in st_
            if not has_digits(ln)
        ]
        if not lines:
            continue
        counts = [count_syllables(ln) for ln in lines]
        exact = sum(1 for c in counts if c == expected)
        near = sum(1 for c in counts if abs(c - expected) <= 1)
        rows.append(
            f"| {label} ({', '.join(patterns)}) | {expected} | {len(lines):,} | "
            f"{exact / len(counts):.1%} | {near / len(counts):.1%} | {st.median(counts):.0f} |"
        )

    every = [
        count_syllables(ln)
        for p in all_poems
        for st_ in p["stanzas"]
        for ln in st_
        if not has_digits(ln)
    ]
    dist = Counter(every)
    top = ", ".join(f"{v}: {n / len(every):.1%}" for v, n in dist.most_common(6))
    rows.append(
        f"\n**A teljes korpusz szótagszám-eloszlása** ({len(every):,} sor): {top}. "
        f"Medián {st.median(every):.0f}, átlag {st.mean(every):.1f}.\n"
    )
    return rows


# ------------------------------------------------------------------ (B)

def rhyme_scorer_ablation(quatrains: dict[str, list[list[str]]], rng: random.Random) -> list[str]:
    """B/a — a pontozó tervezési döntése mérésből, nem ízlésből.

    Három változatot vetünk össze ugyanazon az adaton. A „valódi” oszlop
    szerzőnként a DOMINÁNS rímpozíciókat nézi (Aranynál 1–2 és 3–4 = páros rím,
    Petőfinél 2–4 = félrím), tehát olyan sorpárokat, amelyekről tudjuk, hogy
    rímelniük kell; a kontroll ugyanezekből a sorokból, de eltérő strófákból
    párosít.
    """
    from hu_prosody import _coda_class, _last_word, rhyme_parts

    def parts(a: str, b: str):
        va, ca, _ = rhyme_parts(a)
        vb, cb, _ = rhyme_parts(b)
        return (va, ca, vb, cb) if va and vb else None

    def v1(a: str, b: str) -> float:
        """Additív, a coda opcionális — ez a `hu_prosody.rhyme_score`."""
        return rhyme_score(a, b)

    def v2(a: str, b: str) -> float:
        """A coda egyezése KÖTELEZŐ (legalább osztály-szinten)."""
        p = parts(a, b)
        if not p:
            return 0.0
        _, ca, _, cb = p
        ok = ca == cb or (len(ca) == len(cb) and _coda_class(ca) == _coda_class(cb))
        return min(rhyme_score(a, b), 0.5) if not ok else rhyme_score(a, b)

    def v3(a: str, b: str) -> float:
        """Csak a magánhangzók számítanak (tiszta asszonánc)."""
        p = parts(a, b)
        if not p:
            return 0.0
        va, _, vb, _ = p
        s = 0.6 if va[-1] == vb[-1] else 0.0
        if len(va) > 1 and len(vb) > 1 and va[-2] == vb[-2]:
            s += 0.4
        return min(s, 0.5) if _last_word(a) == _last_word(b) else s

    true_pairs = {"arany": [(0, 1), (2, 3)], "petofi": [(1, 3)]}
    all_pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    all_stanzas = [s for ss in quatrains.values() for s in ss]
    ctrl_sample = [
        (rng.choice(all_stanzas), rng.choice(all_stanzas), rng.choice(all_pairs))
        for _ in range(6000)
    ]

    rows = ["### B/a — A pontozó változatai (abláció)\n",
            "| pontozó | küszöb | Arany (1–2, 3–4) | Petőfi (2–4) | kontroll | **rés** |",
            "|---|---:|---:|---:|---:|---:|"]
    for name, fn in (("**v1** additív, coda opcionális *(ez fut)*", v1),
                     ("v2 — coda kötelező", v2),
                     ("v3 — csak magánhangzó", v3)):
        for t in (0.6, 0.8):
            rates = {
                k: st.mean([float(fn(s[i], s[j]) >= t) for s in ss for i, j in true_pairs[k]])
                for k, ss in quatrains.items() if ss
            }
            ctrl = st.mean([float(fn(a[i], b[j]) >= t) for a, b, (i, j) in ctrl_sample])
            gap = st.mean(list(rates.values())) - ctrl
            rows.append(
                f"| {name} | {t:.1f} | {rates.get('arany', 0):.1%} | "
                f"{rates.get('petofi', 0):.1%} | {ctrl:.1%} | **{gap:+.1%}** |"
            )
    rows.append(
        "\nA v1 adja a legnagyobb rést 0,6-nál, ezért ez fut. Ára megnevezhető: "
        "a coda-egyezés hiányát két magánhangzó-egyezés kiválthatja, így az "
        "„isten / kell” párt rímnek látja (0,6). A v2 ezt kiszűrné, de vele "
        "esne Petőfi valódi „svábság / adósságát” ríme is — a mérés szerint "
        "többet veszítenénk, mint nyernénk.\n"
    )
    return rows


def validate_rhyme(poems: dict[str, list[dict]]) -> list[str]:
    rng = random.Random(SEED)
    quatrains: dict[str, list[list[str]]] = {}
    for key, ps in poems.items():
        quatrains[key] = [
            s for p in ps for s in p["stanzas"]
            if len(s) == 4 and not any(has_digits(ln) for ln in s)
        ]

    rows = ["## B — Rímdetektor kontrollcsoporthoz mérve\n"]
    rows += rhyme_scorer_ablation(quatrains, rng)

    # --- pozíciópár-rímarányok: melyik sorpár rímel valójában?
    rows.append("### B/b — Melyik sorpár rímel a négysoros strófákban?\n")
    rows.append("| szerző | négysoros strófa | 1–2 | 1–3 | 1–4 | 2–3 | 2–4 | 3–4 | **kontroll** |")
    rows.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    threshold = RHYME_THRESHOLD
    control_rates: dict[str, float] = {}
    for key, stanzas in quatrains.items():
        if not stanzas:
            continue
        rates = []
        for i, j in pairs:
            hits = sum(1 for s in stanzas if rhyme_score(s[i], s[j]) >= threshold)
            rates.append(hits / len(stanzas))
        # Kontroll: azonos pozíciókból, de KÜLÖNBÖZŐ strófákból vett sorpárok.
        # Ugyanaz a szerző, ugyanaz a szókincs — csak a rímszándék hiányzik.
        ctrl_hits = 0
        n_ctrl = min(4000, len(stanzas) * 4)
        for _ in range(n_ctrl):
            s1, s2 = rng.choice(stanzas), rng.choice(stanzas)
            i, j = rng.choice(pairs)
            ctrl_hits += rhyme_score(s1[i], s2[j]) >= threshold
        ctrl = ctrl_hits / n_ctrl
        control_rates[key] = ctrl
        rows.append(
            f"| {SOURCES[key]['author']} | {len(stanzas):,} | "
            + " | ".join(f"{r:.1%}" for r in rates)
            + f" | {ctrl:.1%} |"
        )
    rows.append(
        "\nA **kontroll** oszlop ugyanazokból a sorokból, de eltérő strófákból "
        "párosít — a szókincs és a szerző azonos, csak a rímszándék hiányzik. "
        "A valódi rímpozíciók és a kontroll közti rés a detektor jele.\n"
    )

    # --- küszöb-érzékenység
    rows.append("### B/c — Küszöbválasztás\n")
    rows.append("| küszöb | valódi rímpozíció (2–4 és 3–4) | kontroll | rés |")
    rows.append("|---:|---:|---:|---:|")
    all_stanzas = [s for ss in quatrains.values() for s in ss]
    ctrl_pairs = [
        (rng.choice(all_stanzas), rng.choice(all_stanzas), rng.choice(pairs))
        for _ in range(6000)
    ]
    for t in (0.4, 0.6, 0.8, 1.0):
        real = st.mean(
            [
                float(rhyme_score(s[1], s[3]) >= t or rhyme_score(s[2], s[3]) >= t)
                for s in all_stanzas
            ]
        )
        ctrl = st.mean([float(rhyme_score(a[i], b[j]) >= t) for a, b, (i, j) in ctrl_pairs])
        rows.append(f"| {t:.1f} | {real:.1%} | {ctrl:.1%} | **{real - ctrl:+.1%}** |")
    rows.append("")

    # --- rímséma-eloszlás
    rows.append("### B/d — Rímséma-eloszlás a négysoros strófákban\n")
    known = ("AABB", "ABAB", "ABCB", "AABA", "ABCD", "AAAA")
    rows.append("| szerző | küszöb | " + " | ".join(f"`{s}`" for s in known) + " | egyéb |")
    rows.append("|---|---:|" + "---:|" * 7)
    for key, stanzas in quatrains.items():
        if not stanzas:
            continue
        for t, label in ((RHYME_THRESHOLD, "asszonánc"), (STRICT_RHYME_THRESHOLD, "tiszta rím")):
            schemes = Counter(rhyme_scheme(s, t) for s in stanzas)
            total = sum(schemes.values())
            cells = [f"{schemes.get(s, 0) / total:.1%}" for s in known]
            other = 1 - sum(schemes.get(s, 0) for s in known) / total
            rows.append(f"| {SOURCES[key]['author']} | {t:.1f} ({label}) | " + " | ".join(cells) + f" | {other:.1%} |")
    rows.append(
        "\n`ABCB` = félrím (csak a páros sorok rímelnek) — a magyar népies vers "
        "alapformája, nem detektálási hiba. `ABCD` = a detektor egyetlen rímet "
        "sem talált: ide gyűlik a hibák nagy része, ezért ezt nézzük kézzel.\n"
    )
    return rows


def sample_for_manual_review(poems: dict[str, list[dict]], n: int = 20) -> list[str]:
    """F0-gate: kézi ellenőrzésre kiírt véletlen minta, rögzített seeddel."""
    rng = random.Random(SEED)
    all_poems = [p for ps in poems.values() for p in ps if 8 <= p["n_lines"] <= 40]
    picked = rng.sample(all_poems, min(n, len(all_poems)))
    rows = ["## C — Kézi ellenőrzésre kiválasztott minta (F0-gate)\n",
            f"Rögzített seed ({SEED}), {len(picked)} vers. A teljes szöveg: "
            "`reports/02_prozodia_minta.md`.\n"]
    lines = ["# F0-gate — kézi ellenőrzés mintája\n"]
    for poem in picked:
        lines.append(f"\n## {poem['display_title']} — {poem['author']}")
        lines.append(f"`{poem['poem_id']}` · {poem['n_stanzas']} strófa · {poem['n_lines']} sor\n")
        for stanza in poem["stanzas"]:
            scheme = rhyme_scheme(stanza)
            syl = "-".join(str(count_syllables(ln)) for ln in stanza)
            lines.append(f"*{scheme} · {syl}*\n")
            for ln in stanza:
                lines.append(f"> {ln}")
            lines.append("")
    (REPORTS / "02_prozodia_minta.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    poems = load_poems()
    total = sum(len(v) for v in poems.values())
    print(f"Betöltve: {total} vers")

    out = ["# F0.3 — A prozódiai mérőeszköz validálása\n",
           "A modul: `src/hu_prosody.py`. Egyetlen modellhívás sincs benne — "
           "ugyanez a kód annotálja a korpuszt és értékeli az F4 generálásait.\n"]
    out += validate_syllables(poems)
    out += validate_rhyme(poems)
    out += sample_for_manual_review(poems)

    (REPORTS / "02_prozodia.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Riport: {REPORTS / '02_prozodia.md'}")
    print("\n".join(ln for ln in out if ln.startswith("|") or ln.startswith("**")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
