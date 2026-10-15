"""03-as kör — a G3-karok tanítása (03-runbook 4.1, 4.7, 6., 10. pont 14.).

A 00/01 receptje (eszkozok/tren_lora.py: mix+se, r16, α 32, lr 1e-4, 1 epoch, grad-accum 16, 30% perm-aug, a
döntési pozíció logits_to_keep=1-gyel, gradient checkpointing), három eltéréssel:
  - a prompt bitre azonos a 03-as kiolvasóéval: kozos03.messages, a bázis snapshotjának tokenizálója, kikapcsolt
    gondolkodás (az önteszt ellenőrzi);
  - nincs bal oldali csonkolás: a --max-len fölötti item hibát ad (a 01-es 1024 az MVP 715 itemjének elejét vágná le;
    a leghosszabb MVP-item 4476 token);
  - veszteség: CE a gold-célra ε label smoothinggal + brier_w · Brier + β · KL(p_bázis ‖ p_modell) az X-gold itemeken.
    A p_bázis az L1★ kalibrált, perm-átlagolt eloszlása (adat/f2/horgony_qwen_L1.jsonl), az adott permutáció címkéire
    vetítve. A kétértelmű itemek célja a puha gold (az item `soft` mezője). G3: β = 0,5; G3-kemény: β = 0.
Kapcsolók: --gorbe 25|50|100 (a tanulási görbe részhalmaza, mvp03.py), --csak-hu (G3-hu: az angol gerinc nélkül, H4),
--longest N (smoke: a N leghosszabb item, a memória-csúcs próbája).

Futtatás (lora-train:2, GPU; a vezénylő: kor03/eszkozok/f3_vezenylo.sh):
  python3 kor03/eszkozok/tren03.py --train kor03/adat/f3/mvp_train.jsonl --out ckpt/k03_g3_s1 --beta 0.5
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.append(str(HERE.parents[1] / "eszkozok"))
from common import (BF16_BASE, EXP, NONE_LABEL, SUBJECT_SNAPSHOT, PromptTokenizer, gold_label,  # noqa: E402
                    labels_for, permutation, read_jsonl, write_json)
from kozos03 import messages  # noqa: E402
from tren_lora import TARGET_SETS, export_vllm, save_state, target_regex  # noqa: E402

HORGONY = EXP / "kor03/adat/f2/horgony_qwen_L1.jsonl"


def is_x(it: dict) -> bool:
    return it["gold"] is None and not it.get("ketertelmu")


def load_anchor(ids: set[str]) -> dict[str, dict[str, float]]:
    out = {}
    with open(HORGONY, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r["id"] in ids:
                out[r["id"]] = r["eloszlas"]
    return out


def example(it: dict, order: list, pt: PromptTokenizer, anchor: dict | None) -> dict:
    labs = labels_for(order)
    target = [0.0] * len(labs)
    if it.get("ketertelmu"):
        soft = it["soft"]
        for oid, lab in zip(order, labs):
            target[labs.index(lab)] = float(soft.get(oid, 0.0)) if oid is not None else 0.0
        z = sum(target)
        if z <= 0:
            raise SystemExit(f"{it['id']}: a puha gold egyik megjelenített opcióra sem esik")
        target = [t / z for t in target]
    else:
        target[labs.index(gold_label(it, order))] = 1.0
    a = None
    if anchor is not None:
        a = [anchor[str(oid)] for oid in order]  # a None opció kulcsa "None"
        s = sum(a)
        a = [v / s for v in a]
    return {"id": it["id"], "ids": pt.encode(messages(it, order)), "label_ids": [pt.label_ids[x] for x in labs],
            "target": target, "anchor": a}


def build_examples(items: list[dict], pt: PromptTokenizer, anchors: dict, epoch: int, perm_aug: float,
                   seed: int) -> list[dict]:
    ex = []
    for it in items:
        order = permutation(it, epoch)
        if perm_aug and random.Random(f"{seed}|{it['id']}|aug|{epoch}").random() < perm_aug:
            order = permutation(it, 1000 + epoch)
        ex.append(example(it, order, pt, anchors.get(it["id"]) if is_x(it) else None))
    return ex


def loss_fn(z: torch.Tensor, t: torch.Tensor, a: torch.Tensor | None, eps: float, brier_w: float,
            beta: float) -> tuple[torch.Tensor, float, float, float]:
    k = z.numel()
    t_s = (1 - eps) * t + eps / k
    logp = torch.log_softmax(z, -1)
    ce = -(t_s * logp).sum()
    brier = ((logp.exp() - t) ** 2).sum()
    loss = ce + brier_w * brier
    kl = 0.0
    if a is not None and beta > 0:
        klt = (a * (a.clamp_min(1e-12).log() - logp)).sum()
        loss = loss + beta * klt
        kl = klt.item()
    return loss, ce.item(), brier.item(), kl


def selftest(base, pt: PromptTokenizer, items: list[dict], anchors: dict, out: Path) -> None:
    """Döntési pozíció, cél, horgony-vetítés és a kiolvasóval azonos prompt, három normál és két X-gold itemen."""
    import importlib

    kiolvaso = importlib.import_module("kiolvaso03")
    tok_r = kiolvaso.Tok(str(SUBJECT_SNAPSHOT))
    pick = [it for it in items if not is_x(it)][:3] + [it for it in items if is_x(it)][:2]
    res = []
    with torch.inference_mode():
        for it in pick:
            order = permutation(it, 1)
            ex = example(it, order, pt, anchors.get(it["id"]) if is_x(it) else None)
            x = torch.tensor([ex["ids"]], device="cuda")
            last = base(x, logits_to_keep=1).logits[0, -1].float()
            full_all = base(x).logits[0].float()
            labs = labels_for(order)
            g = gold_label(it, order) if not it.get("ketertelmu") else labs[max(range(len(labs)), key=lambda i: ex["target"][i])]
            r = {"id": it["id"], "x": is_x(it),
                 "max_abs_diff_last_vs_full": float((last - full_all[-1]).abs().max()),
                 "max_abs_diff_last_vs_prev": float((last - full_all[-2]).abs().max()),
                 "target_ok": labs[max(range(len(labs)), key=lambda i: ex["target"][i])] == g,
                 "prompt_azonos_a_kiolvasoval": ex["ids"] == tok_r.encode(messages(it, order)),
                 "label_follows_prompt": pt.tok.encode(pt.tok.decode(ex["ids"]) + g, add_special_tokens=False)[-1] == pt.label_ids[g]}
            if is_x(it):
                a = ex["anchor"]
                r["horgony_osszeg"] = sum(a)
                r["horgony_x_egyezik"] = abs(a[labs.index(NONE_LABEL)] - anchors[it["id"]]["None"] / sum(anchors[it["id"]].values())) < 1e-9
            res.append(r)
    ok = all(r["target_ok"] and r["prompt_azonos_a_kiolvasoval"] and r["label_follows_prompt"]
             and r["max_abs_diff_last_vs_full"] < 0.25 and r["max_abs_diff_last_vs_prev"] > 1.0
             and (not r["x"] or (abs(r["horgony_osszeg"] - 1) < 1e-6 and r["horgony_x_egyezik"])) for r in res)
    write_json(out / "selftest.json", {"ok": ok, "items": res})
    print(json.dumps({"ok": ok, "items": res}, ensure_ascii=False))
    raise SystemExit(0 if ok else 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--targets", default="mix+se", choices=sorted(TARGET_SETS))
    ap.add_argument("--r", type=int, default=16)
    ap.add_argument("--alpha", type=int, default=32)
    ap.add_argument("--dropout", type=float, default=0.05)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--max-steps", type=int, default=0, help="optimalizáló-lépés felső korlát (0 = epoch szerint)")
    ap.add_argument("--grad-accum", type=int, default=16)
    ap.add_argument("--warmup", type=float, default=0.03)
    ap.add_argument("--eps", type=float, default=0.05)
    ap.add_argument("--brier", type=float, default=0.5)
    ap.add_argument("--beta", type=float, required=True, help="bázis-horgony súlya (G3: 0,5; G3-kemény: 0)")
    ap.add_argument("--perm-aug", type=float, default=0.3)
    ap.add_argument("--max-len", type=int, default=5120)
    ap.add_argument("--gorbe", type=int, default=100, choices=[25, 50, 100])
    ap.add_argument("--csak-hu", action="store_true", help="G3-hu: az angol itemek nélkül (H4)")
    ap.add_argument("--save-every", type=int, default=100)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--longest", type=int, default=0, help="smoke: a N leghosszabb item")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    out = Path(args.out)
    if not out.is_absolute():
        out = EXP / out
    out.mkdir(parents=True, exist_ok=True)
    if (out / "final" / "adapter_model.safetensors").exists() and not args.selftest:
        print(f"{out}: kész (final), kihagyva")
        return
    random.seed(args.seed)
    torch.manual_seed(args.seed)

    pt = PromptTokenizer(SUBJECT_SNAPSHOT)
    items = [it for it in read_jsonl(Path(args.train) if Path(args.train).is_absolute() else EXP / args.train)
             if it.get("gorbe", 100) <= args.gorbe and not (args.csak_hu and it["lang"] == "en")]
    anchors = load_anchor({it["id"] for it in items if is_x(it)})
    if missing := [it["id"] for it in items if is_x(it) and it["id"] not in anchors]:
        raise SystemExit(f"{len(missing)} X-gold itemhez nincs horgony, pl. {missing[:3]}")
    if bad := [it["id"] for it in items if is_x(it) and set(anchors[it["id"]]) != {str(o) for o in permutation(it, 0)}]:
        raise SystemExit(f"{len(bad)} X-gold item horgonyának opciói eltérnek az itemétől, pl. {bad[:3]}")
    lens = {it["id"]: len(pt.encode(messages(it, permutation(it, 0)))) for it in items}
    if args.longest:
        items = sorted(items, key=lambda it: -lens[it["id"]])[: args.longest]
    if args.limit:
        items = items[: args.limit]
    chosen_ids = {it["id"] for it in items}
    if too_long := [i for i in chosen_ids if lens[i] > args.max_len - 16]:
        raise SystemExit(f"{len(too_long)} item hosszabb a --max-len-nél ({args.max_len}), pl. {too_long[:3]}")

    from peft import LoraConfig, PeftModel, get_peft_model
    from hf_kiolvaso import load_model

    base, _ = load_model(BF16_BASE)
    if args.selftest:
        selftest(base, pt, items, anchors, out)

    base.config.use_cache = False
    base.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    base.enable_input_require_grads()
    resume = (out / "last" / "adapter_model.safetensors").exists()
    if resume:
        model = PeftModel.from_pretrained(base, str(out / "last"), is_trainable=True)
    else:
        cfg = LoraConfig(r=args.r, lora_alpha=args.alpha, lora_dropout=args.dropout, bias="none",
                         target_modules=target_regex(args.targets))
        model = get_peft_model(base, cfg)
    n_train = sum(p.numel() for p in model.parameters() if p.requires_grad)

    steps_per_epoch = math.ceil(len(items) / args.grad_accum)
    total = args.max_steps or steps_per_epoch * args.epochs
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.0)
    warm = max(1, int(args.warmup * total))
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / warm) * 0.5 * (1 + math.cos(math.pi * min(1.0, max(0, s - warm) / max(1, total - warm)))))
    state = {"step": 0, "epoch": 0, "pos": 0, "args": vars(args), "n_trainable": n_train, "n_items": len(items),
             "n_x": sum(map(is_x, items)), "n_tokens": sum(lens[it["id"]] for it in items), "total_steps": total}
    if resume:
        st = torch.load(out / "last" / "train_state.pt", weights_only=False)
        opt.load_state_dict(st["opt"])
        sched.load_state_dict(st["sched"])
        random.setstate(st["rng"])
        torch.set_rng_state(st["torch_rng"])
        torch.cuda.set_rng_state(st["cuda_rng"])
        state = json.load(open(out / "last" / "state.json"))
        print(f"folytatás: lépés {state['step']}, epoch {state['epoch']}, pozíció {state['pos']}", flush=True)
    write_json(out / "config.json", {**state, "resumed": resume})

    log = open(out / "train_log.jsonl", "a")
    model.train()
    t0, tok_count, start_step = time.time(), 0, state["step"]
    max_epochs = 10**6 if args.max_steps else args.epochs
    while state["step"] < total and state["epoch"] < max_epochs:
        idx = list(range(len(items)))
        random.Random(f"{args.seed}|{state['epoch']}").shuffle(idx)
        exs = build_examples([items[i] for i in idx], pt, anchors, state["epoch"], args.perm_aug, args.seed)
        while state["pos"] < len(exs) and state["step"] < total:
            batch = exs[state["pos"]: state["pos"] + args.grad_accum]
            opt.zero_grad(set_to_none=True)
            lsum = cesum = brsum = klsum = 0.0
            n_kl = 0
            for ex in batch:
                if len(ex["ids"]) > args.max_len:
                    raise SystemExit(f"{ex['id']}: {len(ex['ids'])} token > --max-len (permutáció után)")
                x = torch.tensor([ex["ids"]], device="cuda")
                logits = model(input_ids=x, logits_to_keep=1).logits[0, -1].float()
                z = logits[torch.tensor(ex["label_ids"], device="cuda")]
                a = torch.tensor(ex["anchor"], device="cuda") if ex["anchor"] is not None else None
                loss, ce, br, kl = loss_fn(z, torch.tensor(ex["target"], device="cuda"), a, args.eps, args.brier, args.beta)
                (loss / len(batch)).backward()
                lsum, cesum, brsum, klsum = lsum + loss.item(), cesum + ce, brsum + br, klsum + kl
                n_kl += a is not None
                tok_count += len(ex["ids"])
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            sched.step()
            state["step"] += 1
            state["pos"] += len(batch)
            el = time.time() - t0
            rec = {"step": state["step"], "epoch": state["epoch"], "loss": lsum / len(batch), "ce": cesum / len(batch),
                   "brier": brsum / len(batch), "kl_horgony": klsum / max(1, n_kl), "n_horgony": n_kl,
                   "lr": sched.get_last_lr()[0], "tok_s": round(tok_count / el, 1),
                   "mem_gb": round(torch.cuda.max_memory_allocated() / 1e9, 1),
                   "eta_s": round(el / max(1, state["step"] - start_step) * (total - state["step"]))}
            log.write(json.dumps(rec) + "\n")
            log.flush()
            print(json.dumps(rec), flush=True)
            if state["step"] % args.save_every == 0:
                save_state(out, model, opt, sched, state)
        if state["pos"] >= len(exs):
            state["epoch"] += 1
            state["pos"] = 0
    model.save_pretrained(out / "final")
    json.dump(TARGET_SETS[args.targets], open(out / "final" / "ldh_groups.json", "w"))
    n = export_vllm(out / "final", out / "vllm")
    write_json(out / "done.json", {**state, "wall_s": round(time.time() - t0), "vllm_tensors": n})
    print(f"kész: {out}/final, vLLM-export: {out}/vllm ({n} tenzor)")


if __name__ == "__main__":
    main()
