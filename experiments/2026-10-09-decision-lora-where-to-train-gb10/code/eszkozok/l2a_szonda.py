"""L2a — tanult címkesorok a döntési pozíció rejtett állapotán (runbook 5., H4).

Multinomiális logisztikus fej L2-büntetéssel a HF-kiolvasó rejtett állapot-cache-én (hf_kiolvaso.py
--hidden-layers/--hidden-out: layer{i}.pt + index.jsonl, a kimeneti sorokkal azonos sorrendben).
- Osztályok: a pozíciócímkék (A…J, X); a sorban nem szereplő címkék maszkolva.
- Cél: az L3-tréninggel azonos (tren_lora.build_examples): gold one-hot, kétértelmű itemnél egyenletes eloszlás a
  meta.soft tagjain.
- Jellemzők: a train-átlaggal és -szórással standardizálva.
- λ: a val NLL-jén választva (a pontozott, nem kétértelmű val-itemek 0. permutációja).
- Kimenet: a hf_kiolvaso sorformátuma (label_logprobs = a fej maszkolt log-softmaxa), így az elemzes.py L1-karjai
  (temp, perm_avg) változtatás nélkül futnak rajta.

  fit    — train → λ-választás a val-on → fej mentése (fej.pt) + val-kimenet (val.jsonl)
  apply  — mentett fej → új split (az F4-ben a teszt)

  python3 eszkozok/l2a_szonda.py fit --layer 27 --items adat/f1 \\
      --train-rows eredmenyek/F2/hf_train.jsonl --train-hidden cache/hidden/train \\
      --val-rows eredmenyek/F2/hf_val.jsonl --val-hidden cache/hidden/val --out eredmenyek/F2/l2a_L27
  python3 eszkozok/l2a_szonda.py apply --head eredmenyek/F2/l2a_L27/fej.pt \\
      --rows eredmenyek/F4/hf_teszt.jsonl --hidden cache/hidden/teszt --out eredmenyek/F4/l2a_L27_teszt.jsonl
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import EXP, read_jsonl, write_json, write_jsonl  # noqa: E402

LABELS = list("ABCDEFGHIJ") + ["X"]
LAMBDAS = [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1]


def _p(p: str) -> Path:
    q = Path(p)
    return q if q.is_absolute() else EXP / q


def load(rows_path: Path, hidden_dir: Path, layer: int) -> tuple[list[dict], torch.Tensor]:
    rows = read_jsonl(rows_path)
    idx = read_jsonl(hidden_dir / "index.jsonl")
    h = torch.load(hidden_dir / f"layer{layer}.pt").float()
    if not (len(idx) == len(rows) == h.shape[0]
            and all(a["id"] == b["id"] and a["perm"] == b["perm"] for a, b in zip(idx, rows))):
        raise SystemExit(f"a sorok és a rejtett állapotok nem illeszkednek: {rows_path}, {hidden_dir}")
    return rows, h


def load_items(items_dir: Path) -> dict[str, dict]:
    return {it["id"]: it for f in sorted(items_dir.glob("items_*.jsonl")) if ".pre_atnezes" not in f.name
            for it in read_jsonl(f)}


def mask_target(rows: list[dict], items: dict[str, dict]) -> tuple[torch.Tensor, torch.Tensor]:
    m = torch.zeros(len(rows), len(LABELS), dtype=torch.bool)
    t = torch.zeros(len(rows), len(LABELS))
    for k, r in enumerate(rows):
        for lab in r["labels"]:
            m[k, LABELS.index(lab)] = True
        soft = (items.get(r["id"], {}).get("meta") or {}).get("soft")
        if soft:
            members = [r["labels"][r["order"].index(o)] for o in soft if o in r["order"]]
            for lab in members:
                t[k, LABELS.index(lab)] = 1.0 / len(members)
        else:
            t[k, LABELS.index(r["gold_label"])] = 1.0
    return m, t


def log_probs(x: torch.Tensor, m: torch.Tensor, w: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    z = (x @ w.T + b).masked_fill(~m, float("-inf"))
    return torch.log_softmax(z, -1)


def fit_head(x: torch.Tensor, m: torch.Tensor, t: torch.Tensor, lam: float, iters: int) -> tuple[torch.Tensor, torch.Tensor]:
    w = torch.zeros(len(LABELS), x.shape[1], requires_grad=True)
    b = torch.zeros(len(LABELS), requires_grad=True)
    opt = torch.optim.LBFGS([w, b], lr=1.0, max_iter=iters, line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        lp = log_probs(x, m, w, b).masked_fill(~m, 0.0)
        loss = -(t * lp).sum(-1).mean() + lam * (w ** 2).sum()
        loss.backward()
        return loss

    opt.step(closure)
    return w.detach(), b.detach()


def to_rows(rows: list[dict], lp: torch.Tensor, layer: int, lam: float) -> list[dict]:
    out = []
    for k, r in enumerate(rows):
        llp = {lab: float(lp[k, LABELS.index(lab)]) for lab in r["labels"]}
        probs = {lab: math.exp(v) for lab, v in llp.items()}
        pred = max(probs, key=lambda lab: probs[lab])
        out.append({"id": r["id"], "split": r.get("split"), "perm": r["perm"], "move_none": r.get("move_none", False),
                    "order": r["order"], "labels": r["labels"], "gold_label": r["gold_label"], "pred": pred,
                    "conf": probs[pred], "probs": probs, "label_logprobs": llp, "label_mass": 1.0,
                    "engine": "hf-l2a", "layer": layer, "lam": lam})
    return out


def cmd_fit(args) -> None:
    items = load_items(_p(args.items))
    tr_rows, tr_h = load(_p(args.train_rows), _p(args.train_hidden), args.layer)
    va_rows, va_h = load(_p(args.val_rows), _p(args.val_hidden), args.layer)
    mu, sd = tr_h.mean(0), tr_h.std(0).clamp_min(1e-3)
    xtr, xva = (tr_h - mu) / sd, (va_h - mu) / sd
    mtr, ttr = mask_target(tr_rows, items)
    mva, _ = mask_target(va_rows, items)
    sel = [k for k, r in enumerate(va_rows) if r["perm"] == 0 and not items[r["id"]]["meta"].get("ketertelmu")]
    gold = torch.tensor([LABELS.index(va_rows[k]["gold_label"]) for k in sel])
    grid, best = [], None
    for lam in LAMBDAS:
        w, b = fit_head(xtr, mtr, ttr, lam, args.iters)
        lp = log_probs(xva[sel], mva[sel], w, b)
        nll = float(-lp.gather(1, gold[:, None]).mean())
        acc = float((lp.argmax(-1) == gold).float().mean())
        tr_acc = float((log_probs(xtr, mtr, w, b).argmax(-1) == ttr.argmax(-1)).float().mean())
        grid.append({"lam": lam, "val_nll": round(nll, 4), "val_acc": round(acc, 4), "train_acc": round(tr_acc, 4)})
        print(grid[-1], flush=True)
        if best is None or nll < best[0]:
            best = (nll, lam, w, b)
    assert best is not None
    _, lam, w, b = best
    out = _p(args.out)
    out.mkdir(parents=True, exist_ok=True)
    torch.save({"w": w, "b": b, "mu": mu, "sd": sd, "lam": lam, "layer": args.layer, "labels": LABELS}, out / "fej.pt")
    write_jsonl(out / "val.jsonl", to_rows(va_rows, log_probs(xva, mva, w, b), args.layer, lam))
    write_json(out / "summary.json", {"layer": args.layer, "lam": lam, "racs": grid, "n_train": len(tr_rows),
                                      "n_val_sor": len(va_rows), "n_val_valaszto": len(sel)})


def cmd_apply(args) -> None:
    head = torch.load(_p(args.head))
    rows, h = load(_p(args.rows), _p(args.hidden), head["layer"])
    m = torch.zeros(len(rows), len(LABELS), dtype=torch.bool)
    for k, r in enumerate(rows):
        for lab in r["labels"]:
            m[k, LABELS.index(lab)] = True
    x = (h - head["mu"]) / head["sd"]
    write_jsonl(_p(args.out), to_rows(rows, log_probs(x, m, head["w"], head["b"]), head["layer"], head["lam"]))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fit", "apply"])
    ap.add_argument("--layer", type=int, default=27)
    ap.add_argument("--items", default="adat/f1")
    ap.add_argument("--train-rows", default="eredmenyek/F2/hf_train.jsonl")
    ap.add_argument("--train-hidden", default="cache/hidden/train")
    ap.add_argument("--val-rows", default="eredmenyek/F2/hf_val.jsonl")
    ap.add_argument("--val-hidden", default="cache/hidden/val")
    ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--out", default="")
    ap.add_argument("--head", default="")
    ap.add_argument("--rows", default="")
    ap.add_argument("--hidden", default="")
    args = ap.parse_args()
    {"fit": cmd_fit, "apply": cmd_apply}[args.cmd](args)


if __name__ == "__main__":
    main()
