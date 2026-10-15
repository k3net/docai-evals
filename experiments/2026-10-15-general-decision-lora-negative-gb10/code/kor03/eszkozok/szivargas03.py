"""03-as kör — szivárgás-audit, első (szöveges) menet (03-runbook 5.: szivárgás-audit; a bge-m3-as menet a Sparkon).

Minden train/val jelölt (F0 és szintetikus) állapotszövegét összeveti minden eval-réteggel: az F0-családok teszt-ID-je, a HO-rétegek (a KIE,
a TED HO-forrás és a 00/01 befagyasztott tesztjei), és a külső evalok (Belebele, SIB-200, LocalLLaMA, fastino).
Mérőszám (saját): **8-gram-átfedés** = a pool-item normalizált szó-8-gramjai közül hány szerepel bármely eval-item
szövegében (állapot + kérdés + opciók; kisbetű, csak szókarakterek). Kapu: ≥ 0,5 → az item kiesik a poolból
(közeli duplikátum); 0,2–0,5 → csak jelentjük.

  python3 kor03/eszkozok/szivargas03.py   → adat/f1/szivargas03.json + szivargas_kizart.jsonl
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]
EXP = ROOT.parent
sys.path.insert(0, str(HERE))
from kozos03 import from_00, from_01  # noqa: E402

F0, F1 = ROOT / "adat/f0", ROOT / "adat/f1"
N = 8
KAPU, JELEZ = 0.5, 0.2
EVAL_SPLITS = {"test-id", "ho-termek", "ho-routing", "ho-uj", "ho-forras", "eval-kulso"}
ITEMS_00 = [EXP / "adat/f1" / f"items_{s}.jsonl" for s in ("T-belso", "T-szallito", "T-kozeli", "T-tavoli")] + \
           [EXP / "adat/k00b/meres/items_T-ujszallito.jsonl"]
ITEMS_01 = [EXP / "kor01/adat/items_teszt.jsonl", EXP / "kor01/adat/f1s/items_katalogus.jsonl"]
TOKEN = re.compile(r"\w+")


def text(r: dict) -> str:
    """Az állapot; ha az túl rövid (kevesebb mint N szó), a kérdés és az opciók is. A fix opciólisták (törvénycímek,
    EuroVoc- és CPV-nevek) és a családonként azonos kérdésszöveg különben minden itemben átfedést adnának."""
    st = r.get("state") or ""
    if len(TOKEN.findall(st)) >= N:
        return st
    return " ".join([st, r["question"]] + [o["text"] for o in r["options"]])


def frac_in(g: np.ndarray, arr: np.ndarray) -> float:
    idx = np.minimum(np.searchsorted(arr, g), len(arr) - 1)
    return float((arr[idx] == g).mean())


def grams(s: str) -> np.ndarray:
    t = TOKEN.findall(s.lower())
    if len(t) < N:
        return np.array([hash(" ".join(t))], dtype=np.int64) if t else np.array([], dtype=np.int64)
    return np.fromiter((hash(" ".join(t[i:i + N])) for i in range(len(t) - N + 1)), dtype=np.int64)


def eval_items():
    for p in sorted(F0.glob("*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["split"] in EVAL_SPLITS:
                yield r
    for paths, fn in ((ITEMS_00, from_00), (ITEMS_01, from_01)):
        for p in paths:
            if p.exists():
                for line in p.read_text(encoding="utf-8").splitlines():
                    yield fn(json.loads(line))


def main() -> None:
    by_fam: dict[str, list[np.ndarray]] = defaultdict(list)
    n_eval = Counter()
    for r in eval_items():
        by_fam[f"{r['family']}|{r['split']}"].append(grams(text(r)))
        n_eval[f"{r['family']}|{r['split']}"] += 1
    fam_arr = {k: np.unique(np.concatenate(v)) for k, v in by_fam.items() if v}
    all_arr = np.unique(np.concatenate(list(fam_arr.values())))
    print(f"eval: {sum(n_eval.values())} item, {len(fam_arr)} réteg, {len(all_arr)} egyedi 8-gram", flush=True)
    # minden train/val jelölt (nem csak a pool): így a keverő eleve a tiszta jelöltekből válogat
    files = sorted(F0.glob("*.jsonl"))
    szint = F1 / "szint"
    if szint.exists():
        files += [p for p in sorted(szint.glob("*.jsonl")) if p.name != "forras_bekezdesek.jsonl"]
    pool = [r for p in files for r in map(json.loads, p.read_text(encoding="utf-8").splitlines())
            if r["split"] in ("train", "val")]
    kizart, rep, hist = [], defaultdict(Counter), Counter()
    for r in pool:
        g = np.unique(grams(text(r)))
        if not len(g):
            continue
        frac = frac_in(g, all_arr)
        hist[min(int(frac * 10), 9)] += 1
        if frac < JELEZ:
            continue
        best = max(fam_arr, key=lambda k: frac_in(g, fam_arr[k]))
        bf = frac_in(g, fam_arr[best])
        key = "kizart" if frac >= KAPU else "jelzett"
        rep[f"{r['family']} → {best}"][key] += 1
        if frac >= KAPU:
            kizart.append({"id": r["id"], "family": r["family"], "atfedes": round(frac, 3), "reteg": best,
                           "reteg_atfedes": round(bf, 3)})
    (F1 / "szivargas_kizart.jsonl").write_text("".join(json.dumps(k, ensure_ascii=False) + "\n" for k in kizart),
                                              encoding="utf-8")
    out = {"n_gram": N, "kapu": KAPU, "jelzes": JELEZ, "pool_item": len(pool), "kizart": len(kizart),
           "atfedes_hisztogram_tized": {f"{k / 10:.1f}–{(k + 1) / 10:.1f}": v for k, v in sorted(hist.items())},
           "parok": {k: dict(v) for k, v in sorted(rep.items(), key=lambda kv: -sum(kv[1].values()))},
           "eval_retegek": dict(n_eval)}
    (F1 / "szivargas03.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "eval_retegek"}, ensure_ascii=False, indent=1)[:3000])


if __name__ == "__main__":
    main()
