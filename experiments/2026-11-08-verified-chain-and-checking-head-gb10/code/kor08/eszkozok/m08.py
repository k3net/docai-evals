"""08 illesztett kontroll (M) — a rögzített eszközök az illesztett (a)-n, burkolóként (a rögzített fájlok nem változnak). A forrás `M1T`, a gyökér `kor08/adat/M`. A parancs első szava dönt.

  kinyer     `kinyer08`
  lanc0      `lanc08 futtat`, a rögzített lánc (ahogy a G3-ban)
  kiolvas    `kiolvas08`, a szelet `lM1T`
  b1rel      `b1rel08`
  egyesit    az (a') és a meglévő (b) egy `g5_k1_08`-bemenetbe, családonként (`cache/k08/m/egyesitett`); az eredeti (a) kimarad, a (b) azokból az egységekből, ahol van (a')
  k1         `g5_k1_08`
  rogzit     a manifest Dani jóváhagyására (felülírni nem lehet); ellenoriz: a rögzített fájlok változatlanok-e
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE)]
FORRAS = "M1T"
GY = "kor08/adat/M"
G3 = "kor08/adat/G3"
MANIFEST = EXP / "kor08/rogzites/M/manifest.json"
CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
FAJLOK = ("kor08/M-rogzites.md", "kor08/eredmenyek/M/felszin/illesztes.json", *(f"kor08/eszkozok/{f}" for f in ("illeszt08m.py", "szint08m.py", "felszin08m.py", "m08.py", "k08m.sh")),
          *(f"{GY}/items/{f}.jsonl" for f in CSALADOK))
PONT = "cache/k08/pecset/pontoz"
EGY = "cache/k08/m/egyesitett"


def bejegyez():
    import lanc08 as L
    L.FORRASOK[FORRAS] = (f"{GY}/terv", f"{GY}/items", None)
    return L


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def wl(p: Path, rows: list[dict]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def kiolvas() -> None:
    import kiolvas08 as K8
    KI = K8.KI
    KI.ITEMS[f"l{FORRAS}"] = EXP / GY / f"G3/kinyert_{FORRAS}/items"
    KI.SZELETEK[f"l{FORRAS}"] = (FORRAS,)
    KI.FORRASOK = (*KI.FORRASOK, f"l{FORRAS}")
    KI.main()


def egyesit() -> None:
    for fam in CSALADOK:
        am = jl(EXP / GY / f"items/{fam}.jsonl")
        eg = {i["meta"]["ertelmezes"]["egyseg"] for i in am}
        b = [i for i in jl(EXP / f"kor08/adat/G2/ert_teszt/items/{fam}.jsonl") if i["meta"]["ertelmezes"]["alt"] == "b" and i["meta"]["ertelmezes"]["egyseg"] in eg]
        bid = {i["id"] for i in b}
        wl(EXP / EGY / f"items/{fam}.jsonl", am + b)
        for ut in ("kinyert", "orakulum"):
            d0, d1 = EXP / G3 / f"{ut}_G2T", EXP / GY / f"G3/{ut}_{FORRAS}"
            wl(EXP / EGY / ut / f"lanc_{fam}.jsonl", jl(d1 / f"lanc_{fam}.jsonl") + [r for r in jl(d0 / f"lanc_{fam}.jsonl") if r["id"] in bid])
            wl(EXP / EGY / ut / "items" / f"{fam}.jsonl", jl(d1 / "items" / f"{fam}.jsonl") + [r for r in jl(d0 / "items" / f"{fam}.jsonl") if r["id"] in bid])
        p0 = json.loads((EXP / PONT / f"lG2T_{fam}_G2T.json").read_text())
        p1 = json.loads((EXP / f"cache/k08/m/pontoz/l{FORRAS}_{fam}_{FORRAS}.json").read_text())
        k0, k1 = p0["keret4"], p1["keret4"]
        if set(k0["pontszam"]) != set(k1["pontszam"]):
            raise SystemExit(f"{fam}: a karok eltérnek")
        tart = [n for n, i in enumerate(k0["ids"]) if i in bid]
        ids = k1["ids"] + [k0["ids"][n] for n in tart]
        p = {k: list(k1["pontszam"][k]) + [k0["pontszam"][k][n] for n in tart] for k in k0["pontszam"]}
        ki = {**p1, "keret4": {"ids": ids, "dontes": {**k1["dontes"], **{k0["ids"][n]: k0["dontes"][k0["ids"][n]] for n in tart}}, "pontszam": p}, "szelet": f"{FORRAS}+G2T(b)"}
        (EXP / EGY / f"pont_{fam}.json").write_text(json.dumps(ki) + "\n", encoding="utf-8")
        print(f"{fam}: (a') {len(k1['ids'])}, (b) {len(tart)} pontozott item")


def rogzit(jov: str) -> None:
    if MANIFEST.exists():
        raise SystemExit(f"az M már rögzítve: {MANIFEST.relative_to(EXP)} (felülírni nem lehet)")
    m = {"rogzitve": datetime.now().isoformat(timespec="seconds"), "jovahagyas": jov, "d12_sha256": sha(EXP / "kor08/rogzites/D12/manifest.json"), "fajlok": {f: sha(EXP / f) for f in FAJLOK}}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"→ {MANIFEST.relative_to(EXP)}: {len(FAJLOK)} fájl")


def ellenoriz() -> None:
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    elt = [f for f, h in m["fajlok"].items() if sha(EXP / f) != h]
    if elt:
        raise SystemExit("az M rögzítése óta változott: " + ", ".join(elt))
    print(f"rendben: {len(m['fajlok'])} rögzített M-fájl változatlan")


def main() -> None:
    cmd, rest = sys.argv[1], sys.argv[2:]
    sys.argv = [f"m08 {cmd}", *rest]
    if cmd == "kinyer":
        bejegyez()
        import kinyer08
        kinyer08.main()
    elif cmd == "lanc0":
        bejegyez().main()
    elif cmd == "kiolvas":
        kiolvas()
    elif cmd == "b1rel":
        bejegyez()
        import b1rel08
        b1rel08.main()
    elif cmd == "egyesit":
        egyesit()
    elif cmd == "k1":
        import g5_k1_08
        g5_k1_08.main()
    elif cmd == "rogzit":
        rogzit(rest[rest.index("--jovahagyas") + 1])
    elif cmd == "ellenoriz":
        ellenoriz()
    else:
        raise SystemExit(f"ismeretlen parancs: {cmd}")


if __name__ == "__main__":
    main()
