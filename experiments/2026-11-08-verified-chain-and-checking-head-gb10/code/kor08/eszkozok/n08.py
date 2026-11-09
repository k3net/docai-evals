"""08 erősebb kontroll (N) — a rögzített eszközök a minimális párokon, burkolóként (a rögzített fájlok nem változnak). A forrás `N1T`, a gyökér `kor08/adat/N`, csak a szabálycsalád. A parancs első szava dönt.

  kinyer     `kinyer08`
  lanc0      `lanc08 futtat`, a rögzített lánc (ahogy a G3-ban)
  kiolvas    `kiolvas08`, a szelet `lN1T`
  b1rel      `b1rel08`
  szoveg     a szöveges modellek a K1(a'') halmazán
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
FORRAS = "N1T"
GY = "kor08/adat/N"
MANIFEST = EXP / "kor08/rogzites/N/manifest.json"
CSALADOK = ("szabaly.koltsegelszamolas",)
FAJLOK = ("kor08/N-rogzites.md", "kor08/eredmenyek/N/felszin/illesztes.json", *(f"kor08/eszkozok/{f}" for f in ("illeszt08m.py", "szint08n.py", "szures08n.py", "felszin08n.py", "n08.py", "k08n.sh")),
          *(f"kor08/adat/N/audit/{f}" for f in ("dontesek.json", "kulcs.json", "dontesek2.json", "kulcs2.json")),
          *(f"{GY}/items/{f}.jsonl" for f in CSALADOK))


def bejegyez():
    import lanc08 as L
    L.FORRASOK[FORRAS] = (f"{GY}/terv", f"{GY}/items", None)
    return L


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def kiolvas() -> None:
    import kiolvas08 as K8
    KI = K8.KI
    KI.ITEMS[f"l{FORRAS}"] = EXP / GY / f"G3/kinyert_{FORRAS}/items"
    KI.SZELETEK[f"l{FORRAS}"] = (FORRAS,)
    KI.FORRASOK = (*KI.FORRASOK, f"l{FORRAS}")
    KI.main()


def szoveg() -> None:
    """A szöveges modellek a K1(a'') pontos halmazán: a régi (a G2 tanítómintáján) és a friss (a párok szerinti CV, kívülre jósolt pontszám). A rögzített olvasat második feltétele ehhez mér."""
    import numpy as np
    import felszin08 as F
    import felszin08m as M
    K = F.K
    fam = CSALADOK[0]
    C = K.Csalad(fam, EXP / f"cache/k08/n/pontoz/l{FORRAS}_{fam}_{FORRAS}.json", EXP / GY / "items", EXP / GY / f"G3/kinyert_{FORRAS}", EXP / GY / f"G3/orakulum_{FORRAS}")
    raw = {i["id"]: i for i in F.jl(EXP / GY / f"items/{fam}.jsonl")}
    x = [F.szoveg(raw[i]) for i in C.ids]
    y = np.array([raw[i]["meta"]["ertelmezes"]["alt"] == "a" for i in C.ids])
    g = np.array(["|".join(sorted((raw[i]["meta"]["ertelmezes"]["forgatokonyv"], raw[i]["meta"]["illesztes"]["par"]))) for i in C.ids])
    tan = F.jl(EXP / f"kor08/adat/G2/ert_tanito/items/{fam}.jsonl")
    xt, yt, gt = [F.szoveg(i) for i in tan], np.array([i["meta"]["ertelmezes"]["alt"] == "a" for i in tan]), np.array([i["template_group_id"] for i in tan])
    halmaz, pos = C.ag["K1a"]
    full = np.where(halmaz)[0]
    res = {"n": int(len(full)), "a": int(pos[full].sum()), "L-RN": K.auroc(-np.mean(C.pont["L-RN"], axis=0)[full], pos[full]), "L-S": K.auroc(-np.mean(C.pont["L-S"], axis=0)[full], pos[full])}
    for t in ("szó", "karakter"):
        res[f"regi_{t}"] = K.auroc(F.illeszt(t, xt, yt, gt)[0].predict_proba(x)[:, 1][full], pos[full])
        res[f"friss_{t}"] = K.auroc(M.friss(t, x, y, g)[1][full], pos[full])
    o = EXP / "kor08/eredmenyek/N/szoveg.json"
    o.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


def rogzit(jov: str) -> None:
    if MANIFEST.exists():
        raise SystemExit(f"az N már rögzítve: {MANIFEST.relative_to(EXP)} (felülírni nem lehet)")
    m = {"rogzitve": datetime.now().isoformat(timespec="seconds"), "jovahagyas": jov, "d12_sha256": sha(EXP / "kor08/rogzites/D12/manifest.json"), "fajlok": {f: sha(EXP / f) for f in FAJLOK}}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"→ {MANIFEST.relative_to(EXP)}: {len(FAJLOK)} fájl")


def ellenoriz() -> None:
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    elt = [f for f, h in m["fajlok"].items() if sha(EXP / f) != h]
    if elt:
        raise SystemExit("az N rögzítése óta változott: " + ", ".join(elt))
    print(f"rendben: {len(m['fajlok'])} rögzített N-fájl változatlan")


def main() -> None:
    cmd, rest = sys.argv[1], sys.argv[2:]
    sys.argv = [f"n08 {cmd}", *rest]
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
    elif cmd == "szoveg":
        szoveg()
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
