"""05-ös kör — tartalmi fej a befagyasztott jellemzőkön: C, H, A kar (05-runbook 3.1, 6.; forrásterv 8.1).

Kimenet itemenként: a K opció pontszáma (közös pontozóháló, maszkolva) és a globális állapotok (NO_MATCH,
MISSING_DATA, OUT_OF_SCOPE; a 05b-ben + AMBIGUOUS) egy közös softmaxban. A prompt X-sora nem opció-kimenet: a
reprezentációja a globális állapotok bemenete.

Jellemzők (a hf_jellemzo05 kimenetéből; standardizálás csak a D_fit alapján):
  C  opciónként: a címke teljes szókészletes logprobja, a szűkített log-valószínűség, top-1-jelző, rés a top-1-hez;
     globálisan: az X logprobja és szűkített valószínűsége, top1–top2 rés, a szűkített és a szókészletes entrópia,
     az opciószám, a címketömeg logaritmusa
  H  C + a 20/28/40. réteg összefűzve (6144): P·q, P·c_vég, P·c_átlag, P·q ⊙ P·c_vég, P·q − P·c_vég opciónként, közös
     128-as P vetítéssel; globálisan P·q, P·x_vég, P·x_átlag és az opciók rejtett rétegének átlaga és maximuma
  A  H + attention: opciónként a fejátlagolt tömeg, a fejek közti szórás, a tokenenkénti átlag és a span-maximum
     rétegenként, a span log-hossza és relatív kezdete; globálisan az X, a rendszer-, az utasítás-, az adat-, a fejléc-
     és a sablonspan tömege, valamint az opciók közti koncentráció (legnagyobb részarány, entrópia) rétegenként

Veszteség: −log Σ_{y ∈ gold_set} p(y) (a megengedett kimenetek összvalószínűsége; forrásterv 8.1). Tanítás: AdamW,
LR ∈ {1e-4, 3e-4}, weight decay 0,01, batch 64, ≤ 20 epoch, patience 3 a D_dev makro NLL-jén, gradient clip 1,0,
seed 17/42/73. Karonként egy LR: amelyiknél a három seed D_dev makro NLL-jének átlaga kisebb.

  python3 kor05/eszkozok/fej05.py tanit --kar H --fit cache/k05/jellemzok/D_fit__fit \\
      --dev cache/k05/jellemzok/D_dev__kanonikus --out cache/k05/fejek/H
  python3 kor05/eszkozok/fej05.py josol --fej cache/k05/fejek/H --be cache/k05/jellemzok/D_meta__kanonikus \\
      --out cache/k05/predikciok/H/D_meta
"""

from __future__ import annotations

import argparse
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
from common import write_json, write_jsonl  # noqa: E402
from pecset05 import kapu  # noqa: E402

STATES = ("NO_MATCH", "MISSING_DATA", "OUT_OF_SCOPE")
STATE_NAMES = ("MATCH", *STATES)
ARMS = ("C", "H", "A", "HX")


def states_of(arm: str) -> tuple[str, ...]:
    """A globális kimenetek: a HX (a K*-X abláció, 05-runbook 3. pont, H4) a H jellemzőivel, de minden nem-MATCH
    állapot egyetlen X-be összevonva."""
    return ("X",) if arm == "HX" else STATES


def hidden(arm: str) -> bool:
    return arm in ("H", "A", "HX")
KMAX = 10
WIDTH, DROPOUT = 128, 0.1
LRS, SEEDS = (1e-4, 3e-4), (17, 42, 73)
GLOBAL_SPANS = ("rendszer", "utasitas", "adat", "fejlec", "sablon")


# --- betöltés ---------------------------------------------------------------------------------------------------------

