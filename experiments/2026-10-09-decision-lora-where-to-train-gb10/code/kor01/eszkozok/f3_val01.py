"""K01F3 val-elemzés: a bázis kalibrációs karjai (L0/L1★) és az L3 a 01-es val-on, a 00 `elemzes.py` függvényeivel.

A mérőszámok definíciója bájtra a 00-é (τ@95/@90 egyoldali CP-vel, AURC, ECE, X-fedés). A val itt a kar- és a
küszöbválasztás saját mintája, így a lefedettség a val-on optimista (in-sample); karok összevetésére jó, végső
állításra nem (az a teszten, F4). Rétegek: val-xlam, val-massive és a kettő együtt; plafon = a pontozott nem-X itemek
aránya (ennél nagyobb besorolási lefedettség nem érhető el hibátlan döntéssel sem).

  LDH_EXP=$PWD python3 kor01/eszkozok/f3_val01.py --kar k01_l3mixse_p30_s1
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "eszkozok"))
from common import read_jsonl, write_json  # noqa: E402
from elemzes import (TARGETS, FAIL_BELOW, arm_predictions, by_item, choose_tau, fit_temperature, label_bias,  # noqa: E402
                     load_meta, metrics)

ROOT = Path(__file__).resolve().parents[1]
RETEG = {"xlam": "val-xlam", "massive_hu": "val-massive"}


def karok(rows: list[dict], meta: dict, ids: list[str], csak: list[str] | None = None) -> dict:
    by = by_item(rows, None)
    val0 = [r for r in rows if r["perm"] == 0]
    temp = fit_temperature(val0, meta)
    bias = label_bias(val0)
    arms = {"nyers": {}, "temp": {"temp": temp}, "perm_avg": {"temp": temp}}
    for lam in (0.5, 0.75, 1.0):
        arms[f"batch_{lam}"] = {"bias": bias, "lam": lam, "temp": temp}
    out = {"temperature": temp, "karok": {}}
    for name, prm in arms.items():
        if csak and name not in csak:
            continue
        p = arm_predictions("batch" if name.startswith("batch") else name, by, meta, prm)
        blk = {}
        for tgt, tn in TARGETS:
            tau = choose_tau(p, meta, ids, tgt)
            blk[tn] = {"tau": tau, "osszes": metrics(p, meta, ids, tau, FAIL_BELOW[tn]),
                       **{r: metrics(p, meta, [i for i in ids if meta[i]["reteg"] == r], tau, FAIL_BELOW[tn])
                          for r in RETEG.values()}}
        out["karok"][name] = blk
        out["karok"][name]["_pred"] = {i: [p[i][0], p[i][1]] for i in ids}
    best = max((k for k in out["karok"]), key=lambda k: (out["karok"][k]["95"]["osszes"]["besorolasi_lefedettseg"],
                                                       out["karok"][k]["90"]["osszes"]["besorolasi_lefedettseg"],
                                                       -out["karok"][k]["95"]["osszes"]["ece"]))
    out["legjobb"] = best
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kar", required=True)
    ap.add_argument("--bazis", default="", help="a bázis val-kiolvasása az F3 alatt (alap: a kar sajátja, ha nincs, a pilotké)")
    args = ap.parse_args()
    d = ROOT / "eredmenyek/F3" / args.kar
    meta = load_meta(ROOT / "adat")
    items = {it["id"]: it for it in read_jsonl(ROOT / "adat/items_val.jsonl")}
    for i, it in items.items():
        meta[i]["reteg"] = RETEG[it["forras"]]
    ids = sorted(items)
    scored = [i for i in ids if not meta[i].get("ketertelmu")]
    plafon = {"osszes": sum(meta[i]["gold"] is not None for i in scored) / len(scored)}
    for r in RETEG.values():
        s = [i for i in scored if meta[i]["reteg"] == r]
        plafon[r] = sum(meta[i]["gold"] is not None for i in s) / len(s)

    bf = ROOT / "eredmenyek/F3" / args.bazis if args.bazis else d / "vllm_val_bazis.jsonl"
    if not bf.exists():
        bf = ROOT / "eredmenyek/F3/k01_l3mixse_p30_s1/vllm_val_bazis.jsonl"
    bazis = karok(read_jsonl(bf), meta, ids)
    l3 = karok(read_jsonl(d / "vllm_val.jsonl"), meta, ids, csak=["nyers", "temp", "perm_avg"])
    hf = {r["id"]: r for r in read_jsonl(d / "hf_val.jsonl")}
    v0 = {r["id"]: r for r in read_jsonl(d / "vllm_val.jsonl") if r["perm"] == 0}
    egyezes = sum(hf[i]["pred"] == v0[i]["pred"] for i in hf) / len(hf)

    def tomor(k: dict, name: str) -> dict:
        b = k["karok"][name]
        return {t: {"tau": round(b[t]["tau"], 4) if b[t]["tau"] != float("inf") else None,
                    **{r: {"lef": round(m["besorolasi_lefedettseg"], 4),
                           "prec": None if m["besorolasi_precizitas"] is None else round(m["besorolasi_precizitas"], 4),
                           "aurc": round(m["aurc"], 4), "ece": round(m["ece"], 4), "pontossag": round(m["pontossag"], 4),
                           "x_fedes": None if m["x_fedes"] is None else round(m["x_fedes"], 4)}
                        for r, m in b[t].items() if r != "tau"}} for t in ("95", "90")}

    pb, pl = bazis["karok"][bazis["legjobb"]]["_pred"], l3["karok"]["temp"]["_pred"]
    rep = {
        "kar": args.kar, "n_val": len(ids), "pontozott": len(scored), "ketertelmu": len(ids) - len(scored),
        "plafon": {k: round(v, 4) for k, v in plafon.items()},
        "bazis": {"temperature": bazis["temperature"], "L1_csillag": bazis["legjobb"],
                  "karok": {k: tomor(bazis, k) for k in bazis["karok"]}},
        "L3": {"temperature": l3["temperature"], "karok": {k: tomor(l3, k) for k in l3["karok"]}},
        "hf_vllm_top_egyezes_perm0": round(egyezes, 4),
        "top_cimke_atvaltas_L1csillag_vs_L3temp": dict(Counter(
            f"{'jo' if pb[i][0] == meta[i]['gold'] else 'rossz'}→{'jo' if pl[i][0] == meta[i]['gold'] else 'rossz'}"
            for i in scored)),
    }
    write_json(d / "val_elemzes.json", rep)
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
