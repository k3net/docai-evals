"""05-ös kör — jellemzőkivonás a HF-úton, az „FP8-hű BF16” bázison (05-runbook 3.1, 5.; forrásterv 7.).

Egyetlen forward itemenként és permutációnként:
  sor (jsonl)   a B0/C alapja: a jelen lévő címkék teljes szókészletes logprobja, a szűkített eloszlás, a címketömeg,
                a tokenszám (a hf_kiolvaso sorformátuma, így az eszkozok/elemzes.py karjai változatlanul futnak rajta)
  H             a `hidden_states` 20., 28. és 40. eleme (0 = embedding; a 40. a záró norma utáni, amelyet az lm_head
                lát, mint a 00 L2a-nál): az utolsó promptpozíció, és opciónként (az X-et is) a leírás utolsó tokenje és
                a span átlaga
  A             ugyanezen három réteg (mind full attention: a config `layer_types` szerint 4, 8, …, 40) attentionjében
                az utolsó promptpozíció softmax-sora, fejenként a spanokra összegezve: opciók, X, rendszerüzenet,
                utasítás, adat, opciófejléc, sablon (a többi token); N × N mátrix nem készül
Az attention-sort az SDPA-függvény burkolója számolja a (RoPE utáni) q/k-ból fp32-ben; a kimenet az eredeti SDPA-é,
változatlanul. A `egyezes` alparancs ezt bájtra ellenőrzi (forrásterv P1).

Spanok (karakterből tokenre a tokenizer offsetjeivel; a token-sor bájtra egyezik a PromptTokenizer.encode-dal):
  opció i       a „{címke}) ” utáni szöveg a következő opciósor elejéig (az utolsó a felhasználói üzenet végéig)
  utasítás      generikus keret: a „Kérdés: …” sor; natív (00/01) keret: a felhasználói üzenet első sora
  adat          generikus keret: az állapot szövege; natív keret: az első sor és az opciófejléc közti sorok

Permutáció-módok (05-runbook 5.1):
  kanonikus     perm 0 (az értékelés előre rögzített promptváltozata)
  fit           itemenként egy, hash-sel választott perm a {0, 1, 2, 3}-ból (D_fit)
  b1            perm 1, 2, 3, jellemzők nélkül (a B1 perm-átlagához)

  python3 kor05/eszkozok/hf_jellemzo05.py spanok --szelet D_dev,teszt:ho-termek,teszt:ho-routing,teszt:ho-uj \\
      --out kor05/eredmenyek/F0/spanok          (CPU: span- és tokenhatár-ellenőrzés + 30 példa kézi átnézésre)
  python3 kor05/eszkozok/hf_jellemzo05.py kivon --feladat D_dev:kanonikus --feladat D_fit:fit \\
      --out-root cache/k05/jellemzok --status STATUS-K05F2A
  python3 kor05/eszkozok/hf_jellemzo05.py egyezes --szelet D_dev --n 100 --ismetles 5 --out kor05/eredmenyek/F1/egyezes
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
import time
from bisect import bisect_left, bisect_right
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor03/eszkozok"), str(EXP / "eszkozok")]
from allapot05 import content_state, gold_set, rows  # noqa: E402
from common import BF16_BASE, labels_for, permutation, restricted, label_mass, write_json, write_jsonl  # noqa: E402
from kozos03 import GENERIC, messages  # noqa: E402

LAYERS = (20, 28, 40)
SZELETEK = EXP / "kor05/adat/szeletek05.json"
ITEM_FILES = ("kor03/adat/f3/mvp_train_v2.jsonl", "kor03/adat/f2/items_val.jsonl", "kor03/adat/f2/items_eval.jsonl")
FIT_SEED = "k05-fit:20261028"
SHARD = 1000
GLOBAL_SPANS = ("rendszer", "utasitas", "adat", "fejlec", "sablon")


# --- itemek és permutációk -------------------------------------------------------------------------------------------

def load_items(names: list[str]) -> list[dict]:
    sz = json.loads(SZELETEK.read_text())
    want = []
    for n in names:
        want += sz["szeletek"][n]["ids"]
    by = {}
    for f in ITEM_FILES:
        for it in rows(EXP / f):
            by[it["id"]] = it
    return [by[i] for i in want]


def perms_for(item: dict, mod: str) -> list[int]:
    if mod == "kanonikus":
        return [0]
    if mod == "fit":
        return [int(hashlib.sha256(f"{FIT_SEED}|{item['id']}".encode()).hexdigest(), 16) % 4]
    if mod == "b1":
        return [1, 2, 3]
    raise ValueError(mod)


# --- spanok ----------------------------------------------------------------------------------------------------------

def char_spans(item: dict, order: list[str | None], msgs: list[dict]) -> dict[str, tuple[int, int] | list]:
    """Karakter-spanok a felhasználói (és a rendszer-) üzeneten belül: {"opciok": [(a, b), …], név: (a, b)}."""
    user = msgs[-1]["content"]
    labs = labels_for(order)
    starts, pos = [], 0
    for lab in labs:
        j = user.find(f"\n{lab}) ", pos)
        if j < 0:
            raise ValueError(f"{item['id']}: a(z) {lab}) opciósor nincs a promptban")
        starts.append(j + 1)
        pos = j + 1
    opts = [(s + len(lab) + 2, (starts[n + 1] - 1) if n + 1 < len(starts) else len(user))
            for n, (lab, s) in enumerate(zip(labs, starts))]
    header = user.rfind("\n", 0, starts[0] - 1) + 1  # az opciófejléc sorának eleje
    out: dict = {"opciok": opts, "fejlec": (header, starts[0] - 1)}
    if "native" in item:
        first = user.find("\n")
        out["utasitas"] = (0, first)
        out["adat"] = (first + 1, header - 1)
    else:
        f = GENERIC[item["lang"]]
        q = f"{f['question']}: {item['question']}"
        qi = user.find(q)
        if qi < 0:
            raise ValueError(f"{item['id']}: a kérdéssor nincs a promptban")
        out["utasitas"] = (qi, qi + len(q))
        st = (item.get("state") or "").strip()
        si = user.find(st) if st else -1
        out["adat"] = (si, si + len(st)) if si >= 0 else (0, 0)
    return out


class Spanner:
    """A prompt tokenjei és a spanok tokenindexei; a token-sor bájtra a PromptTokenizer.encode-é."""

    def __init__(self, pt):
        self.pt = pt

    def build(self, item: dict, order: list[str | None]) -> dict:
        msgs = messages(item, order)
        text = self.pt.chat_text(msgs)
        enc = self.pt.tok(text, add_special_tokens=False, return_offsets_mapping=True)
        ids, offs = enc["input_ids"], enc["offset_mapping"]
        if ids != self.pt.tok.encode(text, add_special_tokens=False):
            raise ValueError(f"{item['id']}: az offsetes tokenizálás eltér az encode-tól")
        user, system = msgs[-1]["content"], msgs[0]["content"] if msgs[0]["role"] == "system" else ""
        if text.count(user) != 1:
            raise ValueError(f"{item['id']}: a felhasználói üzenet nem egyértelműen található")
        u0, s0 = text.find(user), (text.find(system) if system else -1)
        cs = char_spans(item, order, msgs)

        starts, ends = [x for x, _ in offs], [y for _, y in offs]

        def tok_span(a: int, b: int) -> list[int]:
            """A [a, b) karaktersávot metsző tokenek (az offsetek monotonok); a nulla hosszú tokenek kimaradnak."""
            if b <= a:
                return []
            return [t for t in range(bisect_right(ends, a), bisect_left(starts, b)) if offs[t][1] > offs[t][0]]

        opt = [tok_span(u0 + a, u0 + b) for a, b in cs["opciok"]]
        spans = {"rendszer": tok_span(s0, s0 + len(system)) if system else [],
                 **{k: tok_span(u0 + cs[k][0], u0 + cs[k][1]) for k in ("utasitas", "adat", "fejlec")}}
        used = {t for s in [*opt, *spans.values()] for t in s}
        spans["sablon"] = [t for t in range(len(ids)) if t not in used]
        if any(not s for s in opt):
            raise ValueError(f"{item['id']}: üres opció-span")
        return {"ids": ids, "opt": opt, "spans": spans, "text": text, "offs": offs}


# --- attention-sor rögzítése -----------------------------------------------------------------------------------------

_CAP: dict = {"on": False, "rows": {}}


def install_capture(layers: tuple[int, ...]) -> None:
    """Az SDPA-függvény burkolása: a kimenet változatlan; a kért rétegekben (1-alapú index = layer_idx + 1) az utolsó
    query-pozíció softmax-sora fp32-ben, fejenként (H × S)."""
    import torch
    from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS

    orig = ALL_ATTENTION_FUNCTIONS["sdpa"]
    want = {i - 1 for i in layers}

    def wrapped(module, query, key, value, attention_mask, **kw):
        out = orig(module, query, key, value, attention_mask, **kw)
        li = getattr(module, "layer_idx", None)
        if _CAP["on"] and li in want:
            q = query[:, :, -1:, :].float()
            k = key.float().repeat_interleave(query.shape[1] // key.shape[1], dim=1)  # a transformers repeat_kv-je
            scale = kw.get("scaling") or getattr(module, "scaling", None) or q.shape[-1] ** -0.5
            _CAP["rows"][li + 1] = torch.softmax((q @ k.transpose(-1, -2)).squeeze(2) * scale, -1)[0]
        return out

    ALL_ATTENTION_FUNCTIONS["sdpa"] = wrapped
    assert ALL_ATTENTION_FUNCTIONS.get_interface("sdpa", None) is wrapped


# --- kivonás ---------------------------------------------------------------------------------------------------------

def load_model(path: Path):
    import torch
    from transformers import AutoModelForCausalLM

    model, info = AutoModelForCausalLM.from_pretrained(str(path), dtype=torch.bfloat16, device_map="cuda",
                                                       attn_implementation="sdpa", output_loading_info=True)
    bad = {k: v for k, v in info.items() if v}
    if bad:
        raise SystemExit(f"BETÖLTÉSI KAPU BUKOTT: {json.dumps({k: sorted(v)[:20] for k, v in bad.items()})}")
    if model.config._attn_implementation != "sdpa":
        raise SystemExit(f"nem SDPA: {model.config._attn_implementation}")
    model.eval()
    return model


def forward(model, pt, sp: Spanner, item: dict, perm: int, features: bool) -> tuple[dict, dict | None]:
    import torch

    order = permutation(item, perm)
    labs = labels_for(order)
    b = sp.build(item, order)
    x = torch.tensor([b["ids"]], device="cuda")
    _CAP["on"], _CAP["rows"] = features, {}
    out = model(x, logits_to_keep=1, output_hidden_states=features)
    _CAP["on"] = False
    logp = torch.log_softmax(out.logits[0, -1].float(), -1)
    llp = {lab: logp[pt.label_ids[lab]].item() for lab in labs}
    probs = restricted(llp)
    pred = max(probs, key=probs.get)
    gold = item.get("gold")
    row = {"id": item["id"], "split": item["split"], "family": item["family"], "perm": perm, "order": order,
           "labels": labs, "gold_label": next((lab for oid, lab in zip(order, labs) if oid == gold), "X"),
           "content_state": content_state(item), "gold_set": gold_set(item), "ketertelmu": bool(item.get("ketertelmu")),
           "pred": pred, "conf": probs[pred], "probs": probs, "label_logprobs": llp, "label_mass": label_mass(llp),
           "entropy_vocab": float(-(logp.exp() * logp).sum().item()), "n_prompt_tokens": len(b["ids"]), "engine": "hf"}
    if not features:
        return row, None
    hs = out.hidden_states
    last = len(b["ids"]) - 1
    h_last = torch.stack([hs[i][0, last] for i in LAYERS]).to(torch.float16).cpu()
    h_end = torch.stack([torch.stack([hs[i][0, s[-1]] for s in b["opt"]]) for i in LAYERS]).to(torch.float16).cpu()
    h_mean = torch.stack([torch.stack([hs[i][0, s].mean(0) for s in b["opt"]]) for i in LAYERS]).to(torch.float16).cpu()
    names = [f"opt:{lab}" for lab in labs] + list(GLOBAL_SPANS)
    idx = [*b["opt"], *(b["spans"][k] for k in GLOBAL_SPANS)]
    if set(_CAP["rows"]) != set(LAYERS):
        raise SystemExit(f"az attention-sor nem minden rétegen készült el: {sorted(_CAP['rows'])}")
    attn = torch.stack([torch.stack([_CAP["rows"][i][:, s].sum(-1) if s else torch.zeros(_CAP["rows"][i].shape[0],
                                                                                         device="cuda")
                                     for s in idx], -1) for i in LAYERS])  # (3, H, n_span)
    amax = torch.stack([torch.stack([_CAP["rows"][i].mean(0)[s].max() if s else torch.zeros((), device="cuda")
                                     for s in idx]) for i in LAYERS])  # diagnosztika: fejátlag, span-maximum
    feat = {"h_last": h_last, "h_opt_end": h_end, "h_opt_mean": h_mean, "attn_span": attn.to(torch.float16).cpu(),
            "attn_max": amax.to(torch.float16).cpu(), "span_names": names, "span_len": [len(s) for s in idx],
            "span_start": [s[0] if s else -1 for s in idx]}
    return row, feat


def kivon(a) -> None:
    """Egy modellbetöltéssel több feladat (`SZELET:MOD`), feladatonként `<out-root>/<szelet>__<mod>/` alá, 1000-es
    shardokban; a kész shard újraindításkor kimarad. A STATUS-fájl shardonként a hátralévő időt és a várható véget írja."""
    import torch

    from common import PromptTokenizer  # noqa: PLC0415

    tasks = []
    for f in a.feladat:
        szelet, mod = f.rsplit(":", 1)
        items = load_items([szelet])[: a.limit or None]
        tasks.append((szelet, mod, [(it, p) for it in items for p in perms_for(it, mod)]))
    total = sum(len(j) for _, _, j in tasks)
    model = load_model(Path(a.base))
    install_capture(LAYERS)
    pt = PromptTokenizer(a.base)
    sp = Spanner(pt)
    t0, n_done, n_new = time.time(), 0, 0
    status = Path(a.status) if a.status else None
    with torch.inference_mode():
        for szelet, mod, jobs in tasks:
            features = mod != "b1"
            out = Path(a.out_root) / f"{szelet.replace(':', '_')}__{mod}"
            out.mkdir(parents=True, exist_ok=True)
            shards = [jobs[i:i + SHARD] for i in range(0, len(jobs), SHARD)]
            t1, m = time.time(), 0
            for k, sh in enumerate(shards):
                fr, ff = out / f"sorok_{k:04d}.jsonl", out / f"jellemzok_{k:04d}.pt"
                if fr.exists() and (ff.exists() or not features):
                    n_done += len(sh)
                    continue
                rs, fs = [], []
                for it, p in sh:
                    r, f = forward(model, pt, sp, it, p, features)
                    rs.append(r)
                    if f is not None:
                        fs.append({"id": it["id"], "perm": p, **f})
                if features:
                    torch.save(fs, ff.with_suffix(".tmp"))
                    ff.with_suffix(".tmp").replace(ff)
                write_jsonl(fr, rs)
                n_done, n_new, m = n_done + len(sh), n_new + len(sh), m + len(sh)
                msg = f"{szelet}:{mod} shard {k + 1}/{len(shards)} · összesen {eta_new(n_done, n_new, total, t0)}"
                print("  " + msg, flush=True)
                if status:
                    status.write_text(msg + "\n")
            write_json(out / "osszegzes.json", {"szelet": szelet, "mod": mod, "n": len(jobs), "retegek": LAYERS,
                                                "item_per_s_ebben_a_futasban": round(m / max(1e-9, time.time() - t1), 3),
                                                "kesz": datetime.now().isoformat(timespec="seconds")})


def eta_new(done: int, new: int, total: int, t0: float) -> str:
    """Hátralévő idő és várható vég (óra:perc); a sebesség csak az ebben a futásban számolt itemekből, hogy
    újraindításkor a kész shardok ne torzítsanak."""
    el = time.time() - t0
    left = el / max(1, new) * (total - done)
    return f"{done}/{total} · hátra ~{left / 60:.0f} perc · várható vége {(datetime.now() + timedelta(seconds=left)):%H:%M}"


def egyezes(a) -> None:
    """Forrásterv P1: (1) az instrumentált és a nem instrumentált forward logitjai bájtra azonosak; (2) ugyanazon n item
    ismétléseinél a top-címke és a jellemzők eltérése; (3) memóriacsúcs és p50/p95 idő mindkét úton."""
    import torch

    from common import PromptTokenizer  # noqa: PLC0415

    items = load_items(a.szelet.split(","))
    rng = random.Random(a.seed)
    items = rng.sample(items, min(a.n, len(items)))
    model = load_model(Path(a.base))
    install_capture(LAYERS)
    pt = PromptTokenizer(a.base)
    sp = Spanner(pt)

    def run(features: bool):
        torch.cuda.reset_peak_memory_stats()
        res, times = [], []
        with torch.inference_mode():
            for it in items:
                torch.cuda.synchronize()
                t = time.perf_counter()
                res.append(forward(model, pt, sp, it, 0, features))
                torch.cuda.synchronize()
                times.append(time.perf_counter() - t)
        times.sort()
        return res, {"p50_s": times[len(times) // 2], "p95_s": times[int(len(times) * 0.95)],
                     "csucs_GiB": torch.cuda.max_memory_allocated() / 2**30}

    with torch.inference_mode():  # bemelegítés: az első hívások kernel-betöltése ne torzítsa a p95-öt
        for it in items[:3]:
            forward(model, pt, sp, it, 0, True)
            forward(model, pt, sp, it, 0, False)
    plain, perf_plain = run(False)
    reps, perf_inst = [], None
    for _ in range(a.ismetles):
        r, perf_inst = run(True)
        reps.append(r)
    byte_eq = sum(all(p[0]["label_logprobs"][k] == q[0]["label_logprobs"][k] for k in p[0]["labels"])
                  for p, q in zip(plain, reps[0]))
    top_flip = [sum(a_[0]["pred"] != b_[0]["pred"] for a_, b_ in zip(reps[0], r)) for r in reps[1:]]
    h_diff = [max(float((a_[1]["h_last"].float() - b_[1]["h_last"].float()).abs().max()) for a_, b_ in zip(reps[0], r))
              for r in reps[1:]]
    at_diff = [max(float((a_[1]["attn_span"].float() - b_[1]["attn_span"].float()).abs().max())
                   for a_, b_ in zip(reps[0], r)) for r in reps[1:]]
    res = {"n": len(items), "ismetles": a.ismetles,
           "instrumentalt_vs_nem_bajtra_azonos_logprob": f"{byte_eq}/{len(items)}",
           "top_cimke_billenes_ismetlesenkent": top_flip, "h_last_max_abs_elteres": h_diff,
           "attn_span_max_abs_elteres": at_diff, "teljesitmeny_nem_instrumentalt": perf_plain,
           "teljesitmeny_instrumentalt": perf_inst}
    write_json(Path(a.out) / "egyezes.json", res)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if byte_eq != len(items):
        raise SystemExit("KAPU BUKOTT: az instrumentáció megváltoztatta a kimenetet")


def spanok(a) -> None:
    """CPU-ellenőrzés modell nélkül: minden itemen a spanok épsége; 30 véletlen példa kézi átnézésre."""
    from common import PromptTokenizer  # noqa: PLC0415

    pt = PromptTokenizer(a.tokenizer)
    sp = Spanner(pt)
    items = load_items(a.szelet.split(","))
    bad, n, lens = [], 0, []
    norm = lambda s: " ".join(s.split())  # noqa: E731
    for it in items:
        for p in ([0, 1] if a.perms_is else [0]):
            order = permutation(it, p)
            try:
                b = sp.build(it, order)
            except ValueError as e:
                bad.append(str(e))
                continue
            n += 1
            lens.append(len(b["ids"]))
            opts = {o["id"]: o for o in it["options"]}
            for oid, s in zip(order, b["opt"]):
                got = norm(pt.tok.decode([b["ids"][t] for t in s]))
                want = norm(opts[oid]["text"]) if oid is not None else None
                if want is not None and want[:40] not in got:
                    bad.append(f"{it['id']}: opció-span eltér ({want[:40]!r} ∉ {got[:80]!r})")
    rng = random.Random(a.seed)
    sample = rng.sample(items, min(30, len(items)))
    md = ["# Span-ellenőrzés — 30 véletlen példa (05-runbook 5.1; publikus 03-adat)", ""]
    for it in sample:
        order = permutation(it, 0)
        b = sp.build(it, order)
        dec = lambda s: pt.tok.decode([b["ids"][t] for t in s]).replace("\n", "⏎")  # noqa: E731
        md += [f"## {it['id']} ({it['family']}, {it.get('lang')}, {'natív' if 'native' in it else 'generikus'})", ""]
        for k in ("utasitas", "adat", "fejlec"):
            md.append(f"- **{k}** ({len(b['spans'][k])} token): `{dec(b['spans'][k])[:160]}`")
        for lab, s in zip(labels_for(order), b["opt"]):
            md.append(f"- **{lab}** ({len(s)} token, utolsó: `{pt.tok.decode([b['ids'][s[-1]]])!r}`): `{dec(s)[:120]}`")
        md.append(f"- **sablon** ({len(b['spans']['sablon'])} token); utolsó prompttoken: "
                  f"`{pt.tok.decode([b['ids'][-1]])!r}`")
        md.append("")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "minta30.md").write_text("\n".join(md), encoding="utf-8")
    lens.sort()
    res = {"n_prompt": n, "hibak": len(bad), "hiba_peldak": bad[:20],
           "tokenszam": {"median": lens[len(lens) // 2], "p99": lens[int(len(lens) * 0.99)], "max": lens[-1]} if lens
           else None}
    write_json(out / "spanok.json", res)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if bad:
        raise SystemExit(f"SPAN-HIBA: {len(bad)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("spanok")
    s.add_argument("--szelet", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--tokenizer", default=str(BF16_BASE))
    s.add_argument("--perms-is", action="store_true", help="a perm 1 is (a permutált sorrend spanjai)")
    s.add_argument("--seed", type=int, default=20261028)
    k = sub.add_parser("kivon")
    k.add_argument("--feladat", action="append", required=True, help="SZELET:MOD, MOD ∈ kanonikus | fit | b1; ismételhető")
    k.add_argument("--out-root", required=True)
    k.add_argument("--status", default="")
    k.add_argument("--base", default=str(BF16_BASE))
    k.add_argument("--limit", type=int, default=0)
    e = sub.add_parser("egyezes")
    e.add_argument("--szelet", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--base", default=str(BF16_BASE))
    e.add_argument("--n", type=int, default=100)
    e.add_argument("--ismetles", type=int, default=5)
    e.add_argument("--seed", type=int, default=20261028)
    a = ap.parse_args()
    {"spanok": spanok, "kivon": kivon, "egyezes": egyezes}[a.cmd](a)


if __name__ == "__main__":
    main()
