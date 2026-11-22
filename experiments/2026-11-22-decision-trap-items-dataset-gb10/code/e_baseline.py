"""E irány — az alapmérések összesítése (terv 10. pont): a `baseline.py score` minden futásra, a thinking-kimenetek leíró adatai,
és a szöveges alapmodell (karakter TF-IDF 3–5 + logisztikus regresszió) a címkére. → publikacio/E/baseline/summary.{json,md}

Szöveges alapmodell: natural és interpretation: train → test; minimal_pairs: 5-szörös keresztvalidáció forgatókönyvpár
(scenario_group) szerint csoportosítva. A calc_traps minden tétele MATCH, ott a címke szövegből nem jósolható (nincs mit jósolni).
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from argparse import Namespace
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
# a kiadott csomagban a szkript a code/ alatt áll, mellette a data/ és a baseline/; a kutatási fában a publikacio/E a gyökér
E = HERE.parent if (HERE.parent / "data").exists() else HERE.parents[1] / "publikacio/E"
sys.path[:0] = [str(E / "code")]
import baseline as B  # noqa: E402


def szoveg(r):
    return r["text"] + "\n" + r["question"] + "\n" + "\n".join(o["text"] for o in r["options"])


def tfidf():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import GroupKFold
    from sklearn.pipeline import make_pipeline

    mk = lambda: make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, max_features=200_000, sublinear_tf=True, dtype=np.float32),  # noqa: E731
                               LogisticRegression(C=10.0, max_iter=400, class_weight="balanced"))
    out = {}
    for k in ("natural", "interpretation"):
        tr, te = B.jsonl(str(E / f"data/{k}/train.jsonl")), B.jsonl(str(E / f"data/{k}/test.jsonl"))
        m = mk().fit([szoveg(r) for r in tr], [r["label"] for r in tr])
        P = m.predict_proba([szoveg(r) for r in te])
        y = np.array([r["label"] for r in te])
        pr = m.classes_[P.argmax(1)]
        o = {"n": len(te), "accuracy": float((pr == y).mean()), "majority": float(max(Counter(y).values()) / len(y)),
             "by_label": {c: float((pr[y == c] == c).mean()) for c in m.classes_}}
        if len(m.classes_) == 2:
            o["auroc"] = float(roc_auc_score(y == m.classes_[1], P[:, 1]))
        if k == "natural":
            fam = np.array([r["family"] for r in te])
            o["by_family_label"] = {f"{f}:{c}": float((pr[(fam == f) & (y == c)] == c).mean()) for f in sorted(set(fam)) for c in m.classes_}
        out[k] = o
    its = B.jsonl(str(E / "data/minimal_pairs/test.jsonl"))
    X, y, g = np.array([szoveg(r) for r in its], dtype=object), np.array([r["label"] == "MATCH" for r in its]), np.array([r["scenario_group"] for r in its])
    p = np.zeros(len(its))
    for a, b in GroupKFold(5).split(X, y, g):
        p[b] = mk().fit(list(X[a]), y[a]).predict_proba(list(X[b]))[:, 1]
    out["minimal_pairs"] = {"n": len(its), "accuracy": float(((p > 0.5) == y).mean()), "majority": 0.5, "auroc": float(roc_auc_score(y, p)), "cv": "5-fold, grouped by scenario_group (matched scenario pairs)"}
    return out


def main():
    res = {"runs": {}, "think": {}}
    for p in sorted((E / "baseline/raw").glob("*.jsonl")):
        k = p.name.split(".")[0]
        with contextlib.redirect_stdout(io.StringIO()):
            res["runs"][p.stem] = B.score(Namespace(items=str(E / f"data/{k}/test.jsonl"), pred=str(p)))
        rows = B.jsonl(str(p))
        if ".think" in p.name:
            t = [r["completion_tokens"] for r in rows if r.get("completion_tokens")]
            res["think"][p.stem] = {"finish": dict(Counter(r.get("finish") for r in rows)), "completion_tokens_median": float(np.median(t)), "completion_tokens_p95": float(np.percentile(t, 95))}
        its = {r["id"]: r for r in B.jsonl(str(E / f"data/{k}/test.jsonl"))}
        if k in ("minimal_pairs", "interpretation"):  # egység / pár szint: a hiányos tagra adott válasz, és a pár mindkét tagja helyes-e
            fr = rows[0]["frame"]
            ok = {r["id"]: r["pred"] == B.gold(its[r["id"]], fr) for r in rows}
            key = "pair_id" if k == "minimal_pairs" else "unit_id"
            u = {}
            for r in rows:
                u.setdefault(its[r["id"]][key], []).append(ok[r["id"]])
            hi = [r for r in rows if not its[r["id"]]["has_deciding_signal"]]
            c = Counter("option" if (r["pred"] or "-") in B.LETTERS else str(r["pred"]) for r in hi)
            res["runs"][p.stem]["undecidable_member"] = {"n": len(hi), "answers": dict(c), "chose_option": c["option"] / len(hi), "chose_option_ci95": B.wilson(c["option"], len(hi))}
            res["runs"][p.stem]["all_members_correct"] = {"n": len(u), "rate": float(np.mean([all(v) for v in u.values()]))}
    res["text_baseline"] = tfidf()
    (E / "baseline/summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    pc = lambda x: f"{100 * x:.1f}"  # noqa: E731
    L = ["# Baseline summary (Qwen3.6-35B-A3B FP8, one read per item)", "", "| run | n | accuracy [95%] | wrong option | wrong exit | no answer |", "|---|---:|---:|---:|---:|---:|"]
    for k, r in res["runs"].items():
        a = r["by"]["all"]
        L.append(f"| {k} | {a['n']} | {pc(a['accuracy'])} [{pc(a['accuracy_ci95'][0])}; {pc(a['accuracy_ci95'][1])}] | {pc(a['wrong_option'])} | {pc(a['wrong_exit'])} | {pc(a['no_answer'])} |")
    L += ["", "## By cell", ""]
    for k, r in res["runs"].items():
        L.append(f"- **{k}**: " + "; ".join(f"{c} {pc(v['accuracy'])} (wrong option {pc(v['wrong_option'])}, n {v['n']})" for c, v in r["by"].items() if c != "all" and not c.startswith("lang")))
        for x in ("undecidable_member", "all_members_correct"):
            if x in r:
                L.append(f"  - {x}: {json.dumps(r[x], ensure_ascii=False)}")
    L += ["", "## Thinking runs", ""] + [f"- {k}: {json.dumps(v)}" for k, v in res["think"].items()]
    L += ["", "## Text-only baseline (label from surface text)", ""] + [f"- {k}: {json.dumps(v, ensure_ascii=False)}" for k, v in res["text_baseline"].items()]
    (E / "baseline/summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
