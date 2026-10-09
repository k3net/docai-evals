"""K01F5b — külső összevetés a JEV-vel a Decision Index 0.2.1 két sávján (01-runbook 7. pont, Napló 2026-10-09).

Bemenet (kor01/../kulso/f5b/):
  jev/<modell>/results.jsonl.gz      — `autotrust/jev-decision-index-results` (Apache-2.0), itemenkénti valószínűségek;
  when2call_test_mcq.jsonl           — nvidia/When2Call @0582f77, sha256 8c3694e5… (a kit rögzített forrása);
  clinc_data_full.json               — clinc/oos-eval data_full.json, sha256 36923c37… (a kit rögzített forrása).
A gold a kit építőivel azonos módon áll elő (normalize_direct.clinc150, adapters_added.when2call): a When2Call A–D =
direct, tool_call, request_for_info, cannot_answer; a CLINC opciói a 151 címke rendezett sorrendjében (`option_k`).

Leképezés a 00/01 mérőszámaira (`elemzes.metrics`, `choose_tau`): az X a „nincs illő válasz” — When2Call-ban a
cannot_answer, CLINC-ben az oos. A pred = a legvalószínűbb opció (X → None), a bizalom = a valószínűsége. Validációs
halmaz nincs, ezért a τ@95 kétfelé osztott keresztillesztéssel áll elő (az item-azonosító hash-e szerint): az egyik
felén választott τ a másik felén mér, és fordítva; a jelentett érték a két fél összege.

Átfedés a 01-gyel: a 01 tesztjének When2Call-itemjei (`w2c-<uuid>`, a tool_call és a cannot_answer válaszúak) a JEV
soraival uuid szerint párosítva; ugyanazokon az itemeken a JEV X-fedése (top = cannot_answer) és a 01 karjaié (top = X).
A keret eltér: a JEV négy válaszmód közül választ, a 01 karjai eszközlistából + X-ből.

  python3 kor01/eszkozok/f5b_jev.py
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "eszkozok"))
from common import read_jsonl, write_json  # noqa: E402
from elemzes import choose_tau, metrics  # noqa: E402
from f4_elemzes01 import load_arm, load_meta01  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
K = ROOT.parent / "kulso/f5b"
MODELS = {"jev-9b": "JEV-9B", "jev-27b": "JEV-27B", "jev-gemma4-26b-a4b": "JEV-Gemma4-26B-A4B"}
SHA = {"when2call_test_mcq.jsonl": "8c3694e583eeeb8dbc297e6cd90da70efc68efa4b6adb7227523e828c6b7b14c",
       "clinc_data_full.json": "36923c3705a59e08fe9c3883d8bc2dd966ef93e22cb78ac41171782a698d56e0"}
W2C_ORDER = ["direct", "tool_call", "request_for_info", "cannot_answer"]
W2C_KEYS = "ABCD"
KEEP = ("besorolasi_lefedettseg", "besorolasi_precizitas", "aurc", "ece", "x_fedes", "x_precizitas", "pontossag")


def check_sha() -> None:
    for f, h in SHA.items():
        got = hashlib.sha256((K / f).read_bytes()).hexdigest()
        if got != h:
            raise SystemExit(f"{f}: sha256 eltér ({got})")


def gold_w2c() -> dict:
    out = {}
    for r in read_jsonl(K / "when2call_test_mcq.jsonl"):
        assert list(r["answers"]) == W2C_ORDER
        out[f"62:{r['uuid']}"] = {"gold": W2C_KEYS[W2C_ORDER.index(r["correct_answer"])], "kat": r["correct_answer"],
                                  "uuid": r["uuid"]}
    return out


def gold_clinc() -> tuple[dict, str]:
    obj = json.loads((K / "clinc_data_full.json").read_text())
    labels = sorted({p[1] for p in obj["train"]} | {"oos"})
    assert len(labels) == 151
    out = {}
    for split in ("test", "oos_test"):
        for i, (_, lab) in enumerate(obj[split]):
            out[f"CLINC150+OOS:{split}:{i}"] = {"gold": f"option_{labels.index(lab)}", "kat": "oos" if lab == "oos" else "in"}
    return out, f"option_{labels.index('oos')}"


def jev_probs(model: str) -> dict:
    out = {}
    for line in gzip.open(K / "jev" / model / "results.jsonl.gz", "rt"):
        r = json.loads(line)
        if r["dataset"] not in ("When2Call MCQ", "CLINC150+OOS") or r["status"] != "ok":
            continue
        (ans,) = r["response"]["answers"].values()
        out[r["group_id"]] = ans["probabilities"]
    return out


def to_preds(probs: dict, gold: dict, x_key: str) -> tuple[dict, dict]:
    preds, meta = {}, {}
    for gid, g in gold.items():
        p = probs[gid]
        top = max(p, key=p.get)
        preds[gid] = (None if top == x_key else top, float(p[top]))
        meta[gid] = {"gold": None if g["gold"] == x_key else g["gold"]}
    return preds, meta


def crossfit(preds: dict, meta: dict, ids: list[str]) -> dict:
    """τ@95 kétfelé osztott keresztillesztéssel; a két fél besorolásainak összesítése."""
    half = {i: int(hashlib.sha256(i.encode()).hexdigest(), 16) % 2 for i in ids}
    a = [i for i in ids if half[i] == 0]
    b = [i for i in ids if half[i] == 1]
    asg = ok = 0
    xasg = 0
    taus = []
    for cal, ev in ((a, b), (b, a)):
        tau = choose_tau(preds, meta, cal, 0.95)
        taus.append(tau)
        for i in ev:
            if preds[i][0] is not None and preds[i][1] >= tau:
                asg += 1
                ok += preds[i][0] == meta[i]["gold"]
                xasg += meta[i]["gold"] is None
    nx = sum(meta[i]["gold"] is None for i in ids)
    return {"tau_ket_fel": taus, "lef95": asg / len(ids), "prec95": ok / asg if asg else None,
            "x_besorolva95": xasg / nx if nx else None}


def bench(preds: dict, meta: dict, gold: dict) -> dict:
    ids = list(gold)
    m = metrics(preds, meta, ids, float("inf"))
    res = {k: m[k] for k in KEEP if k in m and k not in ("besorolasi_lefedettseg", "besorolasi_precizitas")}
    res["plafon"] = sum(meta[i]["gold"] is not None for i in ids) / len(ids)
    res.update(crossfit(preds, meta, ids))
    kat = defaultdict(list)
    for i in ids:
        kat[gold[i]["kat"]].append(preds[i][0] == meta[i]["gold"])
    res["helyes_kategoriankent"] = {k: sum(v) / len(v) for k, v in sorted(kat.items())}
    return res


def w2c_confusion(preds: dict, gold: dict) -> dict:
    c = Counter()
    for i, g in gold.items():
        p = preds[i][0]
        c[f"{g['kat']}->{W2C_ORDER[W2C_KEYS.index(p)] if p else 'cannot_answer'}"] += 1
    return dict(sorted(c.items()))


def call_separation(pos: list[float], neg: list[float]) -> dict:
    """Hívási valószínűség: AUROC (tool_call = pozitív, cannot_answer = negatív) és a hamis hívási arány a cannot_answer
    itemeken, ha a küszöb a tool_call itemek 90, illetve 95%-át hívatja."""
    pos_s, neg_s = sorted(pos), sorted(neg)
    import bisect
    auc = sum(bisect.bisect_left(neg_s, x) + 0.5 * (bisect.bisect_right(neg_s, x) - bisect.bisect_left(neg_s, x))
              for x in pos_s) / (len(pos_s) * len(neg_s))
    out = {"auroc": auc}
    for rec in (0.90, 0.95):
        thr = pos_s[int((1 - rec) * len(pos_s))]
        out[f"hamis_hivas@{int(rec * 100)}"] = sum(x >= thr for x in neg_s) / len(neg_s)
    return out


def overlap01(jev: dict[str, dict], jev_pb: dict[str, dict], gw: dict) -> dict:
    """A 01 When2Call-itemjein, When2Call-kategóriánként (a 01 a tool_call és a request_for_info itemeket nem-X-nek
    vette, a gold az eszköz; a cannot_answer az X). A 01 karjainál: hív-e (top ≠ X) és helyes-e az eszköz; a JEV-nél:
    a választott válaszmód (A direct, B tool_call, C request_for_info, D cannot_answer)."""
    meta = load_meta01()
    V = ROOT / "eredmenyek/F4/vllm"
    arms = {"L1★": load_arm(V, "bazis_val", "bazis_test", meta, "perm_avg")[0]}
    for k in ("s1", "s2", "s3"):
        arms[f"L3 {k}"] = load_arm(V, f"l3_{k}_val", f"l3_{k}_test", meta, "temp")[0]
    ids01 = [i for i in meta if meta[i]["forras"] == "w2c_teszt" and not meta[i].get("ketertelmu")]
    pair = {i: f"62:{i[4:]}" for i in ids01 if f"62:{i[4:]}" in gw}
    kat = defaultdict(list)
    for i, g in pair.items():
        kat[gw[g]["kat"]].append(i)
    out = {"n_parositott": len(pair), "n_kategoriankent": {k: len(v) for k, v in sorted(kat.items())}, "karok": {}}
    for name, p in arms.items():
        r = {}
        for k, ids in sorted(kat.items()):
            r[k] = {"hiv": sum(p[i][0] is not None for i in ids) / len(ids)}
            if k != "cannot_answer":
                r[k]["helyes_eszkoz"] = sum(p[i][0] == meta[i]["gold"] for i in ids) / len(ids)
        r["szetvalasztas"] = call_separation([1 - p[i][2].get(None, 0.0) for i in kat["tool_call"]],
                                             [1 - p[i][2].get(None, 0.0) for i in kat["cannot_answer"]])
        out["karok"][name] = r
    for name, preds in jev.items():
        r = {}
        for k, ids in sorted(kat.items()):
            c = Counter(preds[pair[i]][0] or "D" for i in ids)
            r[k] = {"hiv": c["B"] / len(ids), **{f"valasz_{W2C_ORDER[W2C_KEYS.index(x)]}": c[x] / len(ids) for x in W2C_KEYS}}
        pb = jev_pb[name]
        r["szetvalasztas"] = call_separation([pb[pair[i]] for i in kat["tool_call"]], [pb[pair[i]] for i in kat["cannot_answer"]])
        out["karok"][name] = r
    return out


def main() -> None:
    check_sha()
    gw = gold_w2c()
    gc, oos_key = gold_clinc()
    res = {"forras": {"jev": "autotrust/jev-decision-index-results", "when2call": "nvidia/When2Call@0582f77",
                      "clinc": "clinc/oos-eval data_full.json"}, "When2Call MCQ": {}, "CLINC150+OOS": {}}
    w2c_preds, w2c_pb = {}, {}
    for m, name in MODELS.items():
        probs = jev_probs(m)
        pw, mw = to_preds(probs, gw, "D")
        w2c_preds[name] = pw
        w2c_pb[name] = {g: float(probs[g]["B"]) for g in gw}
        res["When2Call MCQ"][name] = {**bench(pw, mw, gw), "konfuzio": w2c_confusion(pw, gw)}
        pc, mc = to_preds(probs, gc, oos_key)
        res["CLINC150+OOS"][name] = bench(pc, mc, gc)
    res["atfedes_01_when2call"] = overlap01(w2c_preds, w2c_pb, gw)
    write_json(ROOT / "eredmenyek/F5b/f5b_jev.json", res)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
