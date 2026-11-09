"""08 erősebb kontroll (N) — a minimális párok szerkezeti szűrője (11-08, Dani vak címkeellenőrzése után: 3 eltérés a 30-ból, mind generálási hiba). Fejet és modellkimenetet nem néz, csak a szöveget és a tervet.
Egy szöveg akkor érvényes, ha a „korábbi kérelem” a tartalmával együtt áll:
  1. van jelölő mondat, és a `mas` mondat szótöveinek legalább harmada a jelölő mondatban áll (a 8. és a 15. tétel hibája: a jelölő mondat üres, a J a kért összegről szól);
  2. a `kert` mondat szótöveinek legalább harmada a jelölő mondaton kívül áll (a 10. tétel hibája: a J kimaradt, a kulcsszó csak az aláírásban van);
  3. a J kulcsszava a (b'')-ben a jelölő mondaton kívül, az (a'')-ben a jelölő mondatban van.
Egy egység csak mindkét tagjával marad meg.
  python3 kor08/eszkozok/szures08n.py [--felszin]      a szűrő hatása, az itemek érintése nélkül
  python3 kor08/eszkozok/szures08n.py --alkalmaz       a szűrt itemek a helyükre, az eredeti `items_szures_elott/` alá (csak Dani döntése után)
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
sys.path[:0] = [str(HERE)]
import illeszt08m as I  # noqa: E402

FAM = "szabaly.koltsegelszamolas"
JELOLO = {"hu": re.compile(r"korábbi|előző|múltkori|régebbi|másik kérelem", re.I), "en": re.compile(r"earlier|previous|prior|another claim|separate claim|different claim", re.I)}
MONDATHATAR = re.compile(r"(?<=[.!?])\s+|\n+")


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def fedes(tovek: list[str], szoveg: str) -> float:
    return sum(t in szoveg for t in tovek) / max(len(tovek), 1)


def hiba(it: dict, p: dict) -> str | None:
    m, lang, alt = p["illesztes"], it["lang"], it["meta"]["ertelmezes"]["alt"]
    s = [x.strip() for x in MONDATHATAR.split(it["state"]) if x.strip()]
    jel = [x for x in s if JELOLO[lang].search(x)]
    if not jel:
        return "nincs jelölő mondat"
    bent, kint = " ".join(jel).lower(), " ".join(x for x in s if not JELOLO[lang].search(x)).lower()
    if fedes(I.tovek(m["mas"]), bent) < 1 / 3:
        return "a jelölő mondat üres"
    if fedes(I.tovek(m["kert"]), kint) < 1 / 3:
        return "a kért összegről szóló mondat hiányzik"
    kulcs = [k.lower() for k in m["kulcs_van"]]
    if alt == "b" and not any(k in kint for k in kulcs):
        return "a J a jelölő mondatban"
    if alt == "a" and not any(k in bent for k in kulcs):
        return "a J nincs a jelölő mondatban"
    if alt == "a" and any(k in kint for k in kulcs):
        return "a J a kért összegről is szól"
    return None


def szur() -> tuple[list[dict], Counter, set]:
    it = jl(EXP / f"kor08/adat/N/items/{FAM}.jsonl")
    te = {r["group_id"]: r for r in jl(EXP / f"kor08/adat/N/terv/{FAM}.jsonl")}
    ok_ = Counter()
    rossz = set()
    for i in it:
        h = hiba(i, te[i["id"]])
        if h:
            ok_[(i["meta"]["ertelmezes"]["alt"], h)] += 1
            rossz.add(i["meta"]["ertelmezes"]["egyseg"])
    return [i for i in it if i["meta"]["ertelmezes"]["egyseg"] not in rossz], ok_, rossz


def felszin(it: list[dict]) -> None:
    import numpy as np
    from sklearn.metrics import roc_auc_score
    import felszin08 as F
    import felszin08m as M
    x = [F.szoveg(i) for i in it]
    y = np.array([i["meta"]["ertelmezes"]["alt"] == "a" for i in it])
    g = np.array(["|".join(sorted((i["meta"]["ertelmezes"]["forgatokonyv"], i["meta"]["illesztes"]["par"]))) for i in it])
    tan = F.jl(EXP / f"kor08/adat/G2/ert_tanito/items/{FAM}.jsonl")
    xt, yt, gt = [F.szoveg(i) for i in tan], np.array([i["meta"]["ertelmezes"]["alt"] == "a" for i in tan]), np.array([i["template_group_id"] for i in tan])
    print("hossz", round(M.hajtott(y, [len(s) for s in x]), 3))
    for t in ("szó", "karakter"):
        m = F.illeszt(t, xt, yt, gt)[0]
        print(t, "régi", round(float(roc_auc_score(y, m.predict_proba(x)[:, 1])), 3), "friss", round(M.friss(t, x, y, g)[0], 3))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--felszin", action="store_true")
    ap.add_argument("--alkalmaz", action="store_true")
    a = ap.parse_args()
    it, ok_, rossz = szur()
    print(f"marad {len(it)} item ({len(it) // 2} egység), kiesik {len(rossz)} egység; forgatókönyv {len({i['meta']['ertelmezes']['forgatokonyv'] for i in it})}, nyelv {dict(Counter(i['lang'] for i in it))}")
    print("okok:", sorted(ok_.items()))
    k = json.loads((EXP / "kor08/adat/N/audit/kulcs.json").read_text()) if (EXP / "kor08/adat/N/audit/kulcs.json").exists() else {}
    if k:
        ids = {i["id"] for i in it}
        print("az ellenőrzött 30-ból megmarad:", sum(v["id"] in ids for v in k.values()), "| a 3 eltérés közül megmarad:", [n for n in ("8", "10", "15") if k[n]["id"] in ids])
    if a.felszin:
        felszin(it)
    if a.alkalmaz:
        d = EXP / "kor08/adat/N"
        if (d / "items_szures_elott").exists():
            raise SystemExit("a szűrő már alkalmazva")
        (d / "items_szures_elott").mkdir()
        (d / "items_szures_elott" / f"{FAM}.jsonl").write_bytes((d / "items" / f"{FAM}.jsonl").read_bytes())
        (d / "items" / f"{FAM}.jsonl").write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in it), encoding="utf-8")
        print(f"→ {len(it)} item a helyén")


if __name__ == "__main__":
    main()
