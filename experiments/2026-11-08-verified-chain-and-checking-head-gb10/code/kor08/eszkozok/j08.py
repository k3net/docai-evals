"""08 javító kör (J) — a rögzített eszközök a friss K3-típusú mintán, burkolóként (a rögzített fájlok nem változnak). A forrás
neve `J1K3`, a gyökér `kor08/adat/J` (`--gyoker`, a próbához). A parancs első szava dönt, a többi argumentum a burkolt eszközé.

  kinyer            `kinyer08`
  lanc              `lanc08 futtat` a javított ellenőrzéssel (`lanc08j`)
  lanc0             `lanc08 futtat` a rögzített ellenőrzéssel (az összevetés útja)
  kiolvas           `kiolvas08` a J szeleteivel: nJ1K3 (lánc nélkül), lJ1K3 (javított), rJ1K3 (rögzített), oJ1K3 (orákulum)
  b1rel             `b1rel08`
  k2                `g5_k2_08`
  minta             a minta diszjunktsága: 0 közös sablon, 0 azonos szöveg a G2-vel
  rogzit            a J-rögzítés manifestje Dani jóváhagyására (felülírni nem lehet)
  ellenoriz         a rögzített J-fájlok változatlanok-e
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
FORRAS = "J1K3"
MANIFEST = EXP / "kor08/rogzites/J/manifest.json"
FAJLOK = ("kor08/J-rogzites.md", *(f"kor08/eszkozok/{f}" for f in ("lanc08j.py", "szint08j.py", "j08.py", "k08j.sh")))
CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")


def bejegyez(gy: str):
    import lanc08 as L
    L.FORRASOK[FORRAS] = (f"{gy}/k3/terv", f"{gy}/k3/items", None)
    return L


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def kiolvas(gy: str) -> None:
    import kiolvas08 as K8
    KI = K8.KI
    for nev, d in ((f"n{FORRAS}", f"{gy}/k3/items"), (f"l{FORRAS}", f"{gy}/G3/kinyert_{FORRAS}/items"),
                   (f"r{FORRAS}", f"{gy}/G3/rogzitett_{FORRAS}/items"), (f"o{FORRAS}", f"{gy}/G3/orakulum_{FORRAS}/items")):
        KI.ITEMS[nev] = EXP / d
        KI.SZELETEK[nev] = (FORRAS,)
        KI.FORRASOK = (*KI.FORRASOK, nev)
    KI.main()


def minta(gy: str) -> None:
    def sorok(p: Path) -> list[dict]:
        return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    for fam in CSALADOK:
        uj = sorok(EXP / gy / "k3/items" / f"{fam}.jsonl")
        reg = [it for r in ("friss", "k3", "ert_teszt", "ert_tanito") for it in sorok(EXP / "kor08/adat/G2" / r / "items" / f"{fam}.jsonl")]
        ks = {x["template_group_id"] for x in uj} & {x["template_group_id"] for x in reg}
        kt = {x["state"].strip() for x in uj} & {x["state"].strip() for x in reg}
        print(f"{fam}: {len(uj)} item, {len({x['template_group_id'] for x in uj})} sabloncsoport; közös sabloncsoport {len(ks)}, azonos szöveg {len(kt)}")
        if ks or kt:
            raise SystemExit("a minta nem diszjunkt")


def rogzit(jov: str) -> None:
    if MANIFEST.exists():
        raise SystemExit(f"a J már rögzítve: {MANIFEST.relative_to(EXP)} (felülírni nem lehet)")
    d12 = EXP / "kor08/rogzites/D12/manifest.json"
    m = {"rogzitve": datetime.now().isoformat(timespec="seconds"), "jovahagyas": jov, "d12_sha256": sha(d12),
         "fajlok": {f: sha(EXP / f) for f in FAJLOK}}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"→ {MANIFEST.relative_to(EXP)}: {len(FAJLOK)} fájl")


def ellenoriz() -> None:
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    elt = [f for f, h in m["fajlok"].items() if sha(EXP / f) != h]
    if elt:
        raise SystemExit("a J rögzítése óta változott: " + ", ".join(elt))
    print(f"rendben: {len(m['fajlok'])} rögzített J-fájl változatlan")


def main() -> None:
    a = sys.argv[1:]
    gy = "kor08/adat/J"
    if a[:1] == ["--gyoker"]:
        gy, a = a[1], a[2:]
    cmd, rest = a[0], a[1:]
    sys.argv = [f"j08 {cmd}", *rest]
    if cmd == "kinyer":
        bejegyez(gy)
        import kinyer08
        kinyer08.main()
    elif cmd in ("lanc", "lanc0"):
        L = bejegyez(gy)
        if cmd == "lanc":
            import lanc08j
            lanc08j.aktival()
        L.main()
    elif cmd == "kiolvas":
        kiolvas(gy)
    elif cmd == "b1rel":
        bejegyez(gy)
        import b1rel08
        b1rel08.main()
    elif cmd == "k2":
        bejegyez(gy)
        import g5_k2_08
        g5_k2_08.main()
    elif cmd == "minta":
        minta(gy)
    elif cmd == "rogzit":
        rogzit(rest[rest.index("--jovahagyas") + 1])
    elif cmd == "ellenoriz":
        ellenoriz()
    else:
        raise SystemExit(f"ismeretlen parancs: {cmd}")


if __name__ == "__main__":
    main()
