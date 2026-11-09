"""06-os kör — családtávolság-audit (06-runbook 3.1, 3.5; a 05 4.2 módszere): a három friss család bge-m3-távolsága a
05 itemkészletének (a 03 pool + a HO-rétegek, 218 család) családjaitól és csoportjaitól.

Szöveg itemenként: az állapot, a kérdés és az opciók (a promptkeret nélkül), legfeljebb 512 token. Beágyazás: bge-m3,
CLS + L2-normálás (a 00 `jeloltek.Embedder`-e). A kimenet csak szám és azonosító, szöveg nincs benne.
  - centroid-koszinusz: a friss családok a referencia-családokhoz (top 10), csoportonként a legközelebbi, és a friss
    családok egymáshoz;
  - viszonyítás: a referencia-családok legközelebbi másik családja ugyanabban, illetve más csoportban (kvantilisek);
  - itemszinten: a friss itemek legnagyobb koszinusza a referenciakészlethez (kvantilisek, ≥ 0,90 és ≥ 0,95 darab, a
    legközelebbi párok azonosítója), és ugyanez viszonyításként a referencia-itemek mintájára (a saját családjuk nélkül).
A kézi indoklás az eredménylapra kerül; ez a script nem dönt.

  python3 kor06/eszkozok/tavolsag06.py --out kor06/eredmenyek/F2/tavolsag   (GPU: py --gpu)
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path.insert(0, str(EXP / "eszkozok"))
from common import BGE_M3  # noqa: E402

CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
UJ = EXP / "kor06/adat/f2/items"
REF = ("kor03/adat/f3/mvp_train_v2.jsonl", "kor03/adat/f2/items_val.jsonl", "kor03/adat/f2/items_eval.jsonl")
Q = (0.5, 0.9, 0.95, 0.99, 1.0)


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def szoveg(it: dict) -> str:
    return "\n".join([it["state"], it["question"], *[o["text"] for o in it["options"]]])


class Embedder:  # a 00 `jeloltek.py`-jáé (CLS + L2-normálás), hossz szerint rendezett batchekkel
    def __init__(self):
        from transformers import AutoModel, AutoTokenizer

        self.tok = AutoTokenizer.from_pretrained(BGE_M3)
        self.model = AutoModel.from_pretrained(BGE_M3, dtype=torch.float16).cuda().eval()

    @torch.inference_mode()
    def __call__(self, texts: list[str], max_len: int, bs: int = 64) -> torch.Tensor:
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        out = torch.empty(len(texts), self.model.config.hidden_size)
        t0 = time.time()
        for b in range(0, len(order), bs):
            idx = order[b:b + bs]
            enc = self.tok([texts[i] for i in idx], padding=True, truncation=True, max_length=max_len,
                           return_tensors="pt").to("cuda")
            h = self.model(**enc).last_hidden_state[:, 0]
            out[idx] = torch.nn.functional.normalize(h.float(), dim=-1).cpu()
            if (b // bs) % 200 == 0:
                print(f"  {b + len(idx)}/{len(texts)} · {(b + len(idx)) / (time.time() - t0):.0f}/s", flush=True)
        return out


def kvant(x: np.ndarray) -> dict:
    return {f"q{int(q * 100)}": round(float(np.quantile(x, q)), 4) for q in Q} if len(x) else {}


def legkozelebb(a: torch.Tensor, b: torch.Tensor, kizar: np.ndarray | None = None, a_csal: np.ndarray | None = None,
                chunk: int = 2048) -> tuple[np.ndarray, np.ndarray]:
    """Az a soraira a b legnagyobb koszinusza és indexe; `kizar` (b családkódjai) és `a_csal` mellett a saját család
    itemjei kimaradnak."""
    bg = b.cuda()
    mx, ix = [], []
    for s in range(0, len(a), chunk):
        sim = a[s:s + chunk].cuda() @ bg.T
        if kizar is not None:
            sim[torch.as_tensor(a_csal[s:s + chunk, None] == kizar[None, :], device="cuda")] = -2.0
        v, i = sim.max(dim=1)
        mx.append(v.cpu().numpy())
        ix.append(i.cpu().numpy())
    return np.concatenate(mx), np.concatenate(ix)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--limit", type=int, default=0, help="próba: családonként legfeljebb ennyi item")
    ap.add_argument("--viszony-minta", type=int, default=5000)
    a = ap.parse_args()

    uj = [it for f in CSALADOK for it in jl(UJ / f"{f}.jsonl")]
    ref = [it for p in REF for it in jl(EXP / p)]
    if a.limit:
        def vag(xs):
            c = collections.Counter()
            return [it for it in xs if (c.update([it["family"]]) or c[it["family"]] <= a.limit)]
        uj, ref = vag(uj), vag(ref)
    if {it["family"] for it in ref} & set(CSALADOK):
        raise SystemExit("friss család a referenciakészletben")
    print(f"friss: {len(uj)} item · referencia: {len(ref)} item, {len({it['family'] for it in ref})} család", flush=True)
    emb = Embedder()
    eu = emb([szoveg(it) for it in uj], a.max_len)
    er = emb([szoveg(it) for it in ref], a.max_len)

    rcs = sorted({it["family"] for it in ref})
    rgrp = {it["family"]: it["group"] for it in ref}
    rkod = {f: i for i, f in enumerate(rcs)}
    r_fam = np.array([rkod[it["family"]] for it in ref])

    def centroid(e: torch.Tensor, mask) -> torch.Tensor:
        return torch.nn.functional.normalize(e[torch.as_tensor(mask)].mean(0), dim=0)

    cu = {f: centroid(eu, np.array([it["family"] == f for it in uj])) for f in CSALADOK}
    cr = torch.stack([centroid(er, r_fam == rkod[f]) for f in rcs])
    rr = (cr @ cr.T).numpy()
    np.fill_diagonal(rr, -2.0)
    same = np.array([[rgrp[x] == rgrp[y] for y in rcs] for x in rcs])
    viszony = {"masik_csalad_ugyanabban_a_csoportban": kvant(np.array([rr[i][same[i]].max() for i in range(len(rcs))
                                                                         if (rr[i][same[i]] > -2).any()])),
               "masik_csalad_mas_csoportban": kvant(np.array([rr[i][~same[i]].max() for i in range(len(rcs))]))}

    rep = {"modell": str(BGE_M3.relative_to(EXP)), "max_len": a.max_len, "n_uj": len(uj), "n_ref": len(ref),
           "ref_csaladok": len(rcs), "viszonyitas_centroid": viszony, "csaladok": {},
           "uj_egymas_kozt": {f"{x} · {y}": round(float(cu[x] @ cu[y]), 4)
                              for i, x in enumerate(CSALADOK) for y in CSALADOK[i + 1:]}}

    mx, ix = legkozelebb(eu, er)
    u_fam = np.array([it["family"] for it in uj])
    for f in CSALADOK:
        s = (cr @ cu[f]).numpy()
        top = np.argsort(-s)[:10]
        csop: dict[str, tuple[str, float]] = {}
        for j in np.argsort(-s):
            csop.setdefault(rgrp[rcs[j]], (rcs[j], round(float(s[j]), 4)))
        m = u_fam == f
        sel = np.where(m)[0]
        par = sel[np.argsort(-mx[sel])[:5]]
        rep["csaladok"][f] = {
            "centroid_top10": [{"csalad": rcs[j], "csoport": rgrp[rcs[j]], "cos": round(float(s[j]), 4)} for j in top],
            "csoportonkent_legkozelebbi": {g: {"csalad": c, "cos": v} for g, (c, v) in sorted(csop.items(), key=lambda kv: -kv[1][1])},
            "item_max_cos": kvant(mx[m]), "item_ge_090": int((mx[m] >= 0.90).sum()), "item_ge_095": int((mx[m] >= 0.95).sum()),
            "legkozelebbi_parok": [{"uj": uj[i]["id"], "ref": ref[ix[i]]["id"], "ref_csalad": ref[ix[i]]["family"],
                                    "cos": round(float(mx[i]), 4)} for i in par],
            "legkozelebbi_ref_csaladok_itemszinten": collections.Counter(ref[ix[i]]["family"] for i in sel).most_common(5)}

    # viszonyítás itemszinten: referencia-itemek determinisztikus mintája, a saját családjuk nélkül
    mi = sorted(range(len(ref)), key=lambda i: hashlib.sha256(ref[i]["id"].encode()).hexdigest())[: a.viszony_minta]
    vm, _ = legkozelebb(er[mi], er, kizar=r_fam, a_csal=r_fam[mi])
    rep["viszonyitas_item_max_cos_mas_csaladhoz"] = kvant(vm)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "tavolsag06.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    md = ["# Családtávolság-audit (06, F2): bge-m3", "",
          f"Friss itemek: {len(uj)}; referencia: a 05 itemkészlete, {len(ref)} item, {len(rcs)} család. Szöveg: állapot + "
          f"kérdés + opciók, ≤ {a.max_len} token. A kézi indoklás az eredménylapra kerül.", "",
          "Viszonyítás (centroid-koszinusz, a referencia-családok legközelebbi másik családja): "
          f"ugyanabban a csoportban {viszony['masik_csalad_ugyanabban_a_csoportban']}, más csoportban "
          f"{viszony['masik_csalad_mas_csoportban']}.", "",
          f"Viszonyítás itemszinten (referencia-item → más család legközelebbi itemje): "
          f"{rep['viszonyitas_item_max_cos_mas_csaladhoz']}.", "", f"A friss családok egymás közt: {rep['uj_egymas_kozt']}.", ""]
    for f, d in rep["csaladok"].items():
        md += [f"## {f}", "", "| referencia-család | csoport | centroid-cos |", "|---|---|---|"]
        md += [f"| {x['csalad']} | {x['csoport']} | {x['cos']:.3f} |" for x in d["centroid_top10"]]
        md += ["", f"Itemszinten a legnagyobb koszinusz a referenciához: {d['item_max_cos']}; ≥ 0,90: {d['item_ge_090']}, "
                   f"≥ 0,95: {d['item_ge_095']}. A legközelebbi referencia-családok itemszinten: "
                   f"{d['legkozelebbi_ref_csaladok_itemszinten']}.", ""]
    (out / "tavolsag06.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md), flush=True)


if __name__ == "__main__":
    main()
