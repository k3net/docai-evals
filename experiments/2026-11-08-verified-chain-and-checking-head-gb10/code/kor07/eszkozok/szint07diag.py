"""07-es kör — a végső diagnosztikai minta (07-runbook 3.3, D6, D11; K3): a 3. kör rögzített konstrukciója a 07 friss
TESZT-sablonjain, egyszer. A `szint07k3` burkolója: a terv, a generátor-utasítás és a tényellenőrzés az övé, itt csak a
sablonforrás, a változatok kiosztása, a darabszám és a kimenet más.

Dani döntései (2026-11-01 19:3x, „igen, mehet így tovább”, `kor07/nehez3-javaslat.md`, „Döntések a végső mintához”):
  - változatok: bank részfizetés; hiba mértékegység-váltás (minden egységpár); szabály nettó / bruttó és deviza
    (fele-fele); a betűvel írt összeg nincs benne (a próbán 2% rossz opció)
  - családonként 200 terv (D6), nyelvenként 100, a 07 TESZT-sablonjain (nyelvenként 30; a fejek ezeken nem tanultak)
A kiosztás előre rögzített: nyelvenként a sablonok id-sorrendjében körbe, a j-edik körben `seq = j`, amíg 100 terv
nincs; a szabálycsaládon a változat a nyelv soron következő tervének sorszáma szerint váltakozik (páros: nettó /
bruttó, páratlan: deviza). Ahol a sablonon az adott körben nincs alkalmas terv (nincs egységpár, egyértelmű
részfizetés vagy küszöb két oldalára eső összeg), az kimarad, a kör megy tovább; a kimaradások oka közölve. A
tényellenőrzőn elveszett itemek helyett nem készül új (D11: a minta egyszer készül, a tényleges szám közölve).

Kimenet: kor07/adat/diag/{terv,raw,items}/<család>.jsonl; split = DIAG; az item-id `<család>:DIAG:<nyelv>:MATCH:<n>`.
  onteszt | terv --csalad F | gen --csalad F --url U --model M [--extra J] [--workers N] | final --csalad F
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import szint07k3 as K3  # noqa: E402

S, S7 = K3.S, K3.S7
EXP = K3.EXP
D = EXP / "kor07/adat/diag"
SZELET = "DIAG"
PER_NYELV = 100
MAX_KOR = 12
VALTOZAT = {"penzugy.bankparositas": ("B3a-reszfizetes",), "muszaki.hibaelharitas": ("H3-valtas",),
            "szabaly.koltsegelszamolas": ("S3a-netto", "S3b-deviza")}
ALLAS = {"v": ""}  # a soron következő terv változata; a `szint07k3.valtozat` helyett ezt olvassa a `plan3`


def path_diag(kind: str, fam: str, _proba: bool = False) -> Path:
    return D / kind / f"{fam}.jsonl"


def sablonok_teszt(fam: str) -> list[dict]:
    """A 07 friss TESZT-sablonjai (a `szint07.sablonok` 06 T500-a helyett)."""
    return [s for s in S.jl_read(S7.F2 / "sablon" / f"{fam}.jsonl") if s["szelet"] == "TESZT"]


def telepit() -> None:
    S7.KOR["n"] = 3
    S7.SZELET = SZELET
    S7.sablonok = sablonok_teszt
    S7.plan_nehez = K3.plan3
    K3.valtozat = lambda _fam, _seq: ALLAS["v"]
    S.path = path_diag
    S.gen_prompt, S.fact_check = K3.gen_prompt3, K3.fact_check3


def probal(fam: str, sab: dict, seq: int, v: str) -> tuple[dict | None, str | None]:
    """Egy terv a megadott változattal; ha a sablonon nincs alkalmas, (None, ok)."""
    ALLAS["v"] = v
    try:
        p = K3.plan3(fam, sab, seq)
    except (SystemExit, IndexError, StopIteration) as e:
        return None, f"{v}: {type(e).__name__}: {str(e).split(':')[-1].strip()[:60] or 'nincs alkalmas'}"
    if p.get("kimarad"):
        return None, f"{v}: nincs alkalmas egységpár"
    return p, None


def cmd_terv(a) -> None:
    fam = a.csalad
    rows, kimarad = [], Counter()
    for lang in S.LANGS:
        sabs = sorted((s for s in sablonok_teszt(fam) if s["lang"] == lang), key=lambda s: s["sablon_id"])
        n = 0
        for j in range(MAX_KOR):
            for sab in sabs:
                if n == PER_NYELV:
                    break
                v = VALTOZAT[fam][n % len(VALTOZAT[fam])]
                p, ok = probal(fam, sab, j, v)
                if p is None:
                    kimarad[f"{lang} · {ok}"] += 1
                    continue
                gid = f"{fam}:{SZELET}:{lang}:MATCH:{n:04d}"
                rows.append(p | {"group_id": gid, "sorrend": S.h(f"{S.SEED}:diag:{gid}") % 10**12, "kor_j": j})
                n += 1
        if n < PER_NYELV:
            raise SystemExit(f"{fam}/{lang}: {MAX_KOR} kör után is csak {n} terv")
    S.jl_write(path_diag("terv", fam), rows)
    print(f"{fam}: {len(rows)} diagnosztikai terv; "
          + ", ".join(f"{k}={x}" for k, x in sorted(Counter((r["lang"], r["nehez"]["valt"]) for r in rows).items()))
          + f"; sablon {len({r['sablon_id'] for r in rows})}; körök {dict(Counter(r['kor_j'] for r in rows))}")
    for k, x in sorted(kimarad.items()):
        print(f"  kimaradt: {k}: {x}")


def cmd_onteszt(_a) -> None:
    """A `szint07k3.cmd_onteszt` a TESZT-sablonokon, a végső minta változataival."""
    hibak = 0
    for fam in S7.CSALADOK:
        for lang in S.LANGS:
            sabs = sorted((s for s in sablonok_teszt(fam) if s["lang"] == lang), key=lambda s: s["sablon_id"])
            for v in VALTOZAT[fam]:
                p = next(q for q in (probal(fam, s, 0, v)[0] for s in sabs) if q is not None)
                for nev, szoveg, varhato in K3.onteszt_szovegek(p):
                    kap = K3.fact_check3(p, szoveg)
                    ok = (kap is None) if varhato is None else (kap is not None and varhato in kap)
                    hibak += not ok
                    print(f"{'OK ' if ok else 'HIBA'} {v:16} {lang} {nev:22} várt: {varhato} · kapott: {kap}")
    raise SystemExit(1 if hibak else 0)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("onteszt")
    t = sub.add_parser("terv")
    g = sub.add_parser("gen")
    g.add_argument("--url", required=True)
    g.add_argument("--model", required=True)
    g.add_argument("--extra", default="")
    g.add_argument("--workers", type=int, default=32)
    f = sub.add_parser("final")
    for sp in (t, g, f):
        sp.add_argument("--csalad", required=True, choices=S7.CSALADOK)
    a = ap.parse_args()
    telepit()
    a.proba = True  # a szint06 `final`-ja: minden túlélő marad, cellakvóta nélkül
    {"onteszt": cmd_onteszt, "terv": cmd_terv, "gen": S.cmd_gen, "final": S.cmd_final}[a.cmd](a)


if __name__ == "__main__":
    main()
