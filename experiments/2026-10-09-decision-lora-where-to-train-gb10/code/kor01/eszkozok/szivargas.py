"""Szivárgás-audit (01-runbook 4. pont; a 00 tanulsága: a ténylegesen használt tanítóhalmaz ellen, nem a generátor
saját újraépített train-je ellen).

A val, a teszt és a T-katalógus minden itemjére:
  * `gold_nev_a_trainben`: a gold eszköz neve szerepel-e opcióként a train-ben (a BFCL-en ez a meglévő
    `train_eszkoznev_atfedes`; itt minden rétegre egységesen);
  * `gold_max_cos`: a gold eszköz („név: leírás”) bge-m3 koszinusza a legközelebbi train-eszközhöz;
  * `keres_duplikatum`: a normalizált kérés szó szerint szerepel-e a train-ben;
  * `keres_max_cos`: a kérés bge-m3 koszinusza a legközelebbi train-kéréshez.
Kapu itt nincs: a küszöböket (T-új-eszköz szűrése, közeli kérés-duplikátumok) a v1 rögzíti ennek ismeretében.

  python3 kor01/eszkozok/szivargas.py [--train-extra kor01/adat/f1s/items_eu180k.jsonl]
      → eredmenyek/F1S/szivargas_itemek.jsonl + szivargas.json

  --uj-eszkoz-x: a T-új-eszköz réteg tagsága (01 v1, 4. pont) a BFCL és a When2Call teszt-itemjeire, a tényleges
  train ellen (--train-extra-val) → eredmenyek/F1S/uj_eszkoz.jsonl (+ .json összesítő)
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kozos01 import A, F1S, R, norm, read_jsonl, write_json, write_jsonl  # noqa: E402
from common import BGE_M3  # noqa: E402

THRESH = (0.85, 0.90, 0.95)
UJ_COS = 0.85  # a T-új-eszköz küszöbe (v1, 4. pont)


class Embedder:  # a 00 `jeloltek.py`-jáé (CLS + L2-normálás)
    def __init__(self):
        from transformers import AutoModel, AutoTokenizer

        self.tok = AutoTokenizer.from_pretrained(BGE_M3)
        self.model = AutoModel.from_pretrained(BGE_M3, dtype=torch.float16).cuda().eval()

    @torch.inference_mode()
    def __call__(self, texts: list[str], max_len: int = 256, bs: int = 64) -> torch.Tensor:
        out = []
        for b in range(0, len(texts), bs):
            enc = self.tok(texts[b:b + bs], padding=True, truncation=True, max_length=max_len, return_tensors="pt").to("cuda")
            h = self.model(**enc).last_hidden_state[:, 0]
            out.append(torch.nn.functional.normalize(h.float(), dim=-1))
        return torch.cat(out)


def max_cos(q: torch.Tensor, ref: torch.Tensor, chunk: int = 2048) -> np.ndarray:
    return torch.cat([(q[i:i + chunk] @ ref.T).max(dim=1).values for i in range(0, len(q), chunk)]).cpu().numpy()


def tool_text(o: dict) -> str:
    return f"{o['name']}: {' '.join((o.get('description') or '').split())}"


def uj_eszkoz_x(train: list[dict], emb: "Embedder") -> None:
    """A T-új-eszköz réteg tagsága (`t_uj_eszkoz`) a BFCL és a When2Call minden teszt-itemjére, a tényleges train
    ellen (a train-extrával): nem-X itemnél a gold, X itemnél minden opció neve hiányzik a train eszköznevei közül,
    és a koszinusza a legközelebbi train-eszközhöz < UJ_COS."""
    tr_tools = {tool_text(o): o["name"] for it in train for o in it["options"]}
    tr_names = set(tr_tools.values())
    E_tool = emb(list(tr_tools))
    its = [it for it in read_jsonl(A / "items_teszt.jsonl") if it["forras"].startswith("bfcl") or it["forras"] == "w2c_teszt"]
    nezett = [[o for o in it["options"] if it["gold"] is None or o["id"] == it["gold"]] for it in its]
    opts = [(k, o) for k, os_ in enumerate(nezett) for o in os_]
    cos = max_cos(emb([tool_text(o) for _, o in opts]), E_tool) if opts else np.array([])
    per = defaultdict(list)
    for (k, o), c in zip(opts, cos):
        per[k].append((o["name"] in tr_names, float(c)))
    rows = [{"id": it["id"], "forras": it["forras"], "x": it["gold"] is None, "n_nezett": len(per[k]),
             "t_uj_eszkoz": bool(per[k]) and all(not nm and c < UJ_COS for nm, c in per[k]),
             "max_cos": round(max((c for _, c in per[k]), default=0.0), 4)} for k, it in enumerate(its)]
    write_jsonl(R / "F1S/uj_eszkoz.jsonl", rows)
    by = defaultdict(lambda: [0, 0])
    for r in rows:
        key = f"{r['forras']}{':X' if r['x'] else ''}"
        by[key][0] += 1
        by[key][1] += r["t_uj_eszkoz"]
    summ = {"kuszob": UJ_COS, "train_itemek": len(train), "itemek": len(rows), "t_uj_eszkoz": sum(r["t_uj_eszkoz"] for r in rows),
            "ebbol_x": sum(r["t_uj_eszkoz"] and r["x"] for r in rows), "forrasonkent": {f: {"n": a, "uj": b} for f, (a, b) in by.items()}}
    write_json(R / "F1S/uj_eszkoz.json", summ)
    print(summ)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-extra", action="append", default=[])
    ap.add_argument("--uj-eszkoz-x", action="store_true")
    args = ap.parse_args()
    train = read_jsonl(A / "items_train.jsonl")
    for f in args.train_extra:
        train += read_jsonl(Path(f))
    if args.uj_eszkoz_x:
        uj_eszkoz_x(train, Embedder())
        return
    evals = {"val": read_jsonl(A / "items_val.jsonl"), "teszt": read_jsonl(A / "items_teszt.jsonl"),
             "katalogus": read_jsonl(F1S / "items_katalogus.jsonl")}
    emb = Embedder()
    tr_tools = {tool_text(o): o["name"] for it in train for o in it["options"]}
    tr_names = set(tr_tools.values())
    tr_req = sorted({norm(it["request"]) for it in train})
    tr_req_set = set(tr_req)
    E_tool = emb(list(tr_tools))
    E_req = emb([it["request"] for it in train])
    rows, summ = [], {"train_itemek": len(train), "train_eszkozok": len(tr_tools), "kuszobok": THRESH}
    for split, items in evals.items():
        golds = [next((o for o in it["options"] if o["id"] == it["gold"]), None) for it in items]
        gi = [k for k, g in enumerate(golds) if g is not None]
        gcos = np.full(len(items), np.nan)
        if gi:
            gcos[gi] = max_cos(emb([tool_text(golds[k]) for k in gi]), E_tool)
        rcos = max_cos(emb([it["request"] for it in items]), E_req)
        by_src = defaultdict(lambda: defaultdict(int))
        for k, it in enumerate(items):
            g = golds[k]
            r = {"id": it["id"], "split": split, "forras": it["forras"],
                 "gold_nev_a_trainben": bool(g and g["name"] in tr_names),
                 "gold_max_cos": None if np.isnan(gcos[k]) else round(float(gcos[k]), 4),
                 "keres_duplikatum": norm(it["request"]) in tr_req_set, "keres_max_cos": round(float(rcos[k]), 4)}
            rows.append(r)
            s = by_src[it["forras"]]
            s["n"] += 1
            s["gold_nev_a_trainben"] += r["gold_nev_a_trainben"]
            s["keres_duplikatum"] += r["keres_duplikatum"]
            for t in THRESH:
                s[f"gold_cos>={t}"] += r["gold_max_cos"] is not None and r["gold_max_cos"] >= t
                s[f"keres_cos>={t}"] += r["keres_max_cos"] >= t
        summ[split] = {k: dict(v) for k, v in by_src.items()}
    write_jsonl(R / "F1S/szivargas_itemek.jsonl", rows)
    write_json(R / "F1S/szivargas.json", summ)
    print(summ)


if __name__ == "__main__":
    main()
