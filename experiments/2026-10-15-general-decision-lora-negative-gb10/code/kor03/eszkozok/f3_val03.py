"""03-as kör — F3 val-elemzés: a G3-karok és az L1★ a 03-as val-on, a 00 `elemzes.py` mérőszámaival.

Minden karnál ugyanaz a választás, mint az F2 L1★-jánál: a kalibrációs karok közül (nyers, temperature, perm-átlag,
batch-korrekció) a val lef@95 szerinti legjobb, saját temperature-rel és saját τ@95-tel. A val itt a kar- és a
küszöbválasztás saját mintája, így a lefedettség optimista (in-sample): karok összevetésére jó, végső állításra nem
(az a kitartott rétegeken, F4). Bontás: összesen, csoportonként, és az X-fedés X-típusonként.

  python3 kor03/eszkozok/f3_val03.py [--karok k03_g3_s1,k03_g3kemeny_s1]   → eredmenyek/F3/f3_val03.json
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from f2_elemzes03 import BUKAS, F2R, arm_predictions, choose_tau, fit_temperature, label_bias, load_items, metrics, rows

F3R = F2R.parent / "F3"


def readout(p: Path, ids: set[str]) -> dict[str, list[dict]]:
    by = defaultdict(list)
    for r in rows(p):
        if r["id"] in ids:
            r["label_logprobs"] = {lab: math.log(max(1e-12, r["probs"][lab])) for lab in r["labels"]}
            by[r["id"]].append(r)
    return by


def kar(by: dict, meta: dict, val_ids: list[str]) -> dict:
    val0 = [r for rs in by.values() for r in rs if r["perm"] == 0]
    temp, bias = fit_temperature(val0, meta), label_bias(val0)
    arms = {"nyers": {}, "temp": {"temp": temp}, "perm_avg": {"temp": temp}}
    arms |= {f"batch_{lam}": {"bias": bias, "lam": lam, "temp": temp} for lam in (0.5, 0.75, 1.0)}
    res = {}
    for name, prm in arms.items():
        pv = arm_predictions("batch" if name.startswith("batch") else name, by, meta, prm)
        t95, t90 = choose_tau(pv, meta, val_ids, 0.95), choose_tau(pv, meta, val_ids, 0.90)
        res[name] = {"pv": pv, "tau95": t95, "val": metrics(pv, meta, val_ids, t95, BUKAS),
                     "val90": metrics(pv, meta, val_ids, t90, 0.88)}
    best = max(res, key=lambda k: (res[k]["val"].get("besorolasi_lefedettseg", 0),
                                   res[k]["val90"].get("besorolasi_lefedettseg", 0), -res[k]["val"].get("ece", 1)))
    b = res[best]
    groups, xtypes = defaultdict(list), defaultdict(list)
    for i in val_ids:
        groups[meta[i]["group"]].append(i)
        if meta[i]["x"] and not meta[i]["ketertelmu"]:
            xtypes[meta[i]["x_type"]].append(i)
    pick = ("besorolasi_lefedettseg", "besorolasi_precizitas", "aurc", "ece", "pontossag", "x_fedes", "n")
    return {"kalibracio": best, "temp": temp, "tau95": b["tau95"],
            "osszes": {k: b["val"].get(k) for k in pick},
            "lef90": b["val90"].get("besorolasi_lefedettseg"),
            "csoport": {g: {k: metrics(b["pv"], meta, ids, b["tau95"], BUKAS).get(k) for k in pick}
                        for g, ids in sorted(groups.items())},
            "x_tipus": {t: {"n": len(ids), "x_fedes": metrics(b["pv"], meta, ids, b["tau95"], BUKAS).get("x_fedes")}
                        for t, ids in sorted(xtypes.items())}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--karok", default="k03_g3_s1,k03_g3kemeny_s1")
    a = ap.parse_args()
    meta = load_items("val")
    val_ids = sorted(meta)
    src = {"L1★": F2R / "qwen_val.jsonl"} | {k: F3R / k / "vllm_val.jsonl" for k in a.karok.split(",")}
    out = {}
    for name, p in src.items():
        by = readout(p, set(val_ids))
        if len(by) < len(val_ids) or any(len(v) < 4 for v in by.values()):
            print(f"{name}: hiányos kiolvasás ({len(by)}/{len(val_ids)} item), kihagyva")
            continue
        out[name] = kar(by, meta, val_ids)
    F3R.mkdir(parents=True, exist_ok=True)
    (F3R / "f3_val03.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    f = lambda v: "-" if v is None else f"{v:.3f}"
    print(f"{'kar':18s} {'kalibr.':10s} {'lef@95':>7s} {'lef@90':>7s} {'prec':>6s} {'AURC':>6s} {'ECE':>6s} {'top-1':>6s} {'X-fed':>6s}")
    for name, r in out.items():
        o = r["osszes"]
        print(f"{name:18s} {r['kalibracio']:10s} {f(o['besorolasi_lefedettseg']):>7s} {f(r['lef90']):>7s} "
              f"{f(o['besorolasi_precizitas']):>6s} {f(o['aurc']):>6s} {f(o['ece']):>6s} {f(o['pontossag']):>6s} {f(o['x_fedes']):>6s}")


if __name__ == "__main__":
    main()
