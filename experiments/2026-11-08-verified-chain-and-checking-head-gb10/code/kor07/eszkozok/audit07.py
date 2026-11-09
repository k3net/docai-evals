"""07-es kör — a friss CAL és TESZT címkeauditja (07-runbook 3.2; a 06 D14 módszere) a 06 eszközeinek burkolásával:
a mintát a `szint06.cmd_audit`, a vak lapot és az összesítést az `audit06` adja, 07-es útvonalakkal. A 06 kódja nem
változik.

  minta      — 300 item: családonként 100, állapot × nyelv szerint rétegezve (cellánként 12 vagy 13), a friss CAL és
               TESZT itemeiből (`kor07/adat/f2/items`), 07-es seeddel → `kor07/adat/f2/audit/{minta,kulcs}.jsonl`.
               A mintafájlban nincs gold és nincs állapot; az a kulcsfájlban van (az adjudikációhoz).
  html       — a vak lap: `kor07/adat/f2/audit/atnezo.html` (átlátszatlan kulcsok a001…, család, nyelv, szelet és
               item-id nélkül; eltérésnél második ítélet a konstrukció címkéjével és a terv tényeivel), a
               kulcsleképezés `atnezo_kulcsok.json`. Utána lefut a szivárgás-ellenőrzés.
  ellenoriz  — a lap szivárgás-ellenőrzése: item-id (`k07-nnnn`), sablon-id (`:k07:`), családnév, szeletnév és „(z)”
               nem fordulhat elő a lapon; a kulcsok száma és sorrendje egyezik a mintával.
  osszesit   — Dani exportja (`dontesek.json`) a kulccsal szemben (`audit06.cmd_osszesit`): egyezés családonként és
               állapotonként, a hibák, a kapu (egyoldali 95%-os Clopper–Pearson felső korlát ≤ 2%; 300 itemen
               legfeljebb 1 hiba) → `kor07/eredmenyek/F2/audit/osszesito.{json,md}`.

  python3 kor07/eszkozok/audit07.py minta
  python3 kor07/eszkozok/audit07.py html
  python3 kor07/eszkozok/audit07.py osszesit --dontesek kor07/adat/f2/audit/dontesek.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "kor06/eszkozok"), str(EXP / "eszkozok")]
import audit06 as A  # noqa: E402
import szint06 as S  # noqa: E402

F2 = EXP / "kor07/adat/f2"
CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
SEED07 = "szint07:2026-11-01"

# a 06 eszközei 07-es útvonalakon
S.D = F2
S.SEED = SEED07
S.path = lambda kind, fam, *_: F2 / kind / f"{fam}.jsonl"  # type: ignore[assignment]
A.D = F2
A.OUT = EXP / "kor07/eredmenyek/F2/audit"
A.HTML = A.HTML.replace("<title>Címkeaudit 06</title>", "<title>Címkeaudit 07</title>").replace(
    '"ldh-audit06-"', '"ldh-audit07-"')


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def raw_kulcs_ellenorzes() -> None:
    """Az `audit06.cmd_html` a terv tényeit a raw rekord `group_id`-jén át az item-id-vel keresi: a 07 raw-jának is így
    kell lennie, különben a lap nem épül meg."""
    for fam in CSALADOK:
        ids = {it["id"] for it in jl(F2 / f"items/{fam}.jsonl")}
        gid = {r["group_id"] for r in jl(F2 / f"raw/{fam}.jsonl")}
        hiany = ids - gid
        if hiany:
            raise SystemExit(f"{fam}: {len(hiany)} item id-je nincs a raw group_id-k között (pl. {sorted(hiany)[:2]})")


def cmd_minta(a) -> None:
    raw_kulcs_ellenorzes()
    S.audit_dir(a.kor).mkdir(parents=True, exist_ok=True)
    a.csalad = None
    S.cmd_audit(a)
    minta, kulcs = jl(S.audit_dir(a.kor) / "minta.jsonl"), jl(S.audit_dir(a.kor) / "kulcs.jsonl")
    c = Counter((m["family"].split(".")[1], k["split"], m["lang"], k["content_state"]) for m, k in zip(minta, kulcs))
    print(f"minta: {len(minta)} item; szelet: {dict(Counter(k['split'] for k in kulcs))}; "
          f"nyelv: {dict(Counter(m['lang'] for m in minta))}")
    for fam in CSALADOK:
        f = fam.split(".")[1]
        print(f"  {fam}: " + ", ".join(f"{sz}/{lang}/{st} {n}" for (ff, sz, lang, st), n in sorted(c.items()) if ff == f))


def cmd_html(a) -> None:
    raw_kulcs_ellenorzes()
    A.cmd_html(a)
    cmd_ellenoriz(a)


def cmd_ellenoriz(a) -> None:
    A_dir = S.audit_dir(a.kor)
    lap = (A_dir / "atnezo.html").read_text(encoding="utf-8")
    km = json.loads((A_dir / "atnezo_kulcsok.json").read_text(encoding="utf-8"))
    minta = jl(A_dir / "minta.jsonl")
    hibak = []
    for nev, rx in (("item-id", r"k07-\d{4}"), ("sablon-id", r":k07:"), ("szelet", r"\b(CAL|TESZT|T500)\b"),
                    ("„(z)”", r"\(z\)")):
        n = len(re.findall(rx, lap))
        if n:
            hibak.append(f"{nev}: {n} előfordulás")
    for fam in CSALADOK:
        if fam in lap:
            hibak.append(f"családnév a lapon: {fam}")
    if list(km["kulcsok"].values()) != [m["id"] for m in minta]:
        hibak.append("a kulcsleképezés nem a minta sorrendje")
    if len(km["kulcsok"]) != len(minta):
        hibak.append(f"kulcsok {len(km['kulcsok'])} ≠ minta {len(minta)}")
    if hibak:
        raise SystemExit("szivárgás-ellenőrzés: " + "; ".join(hibak))
    print(f"szivárgás-ellenőrzés: rendben ({len(minta)} item, sig {km['sig']}; item-id, sablon-id, szelet, családnév "
          f"és „(z)” nincs a lapon)")


def cmd_osszesit(a) -> None:
    A.cmd_osszesit(a)
    md = (A.OUT if a.kor == 1 else A.OUT / f"kor{a.kor}") / "osszesito.md"
    if md.exists():
        md.write_text(md.read_text(encoding="utf-8").replace("# 06 F2 — címkeaudit (D14)", "# 07 F2 — címkeaudit a friss CAL + TESZT-en (06 D14)"),
                      encoding="utf-8")

def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("minta", "html", "ellenoriz"):
        sub.add_parser(c).add_argument("--kor", type=int, default=1)
    o = sub.add_parser("osszesit")
    o.add_argument("--kor", type=int, default=1)
    o.add_argument("--dontesek", required=True)
    o.add_argument("--elozo", help="az 1. kör döntései a 2. körben nem szereplő családokra")
    a = ap.parse_args()
    {"minta": cmd_minta, "html": cmd_html, "ellenoriz": cmd_ellenoriz, "osszesit": cmd_osszesit}[a.cmd](a)



if __name__ == "__main__":
    main()
