"""05-ös kör — megbízhatósági fej (05-runbook 3.2; forrásterv 3.2, 8.2) és a karok döntési sorai.

A rögzített tartalmi fej (karonként és seedenként, `fej05.py`) javaslata:
  javaslat = argmax a tartalmi kimeneteken (K opció + NO_MATCH, MISSING_DATA, OUT_OF_SCOPE)
  opció → SELECT · NO_MATCH → NONE · MISSING_DATA / OUT_OF_SCOPE → DEFER (az ok a javaslat; forrásterv 9.)
  helyes (szigorú, elsődleges): SELECT ⇔ az opció a gold_set-ben; NONE ⇔ a tartalmi állapot NO_MATCH
  helyes (enyhe, leíró): NONE ⇔ a tartalmi állapot nem MATCH
A megbízhatósági fej a SELECT/NONE javaslatok szigorú helyességét tanulja (BCE), a D_meta-n. Bemenet:
  összegzés (11): NONE-jelző, a javaslat valószínűsége, top1, top2, rés, entrópia, a három állapot valószínűsége, az
                  opciók összvalószínűsége, log K
  C: a javasolt opció cf-je (NONE-nál 0) és a gf
  H: + P·q, P·c_vég, P·c_átlag, P·q ⊙ P·c_vég, P·q − P·c_vég, ahol c a javasolt opció (NONE-nál az X-sor) állapota
  A: + a javasolt opció af-je (NONE-nál 0) és az ag
A jellemzők a tartalmi fej D_fit-statisztikájával standardizálva, az összegzés a D_meta tanító részén. Felépítés:
128-as vetítés (H, A), 128 GELU, 0,1 dropout, egy logit. Tanítás: AdamW, LR ∈ {1e-4, 3e-4}, wd 0,01, batch 64,
≤ 20 epoch, patience 3 a D_meta belső validációs részén (alapesetenként hash-elve, 20%), seedenként a tartalmi fej
seedjével párban; karonként egy LR (a három seed belső val-BCE-jének átlaga).

  python3 kor05/eszkozok/megbizhatosag05.py tanit --kar H --fej cache/k05/fejek/H \\
      --meta cache/k05/jellemzok/D_meta__kanonikus --out cache/k05/megbizhatosag/H
  python3 kor05/eszkozok/megbizhatosag05.py dont --kar H --fej cache/k05/fejek/H --rel cache/k05/megbizhatosag/H \\
      --be cache/k05/jellemzok/D_cal_prob__kanonikus --out cache/k05/dontesek/H/D_cal_prob

A `dont` kimenete itemenként és seedenként: javaslat, a nyers megbízhatósági logit, a tartalmi log-valószínűségek (a
temperature-illesztéshez) és a helyesség. A kalibráció és a τ a `kalib05.py`-ban.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import torch
from torch import nn

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "eszkozok")]
import fej05  # noqa: E402
from allapot05 import rows as item_rows  # noqa: E402
from common import write_json, write_jsonl  # noqa: E402

KMAX, WIDTH, DROPOUT = fej05.KMAX, fej05.WIDTH, fej05.DROPOUT
states_of, hidden = fej05.states_of, fej05.hidden
LRS, SEEDS = fej05.LRS, fej05.SEEDS
VAL_SEED = "k05-meta-val:20261029"
TMETA_SEED = "k05-tmeta:20261029"
ITEM_FILES = ("kor03/adat/f3/mvp_train_v2.jsonl", "kor03/adat/f2/items_val.jsonl", "kor03/adat/f2/items_eval.jsonl")


def d_small(arm: str) -> int:
    return 8 + len(states_of(arm))  # 11 a C/H/A-n, 9 a HX-en


def group_ids() -> dict[str, str]:
    return {it["id"]: it["group_id"] for f in ITEM_FILES for it in item_rows(EXP / f)}


# --- a tartalmi fej javaslata -----------------------------------------------------------------------------------------

@torch.no_grad()
def content_probs(fejdir: Path, seed: int, arm: str, exs: list[dict], st: fej05.Stats, dev: str) -> torch.Tensor:
    ck = torch.load(fejdir / f"fej_s{seed}.pt", weights_only=False, map_location="cpu")
    model = fej05.ContentHead(arm, **ck["dims"]).to(dev)
    model.load_state_dict(ck["state_dict"])
    model.eval()
    out = []
    for i in range(0, len(exs), 256):
        out.append(torch.softmax(model(fej05.collate(exs[i:i + 256], arm, st, dev)), -1).cpu())
    return torch.cat(out)


def proposal(e: dict, p: torch.Tensor, states: tuple[str, ...] = fej05.STATES) -> dict:
    """A javaslat és a helyessége egy itemre; p: (KMAX + |states|) valószínűség (a maszkolt opciók 0). A HX X-e
    NONE-javaslat (a régi L1★ X-értelmezése)."""
    k = e["k"]
    full = torch.cat([p[:k], p[KMAX:]])
    j = int(full.argmax())
    gold = e["gold"]
    if j < k:
        kind, cand, ok = "SELECT", e["cand_ids"][j], bool(gold[j])
        ok_l = ok
    else:
        s = states[j - k]
        kind = "NONE" if s in ("NO_MATCH", "X") else "DEFER"
        cand = None
        ok = e["state"] == "NO_MATCH" if kind == "NONE" else None
        ok_l = e["state"] != "MATCH" if kind == "NONE" else None
    srt = torch.sort(full, descending=True).values
    ent = float(-(full.clamp(min=1e-12).log() * full).sum())
    small = [float(kind == "NONE"), float(full[j]), float(srt[0]), float(srt[1]) if len(srt) > 1 else 0.0,
             float(srt[0] - (srt[1] if len(srt) > 1 else 0.0)), ent, *[float(x) for x in p[KMAX:]],
             float(p[:k].sum()), math.log(k)]
    return {"kind": kind, "j": j, "cand": cand, "defer_reason": states[j - k] if kind == "DEFER" else None,
            "helyes": ok, "helyes_enyhe": ok_l, "small": small, "logp": full.clamp(min=1e-30).log().tolist()}


def rel_example(e: dict, pr: dict, arm: str, st: fej05.Stats) -> dict:
    j, k, sel = pr["j"], e["k"], pr["kind"] == "SELECT"
    cf = st.z("cf", e["cf"])
    r = {"small": torch.tensor(pr["small"]), "cf": cf[j] if sel else torch.zeros(cf.shape[1]),
         "gf": st.z("gf", e["gf"]), "y": float(bool(pr["helyes"]))}
    if hidden(arm):
        r |= {"q": st.z("h", e["q"]), "c": st.z("h", e["c_end"][j] if sel else e["x_end"]),
              "cm": st.z("h", e["c_mean"][j] if sel else e["x_mean"])}
    if arm == "A":
        af = st.z("af", e["af"])
        r |= {"af": af[j] if sel else torch.zeros(af.shape[1]), "ag": st.z("ag", e["ag"])}
    assert j < k or not sel
    return r


class RelHead(nn.Module):
    def __init__(self, arm: str, d_cf: int, d_gf: int, d_h: int = 0, d_af: int = 0, d_ag: int = 0,
                 width: int = WIDTH, dropout: float = DROPOUT):
        super().__init__()
        self.arm = arm
        hid = hidden(arm)
        self.proj = nn.Linear(d_h, width) if hid else None
        d_in = d_small(arm) + d_cf + d_gf + (5 * width if hid else 0) + (d_af + d_ag if arm == "A" else 0)
        self.net = nn.Sequential(nn.Linear(d_in, width), nn.GELU(), nn.Dropout(dropout), nn.Linear(width, 1))

    def forward(self, b: dict) -> torch.Tensor:
        parts = [b["small"], b["cf"], b["gf"]]
        if self.proj is not None:
            q, c, cm = self.proj(b["q"]), self.proj(b["c"]), self.proj(b["cm"])
            parts += [q, c, cm, q * c, q - c]
        if self.arm == "A":
            parts += [b["af"], b["ag"]]
        return self.net(torch.cat(parts, -1)).squeeze(-1)


def batch(rs: list[dict], ms: tuple[torch.Tensor, torch.Tensor], dev: str) -> dict:
    out = {k: torch.stack([r[k] for r in rs]) for k in rs[0] if k not in ("y", "small")}
    out["small"] = (torch.stack([r["small"] for r in rs]) - ms[0]) / ms[1]
    out["y"] = torch.tensor([r["y"] for r in rs])
    return {k: v.float().to(dev) for k, v in out.items()}


def auroc(score: list[float], y: list[float]) -> float:
    pos = [s for s, t in zip(score, y) if t]
    neg = [s for s, t in zip(score, y) if not t]
    if not pos or not neg:
        return math.nan
    order = sorted(score)
    rank = {}
    for i, s in enumerate(order):
        rank.setdefault(s, []).append(i + 1)
    avg = {s: sum(v) / len(v) for s, v in rank.items()}
    return (sum(avg[s] for s in pos) - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


@torch.no_grad()
def bce_eval(model: RelHead, rs: list[dict], ms, dev: str) -> tuple[float, list[float]]:
    model.eval()
    logits = []
    for i in range(0, len(rs), 256):
        logits += model(batch(rs[i:i + 256], ms, dev)).cpu().tolist()
    y = torch.tensor([r["y"] for r in rs])
    return float(nn.functional.binary_cross_entropy_with_logits(torch.tensor(logits), y)), logits


def train_rel(arm: str, fit: list[dict], val: list[dict], ms, dims: dict, lr: float, seed: int, dev: str,
              init: RelHead | None = None):
    torch.manual_seed(seed)
    model = init if init is not None else RelHead(arm, **dims).to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    g = torch.Generator().manual_seed(seed)
    best, best_state, bad, hist = math.inf, None, 0, []
    for epoch in range(20):
        model.train()
        perm = torch.randperm(len(fit), generator=g).tolist()
        tot = 0.0
        for i in range(0, len(perm), 64):
            b = batch([fit[j] for j in perm[i:i + 64]], ms, dev)
            loss = nn.functional.binary_cross_entropy_with_logits(model(b), b["y"])
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tot += loss.item() * len(b["y"])
        v, logits = bce_eval(model, val, ms, dev)
        hist.append({"epoch": epoch + 1, "train_bce": tot / len(fit), "val_bce": v,
                     "val_auroc": auroc(logits, [r["y"] for r in val])})
        if v < best - 1e-6:
            best, bad = v, 0
            best_state = {k: t.detach().cpu().clone() for k, t in model.state_dict().items()}
        else:
            bad += 1
            if bad >= 3:
                break
    model.load_state_dict(best_state)
    return model, {"lr": lr, "seed": seed, "legjobb_val_bce": best, "tortenet": hist}


def dims_for(arm: str, r: dict) -> dict:
    return {"d_cf": r["cf"].shape[0], "d_gf": r["gf"].shape[0], "d_h": r["q"].shape[0] if "q" in r else 0,
            "d_af": r["af"].shape[0] if "af" in r else 0, "d_ag": r["ag"].shape[0] if "ag" in r else 0}


def load_examples(d: Path, arm: str) -> list[dict]:
    return [fej05.to_example(e, arm) for e in fej05.load_dir(d, arm != "C")]


# --- alparancsok ------------------------------------------------------------------------------------------------------

def tanit(a) -> None:
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    fejdir = Path(a.fej)
    st = fej05.Stats.from_state(json.loads((fejdir / "fej.json").read_text())["stats"])
    exs = load_examples(Path(a.meta), a.kar)
    gid = group_ids()
    is_val = [int(hashlib.sha256(f"{VAL_SEED}|{gid[e['id']]}".encode()).hexdigest(), 16) % 5 == 0 for e in exs]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    runs, per_seed = {}, {}
    for seed in SEEDS:
        P = content_probs(fejdir, seed, a.kar, exs, st, dev)
        prs = [proposal(e, p, states_of(a.kar)) for e, p in zip(exs, P)]
        keep = [i for i, pr in enumerate(prs) if pr["kind"] != "DEFER"]
        rs = [rel_example(exs[i], prs[i], a.kar, st) for i in keep]
        fit = [r for r, i in zip(rs, keep) if not is_val[i]]
        val = [r for r, i in zip(rs, keep) if is_val[i]]
        sm = torch.stack([r["small"] for r in fit])
        ms = (sm.mean(0), sm.std(0).clamp(min=1e-6))
        dims = dims_for(a.kar, rs[0])
        kinds = [pr["kind"] for pr in prs]
        per_seed[seed] = {"n": len(exs), "SELECT": kinds.count("SELECT"), "NONE": kinds.count("NONE"),
                          "DEFER": kinds.count("DEFER"), "n_fit": len(fit), "n_val": len(val),
                          "javaslat_szigoru_pontossag": sum(r["y"] for r in rs) / max(1, len(rs)),
                          "kis_jellemzo_stat": [ms[0].tolist(), ms[1].tolist()], "dims": dims}
        for lr in LRS:
            model, info = train_rel(a.kar, fit, val, ms, dims, lr, seed, dev)
            runs[(lr, seed)] = (model, info)
            last = min(info["tortenet"], key=lambda h: h["val_bce"])
            print(f"{a.kar} s{seed} lr={lr}: val BCE {info['legjobb_val_bce']:.4f}, AUROC {last['val_auroc']:.4f} "
                  f"(SELECT {per_seed[seed]['SELECT']}, NONE {per_seed[seed]['NONE']}, DEFER {per_seed[seed]['DEFER']})",
                  flush=True)
    mean = {lr: sum(runs[(lr, s)][1]["legjobb_val_bce"] for s in SEEDS) / len(SEEDS) for lr in LRS}
    lr_best = min(mean, key=lambda lr: mean[lr])
    for s in SEEDS:
        torch.save({"state_dict": runs[(lr_best, s)][0].state_dict(), "arm": a.kar, "dims": per_seed[s]["dims"],
                    "kis_jellemzo_stat": per_seed[s]["kis_jellemzo_stat"]}, out / f"rel_s{s}.pt")
    write_json(out / "rel.json", {"kar": a.kar, "lr_valasztott": lr_best, "val_bce_lr_szerint": mean,
                                  "parameterszam": fej05.n_params(runs[(lr_best, SEEDS[0])][0]), "seedenkent": per_seed,
                                  "futasok": [runs[k][1] for k in runs], "val_seed": VAL_SEED})


def decision_rows(arm: str, exs: list[dict], prs: list[dict], logit: dict, seed: int, gid: dict) -> list[dict]:
    rows = []
    for i, (e, pr) in enumerate(zip(exs, prs)):
        rows.append({"id": e["id"], "perm": e["perm"], "seed": seed, "group_id": gid[e["id"]], "state": e["state"],
                     "ketertelmu": e["ketertelmu"], "javaslat": pr["kind"], "jelolt": pr["cand"],
                     "defer_ok": pr["defer_reason"], "helyes": pr["helyes"], "helyes_enyhe": pr["helyes_enyhe"],
                     "p_javaslat": pr["small"][1], "rel_logit": logit.get(i), "out_ids": e["cand_ids"] + list(states_of(arm)),
                     "logp": pr["logp"], "gold": [o for o, g in zip(e["out_ids"], e["gold"].tolist()) if g]})
    return rows


def load_rel(path: Path, arm: str, dev: str) -> tuple[RelHead, tuple, dict]:
    ck = torch.load(path, weights_only=False, map_location="cpu")
    model = RelHead(arm, **ck["dims"]).to(dev)
    model.load_state_dict(ck["state_dict"])
    model.eval()
    return model, tuple(torch.tensor(x) for x in ck["kis_jellemzo_stat"]), ck


@torch.no_grad()
def rel_logits(model: RelHead, rs: list[dict], idx: list[int], ms, dev: str) -> dict[int, float]:
    model.eval()
    out = {}
    for c in range(0, len(idx), 256):
        out |= dict(zip(idx[c:c + 256], model(batch(rs[c:c + 256], ms, dev)).cpu().tolist()))
    return out


def prepare(arm: str, fejdir: Path, d: Path, seed: int, st, dev: str):
    exs = load_examples(d, arm)
    P = content_probs(fejdir, seed, arm, exs, st, dev)
    prs = [proposal(e, p, states_of(arm)) for e, p in zip(exs, P)]
    keep = [i for i, pr in enumerate(prs) if pr["kind"] != "DEFER"]
    return exs, prs, keep, [rel_example(exs[i], prs[i], arm, st) for i in keep]


def dont(a) -> None:
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    fejdir, reldir = Path(a.fej), Path(a.rel)
    st = fej05.Stats.from_state(json.loads((fejdir / "fej.json").read_text())["stats"])
    gid = group_ids()
    out = Path(a.out)
    for seed in SEEDS:
        exs, prs, keep, rs = prepare(a.kar, fejdir, Path(a.be), seed, st, dev)
        model, ms, _ = load_rel(reldir / f"rel_s{seed}.pt", a.kar, dev)
        rows = decision_rows(a.kar, exs, prs, rel_logits(model, rs, keep, ms, dev), seed, gid)
        write_jsonl(out / f"s{seed}.jsonl", rows)
        print(f"{a.kar} s{seed} → {out}: {len(rows)} sor", flush=True)


def tmeta(a) -> None:
    """K*-T-meta (05-runbook 3.3; v1a D3): a D_meta-n tanult megbízhatósági fej finomhangolása a célcsalád-mintán,
    5-szörös, alapesetenként hash-elt cross-fittinggel. Foldonként a többi négy fold tanít (a korai megállás azok
    20%-os belső részén, alapesetenként hash-elve), a kihagyott fold kapja a cross-fittelt logitot; a teszten az öt
    fold-modell logitjának átlaga. A LR és a kis jellemzők standardizálása a D_meta-fejé; a τ és a Platt a
    cross-fittelt mintán illeszkedik (`kalib05`)."""
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    fejdir, reldir = Path(a.fej), Path(a.rel)
    st = fej05.Stats.from_state(json.loads((fejdir / "fej.json").read_text())["stats"])
    lr = json.loads((reldir / "rel.json").read_text())["lr_valasztott"]
    gid = group_ids()
    out = Path(a.out)
    info = {"kar": a.kar, "lr": lr, "fold_seed": TMETA_SEED, "seedenkent": {}}
    for seed in SEEDS:
        exs, prs, keep, rs = prepare(a.kar, fejdir, Path(a.minta), seed, st, dev)
        tests = {Path(t).name.split("__")[0]: prepare(a.kar, fejdir, Path(t), seed, st, dev) for t in a.teszt}
        h = lambda tag, i: int(hashlib.sha256(f"{TMETA_SEED}|{tag}|{gid[exs[i]['id']]}".encode()).hexdigest(), 16)
        fold = [h("fold", i) % 5 for i in keep]
        cross, test_sum, folds = {}, {n: defaultdict(float) for n in tests}, []
        for f in range(5):
            tr = [n for n, x in enumerate(fold) if x != f]
            inner_val = [n for n in tr if h("belso", keep[n]) % 5 == 0]
            inner_fit = [n for n in tr if h("belso", keep[n]) % 5 != 0]
            model, ms, ck = load_rel(reldir / f"rel_s{seed}.pt", a.kar, dev)
            model, inf = train_rel(a.kar, [rs[n] for n in inner_fit], [rs[n] for n in inner_val], ms, ck["dims"], lr,
                                   seed * 10 + f, dev, init=model)
            held = [n for n, x in enumerate(fold) if x == f]
            cross |= rel_logits(model, [rs[n] for n in held], [keep[n] for n in held], ms, dev)
            for n, (_, _, tkeep, trs) in tests.items():
                for i, v in rel_logits(model, trs, tkeep, ms, dev).items():
                    test_sum[n][i] += v / 5
            folds.append({"fold": f, "n_tanit": len(inner_fit), "n_belso_val": len(inner_val), "n_kihagyott": len(held),
                          "legjobb_val_bce": inf["legjobb_val_bce"], "epoch": len(inf["tortenet"])})
        write_jsonl(out / "minta" / f"s{seed}.jsonl", decision_rows(a.kar, exs, prs, cross, seed, gid))
        for n, (texs, tprs, _, _) in tests.items():
            write_jsonl(out / "teszt" / n / f"s{seed}.jsonl", decision_rows(a.kar, texs, tprs, dict(test_sum[n]), seed, gid))
        info["seedenkent"][str(seed)] = {"n_minta": len(exs), "n_minta_dontes": len(keep), "foldok": folds}
        print(f"{a.kar} s{seed}: T-meta kész ({len(keep)} mintabeli döntés)", flush=True)
    write_json(out / "tmeta.json", info)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tanit")
    t.add_argument("--kar", required=True, choices=list(fej05.ARMS))
    t.add_argument("--fej", required=True)
    t.add_argument("--meta", required=True)
    t.add_argument("--out", required=True)
    d = sub.add_parser("dont")
    d.add_argument("--kar", required=True, choices=list(fej05.ARMS))
    d.add_argument("--fej", required=True)
    d.add_argument("--rel", required=True)
    d.add_argument("--be", required=True)
    d.add_argument("--out", required=True)
    m = sub.add_parser("tmeta")
    m.add_argument("--kar", required=True, choices=list(fej05.ARMS))
    m.add_argument("--fej", required=True)
    m.add_argument("--rel", required=True)
    m.add_argument("--minta", required=True, help="a célcsalád-minta jellemzői (cel:*)")
    m.add_argument("--teszt", action="append", required=True, help="a teszt(ek) jellemzői (teszt:*); ismételhető")
    m.add_argument("--out", required=True)
    a = ap.parse_args()
    {"tanit": tanit, "dont": dont, "tmeta": tmeta}[a.cmd](a)


if __name__ == "__main__":
    main()