def load_dir(d: Path, features: bool = True) -> list[dict]:
    """(sor, jellemző) párok shardsorrendben; a jellemzők (id, perm) szerint illesztve. A pecsét alatti könyvtárat a
    v1a rögzítése nélkül nem olvassa (pecset05.kapu)."""
    kapu(d)
    out = []
    for fr in sorted(d.glob("sorok_*.jsonl")):
        rs = [json.loads(line) for line in fr.read_text(encoding="utf-8").splitlines() if line.strip()]
        fs = {}
        if features:
            for f in torch.load(fr.with_name(fr.name.replace("sorok_", "jellemzok_").replace(".jsonl", ".pt")),
                                weights_only=False):
                fs[(f["id"], f["perm"])] = f
        for r in rs:
            out.append({"row": r, "feat": fs.get((r["id"], r["perm"])) if features else None})
    return out


def c_features(r: dict) -> tuple[list[list[float]], list[float]]:
    labs = r["labels"]
    cand = [lab for lab in labs if lab != "X"]
    lp = r["label_logprobs"]
    pr = r["probs"]
    top = max(pr.values())
    srt = sorted(pr.values(), reverse=True)
    cf = [[lp[lab], math.log(max(pr[lab], 1e-12)), float(pr[lab] == top), math.log(max(pr[lab], 1e-12)) - math.log(top)]
          for lab in cand]
    ent = -sum(p * math.log(max(p, 1e-12)) for p in pr.values())
    gf = [lp["X"], pr["X"], srt[0] - (srt[1] if len(srt) > 1 else 0.0), ent, r.get("entropy_vocab", 0.0),
          float(len(cand)), math.log(max(r["label_mass"], 1e-12))]
    return cf, gf


