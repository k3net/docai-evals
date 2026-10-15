"""03-as kör — az F2 elemzése (03-runbook 4.1, 4.2, 4.4, 4.7, 6., 10. pont 4.).

A 00 `eszkozok/elemzes.py` kalibrációs és mérőfüggvényeivel (a kiolvaso03 sorai `label_logprobs`-ra alakítva: a
szűkített valószínűség logaritmusa; a szűkített softmax eltolás-invariáns, így a temperature-illesztés ugyanaz).

  1. L1★ (Qwen3.6 L0): kalibrációs karok a val-on (nyers, temperature, batch λ ∈ {0,5; 0,75; 1}, 4-permutációs átlag
     + temperature); L1★ = a val-on legnagyobb lefedettség@95, holtversenyben @90, majd kisebb ECE (00 szabály).
  2. Rétegenként az L1★ a val-on választott τ@95-tel (leíró; a H3 szerint a val-τ nem feltétlenül visz át).
  3. Családválasztás (10. pont 4.): train-családonként az L1★ a globális τ-val. Plafon (saját mérőszám) = a pontozott
     itemek nem-X hányada (a besorolási lefedettség ennél több nem lehet). Plafon közeli: lefedettség@95 ≥ a plafon
     90%-a, és a precizitás nem bukik (≥ 0,93) → a család legfeljebb a train 5%-a.
  4. Tanárkapu (4.4): a val forrás- és konstrukciós goldú itemjein (a szintetikus nélkül), szűretlenül. A Gemma és a
     Mistral 4-permutációs átlag + saját temperature; a Qwen gondolkodó módja 4 minta (mintánként más permutáció)
     empirikus eloszlása. Feltételek: top-1 pontosság ≥ az L1★-é ugyanazokon az itemeken; ECE ≤ 0,05; X-es egységen
     az X-fedés ≥ 0,5 típusonként (legalább 10 X-itemű típuson). Az egység a csoport (családonként a val túl kicsi: a
     kapu családonkénti változatát csak n ≥ 60 családra jelentjük, leíróan). A gondolkodó tanár csak csoportszinten.
  5. Gépi zajbecslés (4.2): forrásonként; zajjelölt, ha legalább két olvasó ugyanarra a nem-gold címkére szavaz: a
     Gemma (≥ 0,8 kalibrált bizalommal), a Qwen gondolkodó mintája, és leíróan a Qwen L1★ (≥ 0,8). Küszöb 10%.
  6. Bázis-horgony (4.7): az L1★ eloszlása minden train-itemre → adat/f2/horgony_qwen_L1.jsonl.

  python3 kor03/eszkozok/f2_elemzes03.py   → eredmenyek/F2/f2_elemzes.json, f2_elemzes.md
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]
sys.path.insert(0, str(ROOT.parent / "eszkozok"))
from elemzes import arm_predictions, choose_tau, fit_temperature, label_bias, metrics  # noqa: E402

F2A, F2R = ROOT / "adat/f2", ROOT / "eredmenyek/F2"
PLAFON_ARANY, BUKAS, ECE_MAX, XFEDES_MIN, ZAJ_KUSZOB, ZAJ_BIZALOM = 0.90, 0.93, 0.05, 0.5, 0.10, 0.8
CSALADI_KAPU_MIN_N = 60


def rows(p: Path) -> list[dict]:
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


def load_items(*names: str) -> dict[str, dict]:
    meta = {}
    for n in names:
        for it in rows(F2A / f"items_{n}.jsonl"):
            meta[it["id"]] = {"split": it["split"], "gold": it["gold"], "x": it["gold"] is None,
                              "ketertelmu": bool(it.get("ketertelmu")), "family": it["family"], "group": it["group"],
                              "source": it.get("source"), "x_type": it.get("x_type"), "lang": it.get("lang")}
    return meta


def readout(name: str, ids: set[str]) -> dict[str, list[dict]]:
    """id → sorok; a jelenlegi itemekre szűrve, `label_logprobs`-szal."""
    by = defaultdict(list)
    for r in rows(F2R / f"{name}.jsonl"):
        if r["id"] in ids:
            r["label_logprobs"] = {lab: math.log(max(1e-12, r["probs"][lab])) for lab in r["labels"]}
            by[r["id"]].append(r)
    return by


def calibrated(by: dict, meta: dict, temp: float | None = None) -> tuple[dict, float]:
    """4-permutációs átlag a tanár saját temperature-jével: a val-on illesztve, vagy a megadott (val-on illesztett)
    értékkel, hogy a train-kiolvasás ne a vizsgált itemeken kalibrálódjon."""
    t = temp if temp is not None else fit_temperature([r for rs in by.values() for r in rs if r["perm"] == 0], meta)
    return arm_predictions("perm_avg", by, meta, {"temp": t}), t


def think_preds(by: dict) -> dict:
    """A gondolkodó minták empirikus eloszlása: opció-id → minták aránya (a hiányzó válasz nem szavaz)."""
    out = {}
    for iid, rs in by.items():
        c = Counter()
        for r in rs:
            if r["pred"] is not None:
                c[None if r["pred"] == "X" else r["order"][r["labels"].index(r["pred"])]] += 1
        n = len(rs)
        sc = {k: v / n for k, v in c.items()}
        if sc:
            pred = max(sc, key=lambda k: sc[k])
            out[iid] = (pred, sc[pred], sc)
        else:
            out[iid] = ("<hiányzik>", 0.0, {})
    return out


def l1_star(meta: dict) -> dict:
    val_ids = [i for i, m in meta.items() if m["split"] == "val"]
    by = readout("qwen_val", set(val_ids))
    val0 = [r for rs in by.values() for r in rs if r["perm"] == 0]
    temp, bias = fit_temperature(val0, meta), label_bias(val0)
    arms = {"nyers": {}, "temp": {"temp": temp}, "perm_avg": {"temp": temp}}
    arms |= {f"batch_{lam}": {"bias": bias, "lam": lam, "temp": temp} for lam in (0.5, 0.75, 1.0)}
    res = {}
    for name, prm in arms.items():
        pv = arm_predictions("batch" if name.startswith("batch") else name, by, meta, prm)
        t95, t90 = choose_tau(pv, meta, val_ids, 0.95), choose_tau(pv, meta, val_ids, 0.90)
        res[name] = {"tau95": t95, "tau90": t90, "val": metrics(pv, meta, val_ids, t95, BUKAS),
                     "val90": metrics(pv, meta, val_ids, t90, 0.88), "params": prm}
    best = max(res, key=lambda k: (res[k]["val"].get("besorolasi_lefedettseg", 0),
                                   res[k]["val90"].get("besorolasi_lefedettseg", 0), -res[k]["val"].get("ece", 1)))
    return {"temp": temp, "karok": res, "L1": best}


def layer_metrics(preds: dict, meta: dict, ids: list[str], key, tau: float) -> dict:
    g = defaultdict(list)
    for i in ids:
        g[key(meta[i])].append(i)
    return {k: metrics(preds, meta, v, tau, BUKAS) for k, v in sorted(g.items())}


def gate(tp: dict, bp: dict, meta: dict, ids: list[str]) -> dict:
    """Tanárkapu egy egységen: tanár-predikciók (tp) vs. L1★ (bp) ugyanazokon a pontozott itemeken."""
    # rendezett id-k és stabil rendezés: a kvantált bizalmú (gondolkodó) tanárnál a holtversenyek vödörhatára így
    # nem a halmaz futásonként változó bejárási sorrendjétől függ
    ids = sorted(i for i in ids if i in tp and i in bp and not meta[i]["ketertelmu"])
    if not ids:
        return {}
    acc_t = float(np.mean([tp[i][0] == meta[i]["gold"] for i in ids]))
    acc_b = float(np.mean([bp[i][0] == meta[i]["gold"] for i in ids]))
    conf = np.array([tp[i][1] for i in ids])
    ok = np.array([tp[i][0] == meta[i]["gold"] for i in ids], dtype=float)
    idx = np.argsort(conf, kind="stable")
    ece = float(sum(abs(ok[b].mean() - conf[b].mean()) * len(b) / len(ids) for b in np.array_split(idx, 15) if len(b)))
    xf = {}
    for t in sorted({meta[i]["x_type"] for i in ids if meta[i]["x"]}):
        xs = [i for i in ids if meta[i]["x"] and meta[i]["x_type"] == t]
        xf[t] = {"n": len(xs), "fedes": float(np.mean([tp[i][0] is None for i in xs]))}
    x_ok = all(v["fedes"] >= XFEDES_MIN for v in xf.values() if v["n"] >= 10)
    return {"n": len(ids), "top1_tanar": acc_t, "top1_L1": acc_b, "ece": ece, "x_fedes": xf,
            "atment": acc_t >= acc_b and ece <= ECE_MAX and x_ok,
            "feltetelek": {"top1": acc_t >= acc_b, "ece": ece <= ECE_MAX, "x": x_ok}}


def main() -> None:
    meta = load_items("val", "eval", "train", "gond_val", "zaj")
    out: dict = {}
    # 1. L1★
    l1 = l1_star(meta)
    best, prm = l1["L1"], l1["karok"][l1["L1"]]["params"]
    tau = l1["karok"][best]["tau95"]
    arm = "batch" if best.startswith("batch") else best
    out["L1"] = {"kar": best, "temp": l1["temp"], "tau95": tau,
                 "karok": {k: {"tau95": v["tau95"], "lef95": v["val"].get("besorolasi_lefedettseg"),
                               "lef90": v["val90"].get("besorolasi_lefedettseg"), "prec": v["val"].get("besorolasi_precizitas"),
                               "aurc": v["val"].get("aurc"), "ece": v["val"].get("ece"), "top1": v["val"].get("pontossag"),
                               "x_fedes": v["val"].get("x_fedes")} for k, v in l1["karok"].items()}}

    def base_preds(name: str, ids: set[str]) -> dict:
        return arm_predictions(arm, readout(name, ids), meta, prm)

    val_ids = {i for i, m in meta.items() if m["split"] == "val"}
    eval_ids = {i for i, m in meta.items() if m["split"] not in ("train", "val")}
    train_ids = {i for i, m in meta.items() if m["split"] == "train"}
    pv, pe, pt = base_preds("qwen_val", val_ids), base_preds("qwen_eval", eval_ids), base_preds("qwen_train", train_ids)
    # 2. rétegek
    out["retegek"] = {"split": layer_metrics(pe, meta, list(pe), lambda m: m["split"], tau),
                      "csalad_split": layer_metrics(pe, meta, list(pe), lambda m: f"{m['family']}|{m['split']}", tau)}
    # 3. családválasztás a train-en
    fam = {}
    for f, mt in layer_metrics(pt, meta, list(pt), lambda m: m["family"], tau).items():
        ids = [i for i in pt if meta[i]["family"] == f and not meta[i]["ketertelmu"]]
        plafon = 1 - float(np.mean([meta[i]["x"] for i in ids])) if ids else 0.0
        lef = mt.get("besorolasi_lefedettseg", 0.0)
        prec = mt.get("besorolasi_precizitas")
        fam[f] = {"n": mt.get("n"), "lef95": lef, "plafon": plafon, "prec": prec, "top1": mt.get("pontossag"),
                  "x_fedes": mt.get("x_fedes"), "plafon_kozeli": bool(plafon) and lef >= PLAFON_ARANY * plafon
                  and prec is not None and prec >= BUKAS}
    out["csaladvalasztas"] = {"plafon_kozeli": sorted(f for f, v in fam.items() if v["plafon_kozeli"]),
                              "csaladok": fam}
    # 4. tanárkapu
    gold_val = [i for i in val_ids if meta[i]["source"] != "szint03"]
    kapu = {}
    for t in ("gemma", "mistral", "qwen38"):  # a qwen38 a negyedik jelölt (Dani, 2026-10-11)
        by = readout(f"{t}_val", val_ids)
        if not by:
            continue
        tp, temp_t = calibrated(by, meta)
        groups = defaultdict(list)
        for i in gold_val:
            groups[meta[i]["group"]].append(i)
        fams = defaultdict(list)
        for i in gold_val:
            fams[meta[i]["family"]].append(i)
        kapu[t] = {"temp": temp_t, "osszes": gate(tp, pv, meta, gold_val),
                   "csoport": {g: gate(tp, pv, meta, ids) for g, ids in sorted(groups.items())},
                   "csalad_leiro": {f: gate(tp, pv, meta, ids) for f, ids in sorted(fams.items())
                                    if len(ids) >= CSALADI_KAPU_MIN_N}}
    gond_ids = set(readout("qwen_gond_val", val_ids))
    if gond_ids:
        tq = think_preds(readout("qwen_gond_val", gond_ids))
        groups = defaultdict(list)
        for i in gond_ids:
            groups[meta[i]["group"]].append(i)
        kapu["qwen_gondolkodo"] = {"osszes": gate(tq, pv, meta, sorted(gond_ids)),
                                   "csoport": {g: gate(tq, pv, meta, ids) for g, ids in sorted(groups.items())},
                                   "hianyzo_valasz": sum(tq[i][0] == "<hiányzik>" for i in gond_ids)}
    out["tanarkapu"] = kapu
    # 5. gépi zajbecslés
    zaj_ids = set(readout("qwen_gond_zaj", train_ids))
    if zaj_ids:
        # a Gemma temperature-je a val-on illesztett: a zaj-itemek goldja épp a vizsgálat tárgya
        gp, gemma_t = calibrated(readout("gemma_train", zaj_ids), meta, kapu.get("gemma", {}).get("temp"))
        tq = think_preds(readout("qwen_gond_zaj", zaj_ids))
        src = defaultdict(lambda: Counter())
        jeloltek = []  # a két olvasó zajjelöltjei: az MVP-ből kimaradnak (4.2)
        for i in zaj_ids:
            if meta[i]["ketertelmu"]:
                continue
            gold = meta[i]["gold"]
            votes = []
            if i in gp and gp[i][1] >= ZAJ_BIZALOM:
                votes.append(gp[i][0])
            if i in tq and tq[i][0] != "<hiányzik>":
                votes.append(tq[i][0])
            v3 = votes + ([pt[i][0]] if i in pt and pt[i][1] >= ZAJ_BIZALOM else [])
            s = src[meta[i]["source"]]
            s["n"] += 1
            jelolt = [k for k, c in Counter(votes).items() if c >= 2 and k != gold]
            if jelolt:
                jeloltek.append({"id": i, "source": meta[i]["source"], "family": meta[i]["family"], "gold": gold,
                                 "konszenzus": jelolt[0]})
            s["zaj_ket_olvaso"] += bool(jelolt)
            s["zaj_harom_olvaso"] += any(c >= 2 for k, c in Counter(v3).items() if k != gold)
        out["zajbecsles_gemma_temp"] = gemma_t
        with open(F2A / "zajjelolt.jsonl", "w", encoding="utf-8") as fh:
            for j in sorted(jeloltek, key=lambda j: j["id"]):
                fh.write(json.dumps(j, ensure_ascii=False) + "\n")
        out["zajbecsles"] = {k: {"n": v["n"], "arany": v["zaj_ket_olvaso"] / v["n"],
                                 "arany_L1_val": v["zaj_harom_olvaso"] / v["n"],
                                 "kimarad": v["zaj_ket_olvaso"] / v["n"] > ZAJ_KUSZOB} for k, v in sorted(src.items())}
    # 6. bázis-horgony
    with open(F2A / "horgony_qwen_L1.jsonl", "w", encoding="utf-8") as fh:
        for i, (_, _, sc) in sorted(pt.items()):
            fh.write(json.dumps({"id": i, "x_gold": meta[i]["x"], "eloszlas": {str(k): v for k, v in sc.items()}},
                                ensure_ascii=False) + "\n")
    (F2R / "f2_elemzes.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"L1": out["L1"]["kar"], "tau95": tau, "plafon_kozeli": out["csaladvalasztas"]["plafon_kozeli"][:40],
                      "kapu": {t: v["osszes"] for t, v in kapu.items()}, "zaj": out.get("zajbecsles")},
                     ensure_ascii=False, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
