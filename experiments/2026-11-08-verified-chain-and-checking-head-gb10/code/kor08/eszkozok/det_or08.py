"""08 — determinizmus-őr a kiolvasáshoz (Dani 11-03): minden kiolvasási folyamat egy rögzített referenciaszelettel indul
és zárul (`det0`, `det1`: 50 szabálycsaládi T500-item, kanonikus mód; `lib08.sh`), és a sorainak bitre egyezniük kell a
referenciával (bemenet: sorrend, címkék, prompt-tokenszám; kimenet: pred és minden címke-logprob). Eltéréskor a futás
jelez (`JELZES-DET-<fázis>`), nem áll le. A referencia (`kor08/adat/G1/det_ref`) a K08G1DET-ben két külön folyamatban
bitre azonosnak mért `o06` T500-kiolvasásból (v1 blokk), az itemek rögzített másolatával. Csak stdlib (a host
`python3`-ján fut).
  python3 kor08/eszkozok/det_or08.py keszit --items kor08/adat/G1/orakulum_06/items --jell cache/k08/jellemzok_det --elo o06
  python3 kor08/eszkozok/det_or08.py ref
  python3 kor08/eszkozok/det_or08.py ellenoriz --jell cache/k08/jellemzok --elo det0 det1 --out logs/k08g1e/det_or.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
REF = EXP / "kor08/adat/G1/det_ref"
FAM = "szabaly.koltsegelszamolas"
SZELET = "T500"
ALLAPOTONKENT = 12  # állapotonként ennyi item a sha256(id) sorrendjében, + a 2 leghosszabb prompt
HOSSZU = 2


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sorok(jell: Path, elo: str) -> list[str]:
    d = jell / f"{elo}_{FAM}_{SZELET}__kanonikus"
    if not d.exists():
        raise FileNotFoundError(d)
    return [x for f in sorted(d.glob("sorok_*.jsonl")) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]


def cmd_keszit(a) -> None:
    if REF.exists():
        raise SystemExit(f"a referencia már létezik, rögzített: {REF.relative_to(EXP)}")
    src = EXP / a.items / f"{FAM}.jsonl"
    items = [x for x in src.read_text(encoding="utf-8").splitlines() if x.strip()]
    items = [x for x in items if json.loads(x)["split"] == SZELET]
    rows = {json.loads(x)["id"]: x for x in sorok(EXP / a.jell, a.elo)}
    if {json.loads(x)["id"] for x in items} != rows.keys():
        raise SystemExit("az itemek és a kiolvasott sorok azonosítói eltérnek")
    rend = sorted(items, key=lambda x: hashlib.sha256(json.loads(x)["id"].encode()).hexdigest())
    valasztott: list[str] = []
    for st in ("MATCH", "NO_MATCH", "MISSING_DATA", "OUT_OF_SCOPE"):
        valasztott += [x for x in rend if json.loads(x)["content_state"] == st][:ALLAPOTONKENT]
    marad = [x for x in rend if x not in valasztott]
    valasztott += sorted(marad, key=lambda x: -json.loads(rows[json.loads(x)["id"]])["n_prompt_tokens"])[:HOSSZU]
    ids = [json.loads(x)["id"] for x in valasztott]
    (REF / "items").mkdir(parents=True)
    (REF / "items" / f"{FAM}.jsonl").write_text("\n".join(valasztott) + "\n", encoding="utf-8")
    (REF / "sorok_ref.jsonl").write_text("\n".join(rows[i] for i in ids) + "\n", encoding="utf-8")
    tok = [json.loads(rows[i])["n_prompt_tokens"] for i in ids]
    meta = {"forras_items": str(src.relative_to(EXP)), "forras_items_sha256": sha(src),
            "forras_sorok": f"{a.jell}/{a.elo}_{FAM}_{SZELET}__kanonikus", "n": len(ids),
            "allapotok": {st: sum(i.split(":")[3] == st for i in ids) for st in ("MATCH", "NO_MATCH", "MISSING_DATA",
                                                                                   "OUT_OF_SCOPE")},
            "nyelvek": {ny: sum(i.split(":")[2] == ny for i in ids) for ny in ("hu", "en")},
            "prompt_token": {"min": min(tok), "max": max(tok)},
            "kivalasztas": f"állapotonként {ALLAPOTONKENT} a sha256(id) sorrendjében, + a {HOSSZU} leghosszabb prompt",
            "items_sha256": sha(REF / "items" / f"{FAM}.jsonl"), "sorok_ref_sha256": sha(REF / "sorok_ref.jsonl"),
            "keszult": datetime.now().isoformat(timespec="seconds")}
    (REF / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=1))


def ref_rendben() -> dict:
    meta = json.loads((REF / "meta.json").read_text(encoding="utf-8"))
    if sha(REF / "items" / f"{FAM}.jsonl") != meta["items_sha256"] or sha(REF / "sorok_ref.jsonl") != meta["sorok_ref_sha256"]:
        print("a referencia megváltozott (sha256)")
        sys.exit(2)
    return meta


def osszevet(ref: dict[str, dict], uj: dict[str, dict]) -> dict:
    kozos = ref.keys() & uj.keys()
    bem = sum(ref[i]["order"] != uj[i]["order"] or ref[i]["labels"] != uj[i]["labels"]
              or ref[i]["n_prompt_tokens"] != uj[i]["n_prompt_tokens"] for i in kozos)
    dm = [max(abs(ref[i]["label_logprobs"][c] - uj[i]["label_logprobs"].get(c, float("inf")))
              for c in ref[i]["label_logprobs"]) for i in kozos]
    r = {"n": len(ref), "hianyzik": len(ref.keys() - uj.keys()), "bemenet_elter": bem,
         "pred_elter": sum(ref[i]["pred"] != uj[i]["pred"] for i in kozos),
         "bitre_azonos": sum(ref[i]["label_logprobs"] == uj[i]["label_logprobs"] for i in kozos),
         "max_delta": max(dm, default=0.0)}
    r["rendben"] = r["hianyzik"] == 0 and r["bitre_azonos"] == r["n"]
    return r


def cmd_ref(_a) -> None:
    meta = ref_rendben()
    print(f"a referencia rendben: {meta['n']} item, {meta['allapotok']}, {meta['nyelvek']}")


def cmd_ellenoriz(a) -> None:
    ref_rendben()
    ref = {r["id"]: r for r in map(json.loads, (REF / "sorok_ref.jsonl").read_text(encoding="utf-8").splitlines())}
    res = {}
    for elo in a.elo:
        try:
            uj = {r["id"]: r for r in map(json.loads, sorok(EXP / a.jell, elo))}
        except FileNotFoundError as e:
            res[elo] = {"rendben": False, "hiba": f"nincs kimenet: {e}"}
        else:
            res[elo] = osszevet(ref, uj)
        print(f"{elo}: " + ", ".join(f"{k} {v}" for k, v in res[elo].items()))
    if a.out:
        out = EXP / a.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"jell": a.jell, "ellenorizve": datetime.now().isoformat(timespec="seconds"),
                                   "eredmeny": res}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    sys.exit(0 if all(r["rendben"] for r in res.values()) else 3)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("keszit")
    k.add_argument("--items", required=True)
    k.add_argument("--jell", required=True)
    k.add_argument("--elo", required=True)
    sub.add_parser("ref")
    e = sub.add_parser("ellenoriz")
    e.add_argument("--jell", required=True)
    e.add_argument("--elo", nargs="+", default=["det0", "det1"])
    e.add_argument("--out")
    a = ap.parse_args()
    {"keszit": cmd_keszit, "ref": cmd_ref, "ellenoriz": cmd_ellenoriz}[a.cmd](a)


if __name__ == "__main__":
    main()
