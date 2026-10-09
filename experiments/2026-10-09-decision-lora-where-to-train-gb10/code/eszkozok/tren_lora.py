"""Döntési LoRA tréning (runbook 5. pont, L3) — saját veszteség a döntési pozíción.

- Bázis: az „FP8-hű BF16” checkpoint (K0f), betöltési kapuval.
- Célmodulok: mix = attention q/k/v/o (10 réteg) + GatedDeltaNet in_proj_qkv/z/a/b, out_proj
  (30 réteg); mix+se = + shared expert gate/up/down. A routed experteken nincs LoRA.
- Veszteség: a jelen lévő címkékre szűkített softmax; CE (opcionális label smoothing ε)
  + brier_w · Brier; kétértelmű itemeknél soft céleloszlás. A döntési pozíció a prompt
  utolsó tokenje utáni pozíció → logits_to_keep=1 (NEM TRL SFT: annak completion-maszkja
  2 tokennel elcsúszik, és pont a döntési tokent vinné el).
- Gradient checkpointing kötelező (GB10: nélküle a node indul újra).
- Checkpoint `--save-every` optimalizáló-lépésenként a <out>/last-ba (atomikusan), és
  automatikus folytatás onnan; a végén <out>/final + <out>/vllm (átnevezett kulcsokkal).
- `--perm-aug p` (01-runbook 5. pont, a JEV receptje): az itemek p hányada az adott epochban véletlen
  opció-permutációval tanul (perm-id 1000 + epoch, az értékelő 0–3-as permutációitól külön); az item-id-ből seedelt,
  így reprodukálható. A `--train` vesszős fájllistát is elfogad (01: train + EU-180k train-extra).

Futtatás (lora-train:2, GPU):
  python3 eszkozok/tren_lora.py --train adat/pilot/items_train.jsonl --out ckpt/smoke --targets mix --max-steps 20
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import shutil
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BF16_BASE, EXP, PromptTokenizer, gold_label, labels_for, permutation, read_jsonl, write_json  # noqa: E402

TARGETS = {
    "attn": r"model\.layers\.\d+\.self_attn\.(q|k|v|o)_proj",
    "gdn": r"model\.layers\.\d+\.linear_attn\.(in_proj_qkv|in_proj_z|in_proj_a|in_proj_b|out_proj)",
    "se": r"model\.layers\.\d+\.mlp\.shared_expert\.(gate|up|down)_proj",
}
TARGET_SETS = {"mix": ["attn", "gdn"], "mix+se": ["attn", "gdn", "se"], "attn": ["attn"], "gdn": ["gdn"], "se": ["se"]}
SHORT_NAMES = {"attn": ["q_proj", "k_proj", "v_proj", "o_proj"],
               "gdn": ["in_proj_qkv", "in_proj_z", "in_proj_a", "in_proj_b", "out_proj"],
               "se": ["gate_proj", "up_proj", "down_proj"]}
HF_PREFIX = "base_model.model.model.layers."
VLLM_PREFIX = "base_model.model.model.language_model.layers."


def target_regex(name: str) -> str:
    return "(" + "|".join(TARGETS[g] for g in TARGET_SETS[name]) + ")"


def export_vllm(adapter_dir: Path, out_dir: Path, rename: bool = True) -> int:
    """A PEFT-adapter vLLM-re: a kulcsok `model.language_model.` alá kerülnek (a vLLM
    Qwen3_5Moe leképezője csak ezt ismeri), a target_modules rövid nevek listája."""
    from safetensors.torch import load_file, save_file

    out_dir.mkdir(parents=True, exist_ok=True)
    sd = load_file(str(adapter_dir / "adapter_model.safetensors"))
    new = {}
    for k, v in sd.items():
        if rename and k.startswith(HF_PREFIX):
            k = VLLM_PREFIX + k[len(HF_PREFIX):]
        new[k] = v.contiguous()
    save_file(new, str(out_dir / "adapter_model.safetensors"))
    cfg = json.load(open(adapter_dir / "adapter_config.json"))
    gf = adapter_dir / "ldh_groups.json"
    groups = json.load(open(gf)) if gf.exists() else ["attn", "gdn", "se"]
    cfg["target_modules"] = sorted({n for g in groups for n in SHORT_NAMES[g]})
    json.dump(cfg, open(out_dir / "adapter_config.json", "w"), indent=2)
    return len(new)


def build_examples(items: list[dict], pt: PromptTokenizer, epoch: int, perm_aug: float = 0.0, seed: int = 1) -> list[dict]:
    ex = []
    for it in items:
        order = permutation(it, epoch)
        if perm_aug and random.Random(f"{seed}|{it['id']}|aug|{epoch}").random() < perm_aug:
            order = permutation(it, 1000 + epoch)
        labs = labels_for(order)
        ids = pt.encode_item(it, order)
        lab_ids = [pt.label_ids[lab] for lab in labs]
        target = [0.0] * len(labs)
        soft = (it.get("meta") or {}).get("soft")
        if soft:
            members = [labs[order.index(o)] for o in soft if o in order]
            for m in members:
                target[labs.index(m)] = 1.0 / len(members)
        else:
            target[labs.index(gold_label(it, order))] = 1.0
        ex.append({"id": it["id"], "ids": ids, "label_ids": lab_ids, "target": target})
    return ex


def loss_fn(z: torch.Tensor, t: torch.Tensor, eps: float, brier_w: float) -> tuple[torch.Tensor, float, float]:
    k = z.numel()
    t_s = (1 - eps) * t + eps / k
    logp = torch.log_softmax(z, -1)
    ce = -(t_s * logp).sum()
    brier = ((logp.exp() - t) ** 2).sum()
    return ce + brier_w * brier, ce.item(), brier.item()


def save_state(out: Path, model, opt, sched, state: dict) -> None:
    tmp = out / "last.tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    model.save_pretrained(tmp)
    torch.save({"opt": opt.state_dict(), "sched": sched.state_dict(), "rng": random.getstate(),
                "torch_rng": torch.get_rng_state(), "cuda_rng": torch.cuda.get_rng_state()}, tmp / "train_state.pt")
    write_json(tmp / "state.json", state)
    if (out / "last").exists():
        shutil.rmtree(out / "last")
    os.replace(tmp, out / "last")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--targets", default="mix", choices=sorted(TARGET_SETS))
    ap.add_argument("--r", type=int, default=16)
    ap.add_argument("--alpha", type=int, default=32)
    ap.add_argument("--dropout", type=float, default=0.05)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--max-steps", type=int, default=0, help="optimalizáló-lépés felső korlát (0 = epoch szerint)")
    ap.add_argument("--grad-accum", type=int, default=16)
    ap.add_argument("--warmup", type=float, default=0.03)
    ap.add_argument("--eps", type=float, default=0.0)
    ap.add_argument("--brier", type=float, default=0.5)
    ap.add_argument("--max-len", type=int, default=1024)
    ap.add_argument("--save-every", type=int, default=200)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--perm-aug", type=float, default=0.0, help="ennyi hányad tanul véletlen opció-permutációval (01: 0,3)")
    ap.add_argument("--selftest", action="store_true", help="döntési pozíció egységteszt, utána kilép")
    ap.add_argument("--fakequant", default="none", choices=["none", "fp32", "vllm", "pow2", "lin"],
                    help="FP8 aktiváció-fake-quant a forwardban (fakequant.py; F3 fake-quant kar, K0d-2)")
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

    from peft import LoraConfig, PeftModel, get_peft_model
    from hf_kiolvaso import load_model

    # betöltési kapu: missing/unexpected kulcs = hiba; a teljes fake-quant expert-útja eager
    base, _ = load_model(BF16_BASE, experts="eager" if args.fakequant not in ("none", "lin") else None)
    fq_info = None
    if args.fakequant != "none":
        import fakequant

        fq_info = fakequant.install(base, args.fakequant)  # PEFT előtt: a hook a base_layeren marad
    pt = PromptTokenizer(BF16_BASE)
    items = [it for f in args.train.split(",") for it in read_jsonl(Path(f) if Path(f).is_absolute() else EXP / f)]
    items = [it for it in items if it.get("options")]
    if args.limit:
        items = items[: args.limit]

    if args.selftest:
        res = []
        with torch.inference_mode():
            for it in items[:3]:
                order = permutation(it, 0)
                ids = pt.encode_item(it, order)
                x = torch.tensor([ids], device="cuda")
                last = base(x, logits_to_keep=1).logits[0, -1].float()
                full_all = base(x).logits[0].float()
                full, prev = full_all[-1], full_all[-2]
                g = gold_label(it, order)
                ex = build_examples([it], pt, 0)[0]
                tgt_lab = labels_for(order)[int(torch.tensor(ex["target"]).argmax())]
                res.append({"id": it["id"], "max_abs_diff_last_vs_full": float((last - full).abs().max()),
                            "max_abs_diff_last_vs_prev": float((last - prev).abs().max()),
                            "target_argmax_label": tgt_lab, "gold_label": g, "ok": tgt_lab == g or it.get("meta", {}).get("soft") is not None,
                            "label_follows_prompt": pt.tok.encode(pt.tok.decode(ids) + g, add_special_tokens=False)[-1] == pt.label_ids[g]})
        # a logits_to_keep=1 és a teljes forward utolsó pozíciója a bf16 GEMM-alak miatt nem bitazonos
        # (mért: ≤ 0,03, egy bf16-ulp alatt ~30-as logitoknál); rossz pozíció egységnyi eltérést adna,
        # ezt az utolsó előtti pozícióval szembeni eltérés igazolja
        ok = all(r["ok"] and r["max_abs_diff_last_vs_full"] < 0.25 and r["max_abs_diff_last_vs_prev"] > 1.0
                 and r["label_follows_prompt"] for r in res)
        write_json(out / "selftest.json", {"ok": ok, "items": res})
        print(json.dumps({"ok": ok, "items": res}, ensure_ascii=False))
        raise SystemExit(0 if ok else 1)

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
    n_mod = sum(1 for n, _ in model.named_modules() if n.endswith("lora_A"))

    steps_per_epoch = math.ceil(len(items) / args.grad_accum)
    total = args.max_steps or steps_per_epoch * args.epochs
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.0)
    warm = max(1, int(args.warmup * total))
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / warm) * 0.5 * (1 + math.cos(math.pi * min(1.0, max(0, s - warm) / max(1, total - warm)))))
    state = {"step": 0, "epoch": 0, "pos": 0, "args": vars(args), "n_trainable": n_train, "n_lora_modules": n_mod,
             "n_items": len(items), "total_steps": total, "fakequant": fq_info,
             "experts_implementation": getattr(base.config, "_experts_implementation", None)}
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
        order_rng = random.Random(f"{args.seed}|{state['epoch']}")
        idx = list(range(len(items)))
        order_rng.shuffle(idx)
        exs = build_examples([items[i] for i in idx], pt, state["epoch"], args.perm_aug, args.seed)
        while state["pos"] < len(exs) and state["step"] < total:
            batch = exs[state["pos"]: state["pos"] + args.grad_accum]
            opt.zero_grad(set_to_none=True)
            lsum = cesum = brsum = 0.0
            for ex in batch:
                ids = ex["ids"][-args.max_len:]
                x = torch.tensor([ids], device="cuda")
                logits = model(input_ids=x, logits_to_keep=1).logits[0, -1].float()
                z = logits[torch.tensor(ex["label_ids"], device="cuda")]
                loss, ce, br = loss_fn(z, torch.tensor(ex["target"], device="cuda"), args.eps, args.brier)
                (loss / len(batch)).backward()
                lsum, cesum, brsum = lsum + loss.item(), cesum + ce, brsum + br
                tok_count += len(ids)
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            sched.step()
            state["step"] += 1
            state["pos"] += len(batch)
            el = time.time() - t0
            rec = {"step": state["step"], "epoch": state["epoch"], "loss": lsum / len(batch), "ce": cesum / len(batch),
                   "brier": brsum / len(batch), "lr": sched.get_last_lr()[0], "tok_s": round(tok_count / el, 1),
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
