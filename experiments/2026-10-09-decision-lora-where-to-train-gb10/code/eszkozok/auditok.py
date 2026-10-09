"""F1-auditok a befagyasztás előtt (runbook 4.5–4.7).

  shortcut  — (measurement-host vagy laptop) csak METAADATOKON tanított logisztikus osztályozó próbálja
              megjósolni az X / nem-X címkét; 5-szörös CV AUC. Kapu: ≤ 0,55. Mellé a gold
              pozíciójának egyenletessége (χ²) a tárolt sorrendben.
  nehezseg  — alanyfüggetlen nehézségi mércék rétegenként (BM25 top-1 gold-arány, testvér a listán,
              BM25-margó), a célsávokkal összevetve.
  valoszeru — (CSAK LAPTOPON) 2000 valós <tenant>-tételsor vs 2000 szintetikus sor: karakter 3–5-gram
              logisztikus kétmintás osztályozó, CV AUC, és a leginkább elkülönítő n-gramok
              MINTÁZAT-TÍPUSRA összesítve. A valós szöveg és n-gram nem kerül kimenetbe.

Példa:
  python3 eszkozok/auditok.py shortcut --gen adat/f1 --out eredmenyek/F1/audit
  .venv/bin/python eszkozok/auditok.py valoszeru --gen adat/f1 --out _belso/valoszeruseg   (laptop)
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import EXP, read_jsonl, write_json  # noqa: E402

SPLITS = ["train", "val-belso", "val-szallito", "T-belso", "T-szallito", "T-kozeli", "T-tavoli", "T-ujszallito"]  # 00b: 15. pont
# A célsávok a pilot (seed 101) alapján rögzítve, az F1 előtt (runbook 4.5; 2026-10-03). Sodródásőr a pilot és a
# végleges generálás közt, és a lexikailag triviális / visszakeresési szemét rétegek ellen. Az eredeti
# (0,50–0,75; ≥ 0,40; ≤ 0,15) sávot a pilot a margón mindenhol átlépte; a K0b-2 szerint a döntés nehézsége az X-en
# múlik, nem a lexikai margón.
CELSAV = {"bm25_top1_gold": (0.40, 0.85), "testver_a_listan_min": 0.40, "bm25_margo_median_max": 0.40}


def _p(p: str) -> Path:
    q = Path(p)
    return q if q.is_absolute() else EXP / q


def load_items(gen: Path, splits: list[str] | None = None) -> list[dict]:
    out = []
    for sp in splits or SPLITS:
        f = gen / f"items_{sp}.jsonl"
        if f.exists():
            out += read_jsonl(f)
    return out


def meta_features(it: dict) -> list[float]:
    """Csak szerkezeti metaadat — szemantika nélkül."""
    opts = it["options"]
    paths = Counter(o["path"] for o in opts)
    roots = Counter(o["path"].split(" › ")[0] for o in opts)
    lens = [len(o["text"]) for o in opts]
    return [len(opts), len(paths), len(roots), max(paths.values()) / len(opts), max(roots.values()) / len(opts),
            statistics.mean(lens), statistics.pstdev(lens), len(it["context"]["sor"]),
            float(it["context"]["sor"].isupper()), float(bool(re.match(r"^\d{5,}", it["context"]["sor"])))]


def cmd_shortcut(args) -> None:
    import numpy as np
    from scipy.stats import chisquare
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    items = load_items(_p(args.gen), args.splits.split(",") if args.splits else None)
    X = np.array([meta_features(i) for i in items])
    y = np.array([i["gold"] is None for i in items], dtype=int)
    auc = cross_val_score(make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)), X, y, cv=5, scoring="roc_auc")
    pos = Counter()
    for i in items:
        if i["gold"] is not None:
            pos[[o["id"] for o in i["options"]].index(i["gold"])] += 1
    obs = [pos[k] for k in range(max(pos) + 1)] if pos else []
    # várt: az opciószám szerinti egyenletes eloszlás keveréke
    exp = [0.0] * len(obs)
    for i in items:
        if i["gold"] is not None:
            for k in range(len(i["options"])):
                exp[k] += 1 / len(i["options"])
    chi = chisquare(obs, f_exp=[e * sum(obs) / sum(exp) for e in exp]) if obs else None
    res = {"n": len(items), "x_arany": float(y.mean()), "x_vs_nemx_cv_auc": float(auc.mean()), "auc_folds": auc.tolist(),
           "kapu_auc_max": 0.55, "kapu_ok": bool(auc.mean() <= 0.55),
           "gold_pozicio": obs, "gold_pozicio_chi2_p": float(chi.pvalue) if chi else None}
    write_json(_p(args.out) / "shortcut.json", res)
    print(json.dumps(res, ensure_ascii=False))


FEATURE_NAMES = ["opcioszam", "utvonalszam", "gyokerszam", "max_utvonal_arany", "max_gyoker_arany", "szoveghossz_atlag",
                 "szoveghossz_szoras", "sorhossz", "nagybetus", "kodelotag"]


def cmd_shortcut_diag(args) -> None:
    """A shortcut-audit bontása: jellemzőnkénti egyváltozós AUC (X vs nem-X), és a teljes AUC X-fajtánként
    (mindegyik X-fajta a nem-X-ek ellen). Megmutatja, melyik jellemző és melyik X-fajta árulkodik."""
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import cross_val_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    items = load_items(_p(args.gen))
    X = np.array([meta_features(i) for i in items])
    y = np.array([i["gold"] is None for i in items], dtype=int)
    kind = np.array([i["meta"].get("x_fajta") or "-" for i in items])
    res = {"egyvaltozos_auc": {n: round(float(roc_auc_score(y, X[:, k])), 4) for k, n in enumerate(FEATURE_NAMES)},
           "atlag_x_vs_nemx": {n: [round(float(X[y == 1, k].mean()), 3), round(float(X[y == 0, k].mean()), 3)]
                               for k, n in enumerate(FEATURE_NAMES)},
           "x_fajtankent": {}}
    for kf in sorted(set(kind) - {"-"}):
        m = (kind == kf) | (y == 0)
        auc = cross_val_score(make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)), X[m], (kind[m] == kf).astype(int),
                              cv=5, scoring="roc_auc")
        res["x_fajtankent"][kf] = {"n": int((kind == kf).sum()), "cv_auc": round(float(auc.mean()), 4)}
    write_json(_p(args.out) / "shortcut_diag.json", res)
    print(json.dumps(res, ensure_ascii=False, indent=1))


def cmd_nehezseg(args) -> None:
    rep = json.load(open(_p(args.gen) / "osszeallit_riport.json"))["splitek"]
    out = {}
    for sp, r in rep.items():
        if not r:
            continue
        top1 = r["bm25_top1_gold_arany_nem_x"]
        tv, mg = r["testver_a_listan_arany_nem_x"], r["bm25_margo_median"]
        ok = (CELSAV["bm25_top1_gold"][0] <= top1 <= CELSAV["bm25_top1_gold"][1] and tv >= CELSAV["testver_a_listan_min"]
              and mg <= CELSAV["bm25_margo_median_max"])
        out[sp] = {"n": r.get("n"), "bm25_top1_gold": top1, "testver_a_listan": tv, "bm25_margo_median": mg, "savban": ok}
    kapu = all(v["savban"] for k, v in out.items() if k != "train")
    write_json(_p(args.out) / "nehezseg.json", {"celsavok": CELSAV, "retegek": out, "kapu_ok_val_teszt": kapu})
    print(json.dumps(out, ensure_ascii=False))


PATTERN = {
    "nagybetus": re.compile(r"^[^a-záéíóöőúüű]*$"), "kiszereles": re.compile(r"\d+\s*[x×*/]\s*\d*|krt|karton", re.I),
    "kod_elotag": re.compile(r"^\s*([A-Z]{0,3}\d{3,}|\d+[-/]\d+)\b"), "zarojel": re.compile(r"[()\[\]]"),
    "szazalek": re.compile(r"%"), "pont_rovidites": re.compile(r"\b\w{1,6}\."), "szamjegy": re.compile(r"\d"),
}


def ngram_type(g: str) -> str:
    """Egy elkülönítő n-gram absztrakt mintázat-típusa (a szöveg maga nem kerül ki)."""
    if re.search(r"\d", g):
        return "szam/mertekegyseg"
    if g.strip() != g:
        return "szohatar"
    if re.search(r"[.]", g):
        return "rovidites-pont"
    if g.isupper():
        return "nagybetus"
    if re.search(r"[áéíóöőúüű]", g.lower()):
        return "ekezetes"
    return "betu"


def cmd_valoszeru(args) -> None:
    import subprocess

    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score

    gen = Path(args.gen) if Path(args.gen).is_absolute() else Path(__file__).resolve().parent.parent / args.gen
    synth = [r["text"] for r in read_jsonl(gen / "s4_sorok.jsonl")]
    # a valós oldal ügyféladat (CSAK LAPTOPON): a tenant tükréből kinyert tételsor-szövegek, soronként egy;
    # a kinyerő lekérdezés a publikus csomagban nincs benne
    real = (Path(__file__).resolve().parent.parent / "_belso/valos_tetelsorok.txt").read_text(encoding="utf-8").splitlines()
    rng = random.Random(9)
    real = rng.sample(real, min(2000, len(real)))
    synth = rng.sample(synth, min(2000, len(synth)))
    texts, y = real + synth, np.array([0] * len(real) + [1] * len(synth))
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, lowercase=False)
    X = vec.fit_transform(texts)
    clf = LogisticRegression(max_iter=3000, C=1.0)
    auc = cross_val_score(clf, X, y, cv=5, scoring="roc_auc")
    clf.fit(X, y)
    names = vec.get_feature_names_out()
    order = np.argsort(clf.coef_[0])
    top_real = Counter(ngram_type(names[i]) for i in order[:200])
    top_synth = Counter(ngram_type(names[i]) for i in order[-200:])
    pat = {k: {"valos": round(sum(bool(p.search(t)) for t in real) / len(real), 3),
               "szintetikus": round(sum(bool(p.search(t)) for t in synth) / len(synth), 3)} for k, p in PATTERN.items()}
    hossz = {"valos_median": statistics.median(len(t) for t in real), "szintetikus_median": statistics.median(len(t) for t in synth)}
    res = {"cv_auc": float(auc.mean()), "kuszob_iteraciohoz": 0.95, "iteracio_kell": bool(auc.mean() > 0.95),
           "elkulonito_ngram_tipusok_valos_oldal": dict(top_real), "elkulonito_ngram_tipusok_szintetikus_oldal": dict(top_synth),
           "mintazat_arany": pat, "hossz": hossz}
    out = Path(args.out) if Path(args.out).is_absolute() else Path(__file__).resolve().parent.parent / args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "valoszeruseg.json").write_text(json.dumps(res, ensure_ascii=False, indent=2))
    print(json.dumps(res, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["shortcut", "shortcut-diag", "nehezseg", "valoszeru"])
    ap.add_argument("--gen", default="adat/f1")
    ap.add_argument("--out", default="eredmenyek/F1/audit")
    ap.add_argument("--splits", default="", help="shortcut: csak ezek a splitek (vesszős lista; üres = mind)")
    args = ap.parse_args()
    {"shortcut": cmd_shortcut, "shortcut-diag": cmd_shortcut_diag, "nehezseg": cmd_nehezseg, "valoszeru": cmd_valoszeru}[args.cmd](args)


if __name__ == "__main__":
    main()
