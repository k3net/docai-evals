"""F0.4 — a korpusz prozódiai annotálása (determinisztikus, LLM nélkül).

Minden strófához: soronkénti szótagszám, sorvégi rímkulcs, rímséma. Minden
vershez: domináns séma, izometria (azonos hosszúságúak-e a sorok), forma-címke.

Ez az annotáció az F1 SFT-adatépítés bemenete: ebből lesz a
„Írj 3 strófás, AABB rímsémájú, 8 szótagos sorokból álló verset…” instrukció.
Vagyis a tanítópár **utasítás-oldala is mérésből származik**, nem kézi
címkézésből — így az F4-ben ugyanazzal az eszközzel ellenőrizhető, hogy a
modell betartotta-e.

    python3 src/annotate_corpus.py
"""

from __future__ import annotations

import json
import statistics as st
import sys
from collections import Counter

from pathlib import Path

from config import CORPUS, REPORTS, SOURCES

# A prozódiai mérőeszköz a repó közös scripts/ mappájában lakik — egyetlen
# példány, önálló self-testtel (`python3 scripts/hu_prosody.py`). Ugyanez a
# modul annotálja a korpuszt és értékeli a generálásokat.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from hu_prosody import count_syllables, has_digits, rhyme_parts, rhyme_scheme  # noqa: E402

# Izometria: a strófa sorai akkor „azonos hosszúságúak”, ha a szótagszámok
# szórása ez alatt van. A magyar strófák jellemzően vagy szigorúan izometrikusak
# (Toldi: 12-12-12-12), vagy szabályosan váltakozók (8-7-8-7) — a kettőt szét
# kell tudni választani.
ISOMETRIC_STD = 0.5


def rhyme_key_str(line: str) -> str:
    """A sorvég rímkulcsa emberi olvasatra: az utolsó két szótag fonémasora."""
    _, _, tail = rhyme_parts(line)
    return "".join(tail)


def annotate_poem(poem: dict) -> dict:
    stanza_meta = []
    for stanza in poem["stanzas"]:
        syllables = [count_syllables(ln) for ln in stanza]
        reliable = not any(has_digits(ln) for ln in stanza)
        stanza_meta.append(
            {
                "n_lines": len(stanza),
                "syllables": syllables,
                "syllables_reliable": reliable,
                "rhyme_keys": [rhyme_key_str(ln) for ln in stanza],
                "scheme": rhyme_scheme(stanza),
            }
        )

    schemes = Counter(m["scheme"] for m in stanza_meta if m["n_lines"] >= 2)
    sizes = Counter(m["n_lines"] for m in stanza_meta)
    all_syll = [s for m in stanza_meta if m["syllables_reliable"] for s in m["syllables"]]

    # Izometria strófánként, majd a versre összesítve.
    iso_flags = [
        st.pstdev(m["syllables"]) <= ISOMETRIC_STD
        for m in stanza_meta
        if m["syllables_reliable"] and m["n_lines"] >= 2
    ]

    poem["prosody"] = {
        "stanzas": stanza_meta,
        "dominant_scheme": schemes.most_common(1)[0][0] if schemes else None,
        "dominant_scheme_share": (
            round(schemes.most_common(1)[0][1] / sum(schemes.values()), 3) if schemes else None
        ),
        "dominant_stanza_size": sizes.most_common(1)[0][0] if sizes else None,
        "regular_stanza_size": (
            round(sizes.most_common(1)[0][1] / sum(sizes.values()), 3) if sizes else None
        ),
        "syllables_mean": round(st.mean(all_syll), 2) if all_syll else None,
        "syllables_mode": Counter(all_syll).most_common(1)[0][0] if all_syll else None,
        "isometric_share": round(sum(iso_flags) / len(iso_flags), 3) if iso_flags else None,
    }
    return poem


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    summary: dict[str, dict] = {}

    for key in SOURCES:
        paths = sorted((CORPUS / key).glob("*.json"))
        if not paths:
            print(f"[{key}] nincs korpusz — futtasd előbb a build_corpus.py-t")
            return 1

        schemes = Counter()
        sizes = Counter()
        syll_modes = Counter()
        iso_shares: list[float] = []
        n_poems = 0
        for path in paths:
            poem = json.loads(path.read_text(encoding="utf-8"))
            poem = annotate_poem(poem)
            path.write_text(json.dumps(poem, ensure_ascii=False, indent=1), encoding="utf-8")
            if poem["kind"] != "poem":
                continue
            n_poems += 1
            pr = poem["prosody"]
            if pr["dominant_scheme"]:
                schemes[pr["dominant_scheme"]] += 1
            if pr["dominant_stanza_size"]:
                sizes[pr["dominant_stanza_size"]] += 1
            if pr["syllables_mode"]:
                syll_modes[pr["syllables_mode"]] += 1
            if pr["isometric_share"] is not None:
                iso_shares.append(pr["isometric_share"])

        summary[key] = {
            "author": SOURCES[key]["author"],
            "poems": n_poems,
            "top_schemes": schemes.most_common(5),
            "top_stanza_sizes": sizes.most_common(4),
            "top_syllable_modes": syll_modes.most_common(4),
            "isometric_mean": round(st.mean(iso_shares), 3) if iso_shares else None,
        }
        s = summary[key]
        print(f"[{key}] {n_poems} vers annotálva · séma {s['top_schemes'][:3]} · "
              f"strófaméret {s['top_stanza_sizes'][:2]} · izometria {s['isometric_mean']:.0%}")

    rows = ["# F0.4 — Prozódiai annotáció\n",
            "Vers-szintű összesítés (`data/corpus/*/*.json` → `prosody` mező).\n",
            "| szerző | vers | leggyakoribb rímséma | jellemző strófaméret | jellemző szótagszám | izometrikus strófa |",
            "|---|---:|---|---|---|---:|"]
    for key, s in summary.items():
        rows.append(
            f"| {s['author']} | {s['poems']} | "
            + ", ".join(f"`{k}` {v}" for k, v in s["top_schemes"][:3])
            + " | "
            + ", ".join(f"{k} soros ({v})" for k, v in s["top_stanza_sizes"][:2])
            + " | "
            + ", ".join(f"{k} ({v})" for k, v in s["top_syllable_modes"][:2])
            + f" | {s['isometric_mean']:.0%} |"
        )
    rows.append(
        "\nAz **izometrikus strófa** aránya azt méri, hány strófában azonos "
        f"hosszúságúak a sorok (szótagszám-szórás ≤ {ISOMETRIC_STD}). A maradék "
        "nem hiba: a magyar strófa gyakran szabályosan váltakozó (8-7-8-7).\n"
    )
    (REPORTS / "03_annotacio.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    (CORPUS / "prosody_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nRiport: {REPORTS / '03_annotacio.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
