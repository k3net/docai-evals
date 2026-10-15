"""03-as kör — HuLU-forrásadapterek a közös sémára (03-runbook 3.1, F0).

  HuRTE, HuWNLI       noul: következik-e a hipotézis a szövegből (igen / nem), X nélkül
  HuCommitmentBank    noul + X: entailment → igen, contradiction → nem, neutral („nem eldönthető”) → X, természetes
  HuCOLA              noul: nyelvtanilag elfogadható-e a mondat, X nélkül
  HuSST               choice: a mondat hangvétele (pozitív / negatív / semleges), X nélkül
  HuCoPA              choice: a két alternatíva közül melyik az ok, illetve a következmény, X nélkül

Splitek: a HuLU tesztcímkéi rejtettek, ezért a forrás val-ja a 03 teszt-ID-je; a 03 val-ja a forrás train-jének 10%-a
(az item-id sha256-ja szerint, determinisztikusan), a többi train. A forrás tesztjét nem használjuk (a HuWNLI-ét sem,
bár a HF-fájlban van címke: a kártya szerint címke nélkül terjesztik).
Az X nélküli családok a runbook 2. pontjának „legalább két család 0% X-szel” feltételét adják.

  python3 kor03/eszkozok/adapter_hulu.py      # → kor03/adat/f0/<család>.jsonl + adapter_hulu_riport.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kozos03 import noul_options, validate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "forras/hf/NYTK"
OUT = ROOT / "adat/f0"
VAL_SHARE = 10  # %


def load(p: Path) -> list[dict]:
    return json.loads(p.read_text(encoding="utf-8"))


def split_of(source_split: str, iid: str) -> str:
    if source_split == "val":
        return "test-id"
    return "val" if int(hashlib.sha256(iid.encode()).hexdigest(), 16) % 100 < VAL_SHARE else "train"


def base(family: str, group: str, source: str, lic: str, src_split: str, sid: str, kind: str) -> dict:
    iid = f"{family}:{src_split}:{sid}"
    return {"id": iid, "family": family, "group": group, "source": source, "source_license": lic,
            "source_ref": f"{src_split}:{sid}", "split": split_of(src_split, iid), "group_id": iid, "lang": "hu",
            "kind": kind, "ketertelmu": False, "soft": None, "x_type": None, "meta": {}}


def nli(name: str, family: str, r: dict, s: str, prem: str, hyp: str, gold, x_type=None) -> dict:
    it = base(family, "nli", name, "CC-BY-SA-4.0", s, str(r["id"]), "noul")
    return {**it, "state": prem, "question": f"Következik-e a szövegből, hogy „{hyp}”?", "options": noul_options("hu"),
            "gold": gold, "x_type": x_type}


def hurte(s: str, r: dict) -> dict:
    return nli("HuRTE", "nli.hurte", r, s, r["premise"], r["hypothesis"], "igen" if str(r["label"]) == "1" else "nem")


def huwnli(s: str, r: dict) -> dict:
    return nli("HuWNLI", "nli.huwnli", r, s, r["sentence1"], r["sentence2"], "igen" if str(r["label"]) == "1" else "nem")


CB = {"entailment": ("igen", None), "contradiction": ("nem", None), "neutral": (None, "natural")}


def hucb(s: str, r: dict) -> dict:
    gold, xt = CB[r["label"]]
    return nli("HuCommitmentBank", "nli.hucb", r, s, r["premise"], r["hypothesis"], gold, xt)


def hucola(s: str, r: dict) -> dict:
    it = base("nyelv.hucola", "szentiment", "HuCOLA", "CC-BY-SA-4.0", s, str(r["id"]), "noul")
    return {**it, "state": r["sentence"], "question": "Nyelvtanilag helyes, elfogadható magyar mondat-e ez?",
            "options": noul_options("hu"), "gold": "igen" if str(r["label"]) == "1" else "nem"}


SST = [("pozitiv", "pozitív"), ("negativ", "negatív"), ("semleges", "semleges")]
SST_GOLD = {"positive": "pozitiv", "negative": "negativ", "neutral": "semleges"}


def husst(s: str, r: dict) -> dict:
    it = base("szentiment.husst", "szentiment", "HuSST", "CC-BY-SA-4.0", s, str(r["id"]), "choice")
    return {**it, "state": r["sentence"], "question": "Milyen a mondat hangvétele?",
            "options": [{"id": i, "text": t} for i, t in SST], "gold": SST_GOLD[r["label"]]}


def hucopa(s: str, r: dict) -> dict:
    it = base("qa.hucopa", "qa", "HuCoPA", "BSD-2-Clause", s, str(r["id"]), "choice")
    q = "Mi lehetett ennek az oka?" if r["question"] == "cause" else "Mi lett ennek a következménye?"
    return {**it, "state": r["premise"], "question": q,
            "options": [{"id": "1", "text": r["choice1"]}, {"id": "2", "text": r["choice2"]}], "gold": str(int(r["label"]) + 1),
            "meta": {"copa_kerdes": r["question"]}}  # a fájlban a címke 0/1 (a kártya 1/2-t ír): 0 = choice1


ADAPTERS = {"HuRTE": ("nli.hurte", hurte), "HuWNLI": ("nli.huwnli", huwnli), "HuCommitmentBank": ("nli.hucb", hucb),
            "HuCOLA": ("nyelv.hucola", hucola), "HuSST": ("szentiment.husst", husst), "HuCoPA": ("qa.hucopa", hucopa)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rep = {}
    for src, (family, fn) in ADAPTERS.items():
        rows, bad = [], 0
        for s in ("train", "val"):
            for r in load(SRC / src / "data" / f"{s}.json"):
                it = fn(s, r)
                if validate(it):
                    bad += 1
                    print(src, it["id"], validate(it))
                    continue
                rows.append(it)
        (OUT / f"{family}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                                             encoding="utf-8")
        rep[family] = {"forras": src, "n": len(rows), "hibas": bad,
                       "split": dict(Counter(r["split"] for r in rows)),
                       "gold": {sp: dict(Counter(str(r["gold"]) for r in rows if r["split"] == sp))
                                for sp in ("train", "val", "test-id")},
                       "x_arany": sum(r["gold"] is None for r in rows) / len(rows)}
        print(family, json.dumps(rep[family], ensure_ascii=False))
    (OUT / "adapter_hulu_riport.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