def a_features(f: dict, n_tok: int, k: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Opciónként 14, globálisan 6 × 3 + 2 × 3 = 24 jellemző (3 réteg)."""
    at = f["attn_span"].float()  # (3, H, n_span): az első k+1 span az opciók és az X, utána a GLOBAL_SPANS
    mx = f["attn_max"].float()  # (3, n_span)
    ln = torch.tensor(f["span_len"], dtype=torch.float32)
    st = torch.tensor(f["span_start"], dtype=torch.float32)
    mean_h, std_h = at.mean(1), at.std(1)  # (3, n_span)
    per_tok = mean_h / ln.clamp(min=1)
    cand = torch.cat([mean_h[:, :k], std_h[:, :k], per_tok[:, :k], mx[:, :k]], 0).T  # (k, 12)
    cand = torch.cat([cand, torch.log1p(ln[:k])[:, None], (st[:k] / max(1, n_tok))[:, None]], 1)  # (k, 14)
    share = mean_h[:, :k] / mean_h[:, :k].sum(1, keepdim=True).clamp(min=1e-12)
    conc = torch.stack([share.max(1).values, -(share * share.clamp(min=1e-12).log()).sum(1)], 1)  # (3, 2)
    glob = torch.cat([mean_h[:, k:k + 1 + len(GLOBAL_SPANS)].reshape(-1), conc.reshape(-1)])  # X + 5 span → 18 + 6
    return cand, glob


def to_example(e: dict, arm: str) -> dict:
    r, f = e["row"], e["feat"]
    labs, order = r["labels"], r["order"]
    cand_ids = [oid for oid, lab in zip(order, labs) if lab != "X"]
    k = len(cand_ids)
    cf, gf = c_features(r)
    out_ids = cand_ids + list(states_of(arm))
    gs = set(r["gold_set"])
    if arm == "HX" and r["content_state"] != "MATCH":
        gs = {"X"}
    ex = {"id": r["id"], "perm": r["perm"], "k": k, "cand_ids": cand_ids, "out_ids": out_ids,
          "state": r["content_state"], "ketertelmu": r["ketertelmu"],
          "cf": torch.tensor(cf), "gf": torch.tensor(gf), "gold": torch.tensor([o in gs for o in out_ids])}
    if hidden(arm):
        x = k  # az X az order utolsó eleme, a spanok sorrendje az orderé
        ex["q"] = f["h_last"].reshape(-1)
        ex["c_end"] = f["h_opt_end"][:, :k].permute(1, 0, 2).reshape(k, -1)
        ex["c_mean"] = f["h_opt_mean"][:, :k].permute(1, 0, 2).reshape(k, -1)
        ex["x_end"] = f["h_opt_end"][:, x].reshape(-1)
        ex["x_mean"] = f["h_opt_mean"][:, x].reshape(-1)
    if arm == "A":
        ex["af"], ex["ag"] = a_features(f, r["n_prompt_tokens"], k)
    if not ex["gold"].any():
        raise ValueError(f"{r['id']}: a gold-halmaz nem képezhető le a kimenetekre ({r['gold_set']})")
    return ex


class Stats:
    """Standardizálás a D_fit alapján (skalár jellemzők és rejtett vektorok külön)."""

    def __init__(self, exs: list[dict], arm: str):
        def ms(t: torch.Tensor):
            t = t.float()
            return t.mean(0), t.std(0).clamp(min=1e-6)

        self.s = {"cf": ms(torch.cat([e["cf"] for e in exs])), "gf": ms(torch.stack([e["gf"] for e in exs]))}
        if hidden(arm):
            self.s["h"] = ms(torch.cat([torch.stack([e["q"] for e in exs]), torch.cat([e["c_end"] for e in exs])]))
        if arm == "A":
            self.s["af"] = ms(torch.cat([e["af"] for e in exs]))
            self.s["ag"] = ms(torch.stack([e["ag"] for e in exs]))

    def state(self) -> dict:
        return {k: (m.tolist(), s.tolist()) for k, (m, s) in self.s.items()}

    @classmethod
    def from_state(cls, st: dict) -> "Stats":
        o = cls.__new__(cls)
        o.s = {k: (torch.tensor(m), torch.tensor(s)) for k, (m, s) in st.items()}
        return o

    def z(self, key: str, t: torch.Tensor) -> torch.Tensor:
        m, s = self.s[key]
        return (t.float() - m) / s


def collate(exs: list[dict], arm: str, st: Stats, dev: str) -> dict:
    b = len(exs)
    mask = torch.zeros(b, KMAX, dtype=torch.bool)
    cf = torch.zeros(b, KMAX, exs[0]["cf"].shape[1])
    gold = torch.zeros(b, KMAX + len(states_of(arm)), dtype=torch.bool)
    for i, e in enumerate(exs):
        mask[i, :e["k"]] = True
        cf[i, :e["k"]] = st.z("cf", e["cf"])
        gold[i, :e["k"]] = e["gold"][:e["k"]]
        gold[i, KMAX:] = e["gold"][e["k"]:]
    out = {"mask": mask, "cf": cf, "gf": st.z("gf", torch.stack([e["gf"] for e in exs])), "gold": gold}
    if hidden(arm):
        d = exs[0]["q"].shape[0]
        ce, cm = torch.zeros(b, KMAX, d), torch.zeros(b, KMAX, d)
        for i, e in enumerate(exs):
            ce[i, :e["k"]] = st.z("h", e["c_end"])
            cm[i, :e["k"]] = st.z("h", e["c_mean"])
        out |= {"q": st.z("h", torch.stack([e["q"] for e in exs])), "c_end": ce, "c_mean": cm,
                "x_end": st.z("h", torch.stack([e["x_end"] for e in exs])),
                "x_mean": st.z("h", torch.stack([e["x_mean"] for e in exs]))}
    if arm == "A":
        af = torch.zeros(b, KMAX, exs[0]["af"].shape[1])
        for i, e in enumerate(exs):
            af[i, :e["k"]] = st.z("af", e["af"])
        out |= {"af": af, "ag": st.z("ag", torch.stack([e["ag"] for e in exs]))}
    return {k: v.to(dev) for k, v in out.items()}


# --- modell -----------------------------------------------------------------------------------------------------------

class ContentHead(nn.Module):
    def __init__(self, arm: str, d_cf: int, d_gf: int, d_h: int = 0, d_af: int = 0, d_ag: int = 0,
                 width: int = WIDTH, dropout: float = DROPOUT):
        super().__init__()
        self.arm = arm
        hid = hidden(arm)
        self.proj = nn.Linear(d_h, width) if hid else None
        d_cand = d_cf + (5 * width if hid else 0) + (d_af if arm == "A" else 0)
        self.cand_hidden = nn.Sequential(nn.Linear(d_cand, width), nn.GELU(), nn.Dropout(dropout))
        self.cand_out = nn.Linear(width, 1)
        d_glob = d_gf + 2 * width + (3 * width if hid else 0) + (d_ag if arm == "A" else 0)
        self.glob = nn.Sequential(nn.Linear(d_glob, width), nn.GELU(), nn.Dropout(dropout), nn.Linear(width, len(states_of(arm))))

    def forward(self, b: dict) -> torch.Tensor:
        parts, gparts = [b["cf"]], [b["gf"]]
        if self.proj is not None:
            q = self.proj(b["q"])
            ce, cm = self.proj(b["c_end"]), self.proj(b["c_mean"])
            qq = q[:, None].expand_as(ce)
            parts += [qq, ce, cm, qq * ce, qq - ce]
            gparts += [q, self.proj(b["x_end"]), self.proj(b["x_mean"])]
        if self.arm == "A":
            parts.append(b["af"])
            gparts.append(b["ag"])
        h = self.cand_hidden(torch.cat(parts, -1))  # (B, KMAX, W)
        m = b["mask"][..., None]
        h_mean = (h * m).sum(1) / m.sum(1).clamp(min=1)
        h_max = h.masked_fill(~m, -1e4).max(1).values
        cand = self.cand_out(h).squeeze(-1).masked_fill(~b["mask"], float("-inf"))
        glob = self.glob(torch.cat([*gparts, h_mean, h_max], -1))
        return torch.cat([cand, glob], -1)  # (B, KMAX + |states_of(arm)|)


def set_nll(logits: torch.Tensor, gold: torch.Tensor) -> torch.Tensor:
    lse_all = torch.logsumexp(logits, -1)
    lse_gold = torch.logsumexp(logits.masked_fill(~gold, float("-inf")), -1)
    return lse_all - lse_gold


def n_params(m: nn.Module) -> int:
    return sum(p.numel() for p in m.parameters())


# --- tanítás ----------------------------------------------------------------------------------------------------------

@torch.no_grad()
def evaluate(model, exs, arm, st, dev) -> dict:
    model.eval()
    by = defaultdict(list)
    for i in range(0, len(exs), 256):
        chunk = exs[i:i + 256]
        b = collate(chunk, arm, st, dev)
        nll = set_nll(model(b), b["gold"])
        for e, v in zip(chunk, nll.tolist()):
            by[e["state"]].append(v)
    per = {s: sum(v) / len(v) for s, v in by.items()}
    return {"makro_nll": sum(per.values()) / len(per), "allapotonkent": per,
            "n": {s: len(v) for s, v in by.items()}}


def train_one(arm, fit, dev_exs, st, lr, seed, dev) -> tuple[nn.Module, dict]:
    torch.manual_seed(seed)
    e0 = fit[0]
    model = ContentHead(arm, e0["cf"].shape[1], e0["gf"].shape[0], e0["q"].shape[0] if "q" in e0 else 0,
                        e0["af"].shape[1] if "af" in e0 else 0, e0["ag"].shape[0] if "ag" in e0 else 0).to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    g = torch.Generator().manual_seed(seed)
    best, best_state, bad, hist = math.inf, None, 0, []
    for epoch in range(20):
        model.train()
        perm = torch.randperm(len(fit), generator=g).tolist()
        tot = 0.0
        for i in range(0, len(perm), 64):
            b = collate([fit[j] for j in perm[i:i + 64]], arm, st, dev)
            loss = set_nll(model(b), b["gold"]).mean()
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tot += loss.item() * len(b["gold"])
        ev = evaluate(model, dev_exs, arm, st, dev)
        hist.append({"epoch": epoch + 1, "train_nll": tot / len(fit), **ev})
        if ev["makro_nll"] < best - 1e-6:
            best, bad = ev["makro_nll"], 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= 3:
                break
    model.load_state_dict(best_state)
    return model, {"lr": lr, "seed": seed, "legjobb_dev_makro_nll": best, "tortenet": hist}


def tanit(a) -> None:
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    fit = [to_example(e, a.kar) for e in load_dir(Path(a.fit), a.kar != "C" or a.mindig_jellemzo)]
    dev_exs = [to_example(e, a.kar) for e in load_dir(Path(a.dev), a.kar != "C" or a.mindig_jellemzo)]
    st = Stats(fit, a.kar)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    runs = {}
    for lr in LRS:
        for seed in SEEDS:
            model, info = train_one(a.kar, fit, dev_exs, st, lr, seed, dev)
            runs[(lr, seed)] = (model, info)
            print(f"{a.kar} lr={lr} seed={seed}: D_dev makro NLL {info['legjobb_dev_makro_nll']:.4f}", flush=True)
    mean = {lr: sum(runs[(lr, s)][1]["legjobb_dev_makro_nll"] for s in SEEDS) / len(SEEDS) for lr in LRS}
    lr_best = min(mean, key=lambda lr: mean[lr])
    for s in SEEDS:
        model, info = runs[(lr_best, s)]
        torch.save({"state_dict": model.state_dict(), "arm": a.kar, "dims": dims_of(fit[0])}, out / f"fej_s{s}.pt")
    write_json(out / "fej.json", {"kar": a.kar, "allapotok": list(states_of(a.kar)), "lr_valasztott": lr_best, "dev_makro_nll_lr_szerint": mean,
                                  "parameterszam": n_params(runs[(lr_best, SEEDS[0])][0]), "stats": st.state(),
                                  "futasok": [runs[k][1] for k in runs], "n_fit": len(fit), "n_dev": len(dev_exs)})


def dims_of(e: dict) -> dict:
    return {"d_cf": e["cf"].shape[1], "d_gf": e["gf"].shape[0], "d_h": e["q"].shape[0] if "q" in e else 0,
            "d_af": e["af"].shape[1] if "af" in e else 0, "d_ag": e["ag"].shape[0] if "ag" in e else 0}


@torch.no_grad()
def josol(a) -> None:
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    meta = json.loads((Path(a.fej) / "fej.json").read_text())
    arm, st = meta["kar"], Stats.from_state(meta["stats"])
    exs = [to_example(e, arm) for e in load_dir(Path(a.be), arm != "C")]
    out = Path(a.out)
    for f in sorted(Path(a.fej).glob("fej_s*.pt")):
        ck = torch.load(f, weights_only=False, map_location="cpu")
        model = ContentHead(arm, **ck["dims"]).to(dev)
        model.load_state_dict(ck["state_dict"])
        model.eval()
        rows = []
        for i in range(0, len(exs), 256):
            chunk = exs[i:i + 256]
            b = collate(chunk, arm, st, dev)
            p = torch.softmax(model(b), -1).cpu()
            for e, pi in zip(chunk, p):
                probs = {oid: float(pi[j]) for j, oid in enumerate(e["cand_ids"])}
                probs |= {s: float(pi[KMAX + j]) for j, s in enumerate(states_of(arm))}
                rows.append({"id": e["id"], "perm": e["perm"], "state": e["state"], "ketertelmu": e["ketertelmu"],
                             "probs": probs, "gold_set": [o for o, g in zip(e["out_ids"], e["gold"].tolist()) if g]})
        write_jsonl(out / f"{f.stem}.jsonl", rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tanit")
    t.add_argument("--kar", required=True, choices=list(ARMS))
    t.add_argument("--fit", required=True)
    t.add_argument("--dev", required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--mindig-jellemzo", action="store_true", help="a C kar is betölti a jellemzőfájlokat (ellenőrzés)")
    j = sub.add_parser("josol")
    j.add_argument("--fej", required=True)
    j.add_argument("--be", required=True)
    j.add_argument("--out", required=True)
    a = ap.parse_args()
    {"tanit": tanit, "josol": josol}[a.cmd](a)


if __name__ == "__main__":
    main()
