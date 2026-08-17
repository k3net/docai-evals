"""F3 — LoRA-tréning. Ez a szkript a GPU-s gépen fut, konténerben.

Egyetlen szkript szolgálja ki az összes ablációt (modell, rank, célrétegek,
epoch, seed), mert csak így összevethetők a futások. Minden futás egy
`run.json`-t ír, amiben ott van MINDEN, ami a reprodukcióhoz kell: modell,
seed, LoRA-konfiguráció, korpusz-hash, a dataset mérete és a mért idő.

Két, a runbookból hiányzó, de a gyakorlatban kritikus döntés:

**(1) Unsloth helyett sima PEFT + TRL.** Az eredeti runbook Unslothot javasol,
de az a 35B MoE memóriaszorítása miatt kellett. Egy 9B dense modell bf16-ban
~18 GB — a GB10 130 GB-jában bőven elfér, tehát nincs miért egy plusz
függőségi réteget behozni aarch64-en. Kevesebb kockázat, ugyanaz az eredmény.

**(2) A LoRA CSAK a nyelvi toronyra megy.** A Qwen3.5 multimodális
(`Qwen3_5ForConditionalGeneration`), és a látómodulban is vannak `q_proj`
nevű rétegek. Egy naiv `target_modules=["q_proj", ...]` felrakná az adaptert
a képfeldolgozóra is: elpazarolt paraméter, lassabb tréning, és a mérés is
zavarossá válna. Ezért a célrétegeket regexszel, a nyelvi névtérre szűkítve
adjuk meg — és a szkript kiírja, hány modult talált.

    python3 src/train_lora.py --author arany --model Qwen/Qwen3.5-9B
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

# ⚠️ A Qwen3.5 HIBRID architektúra, és ez felborítja a bevett LoRA-receptet.
# A 2B-ben 24 rétegből mindössze 6 (a 3., 7., 11., …) klasszikus attention
# `q_proj/k_proj/v_proj/o_proj` névvel; a maradék 18 réteg `Qwen3_5GatedDeltaNet`
# lineáris figyelem, ahol a vetítők neve `in_proj_qkv / in_proj_a / in_proj_b /
# in_proj_z / out_proj`. A szokásos „attention-only” célkészlet tehát a
# token-keverő rétegek HÁROMNEGYEDÉT kihagyja — nem azt méri, amit hisz róla.
# Ezért van külön `attn` (csak a full attention) és `mixer` (mindkét fajta).
TARGET_SETS = {
    # a bevett recept — itt szándékosan féloldalas, épp ezt akarjuk megmérni
    "attn": ("q_proj", "k_proj", "v_proj", "o_proj"),
    # a lineáris figyelem (GatedDeltaNet) vetítői
    "linattn": ("in_proj_qkv", "in_proj_a", "in_proj_b", "in_proj_z", "out_proj"),
    # minden token-keverő réteg: a valódi „attention-only” megfelelője
    "mixer": ("q_proj", "k_proj", "v_proj", "o_proj",
              "in_proj_qkv", "in_proj_a", "in_proj_b", "in_proj_z", "out_proj"),
    "mlp": ("gate_proj", "up_proj", "down_proj"),
    "all": ("q_proj", "k_proj", "v_proj", "o_proj",
            "in_proj_qkv", "in_proj_a", "in_proj_b", "in_proj_z", "out_proj",
            "gate_proj", "up_proj", "down_proj"),
}

SYSTEM_PROMPT = "Magyar költő vagy. A válaszod kizárólag a kért vers legyen, magyarázat nélkül."


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--author", required=True, choices=["arany", "petofi"])
    ap.add_argument("--model", default="Qwen/Qwen3.5-9B")
    ap.add_argument("--rank", type=int, default=32)
    ap.add_argument("--alpha", type=int, default=0, help="0 = 2*rank (fix alfa/rank arány)")
    ap.add_argument("--dropout", type=float, default=0.05)
    ap.add_argument("--targets", default="attn", choices=sorted(TARGET_SETS))
    ap.add_argument("--epochs", type=float, default=4.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--accum", type=int, default=4)
    # A tanítópéldák mediánja ~230 token, p90 ~790. A 2048-as ablakkal a
    # számítás ~83%-a padding-tokenre menne el; 1024-nél a példák 96%-a
    # csonkítatlanul befér. Ez mérés, nem tipp — ld. reports/08_teljesitmeny.md.
    ap.add_argument("--max-length", type=int, default=1024)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--save-frac", type=float, default=0.25,
                    help="checkpoint ilyen epoch-törtenként (A1 abláció)")
    ap.add_argument("--max-steps", type=int, default=-1, help="smoke-teszthez")
    # ⚠️ ALAPÉRTELMEZÉSBEN KI. A BFD packing 2,6× gyorsulást adna, de a TRL
    # figyelmeztet: packing mellett CSAK flash-attention variánsokkal garantált,
    # hogy a csomagba fűzött példák ne lássák egymást. A GB10-en (sm_121)
    # nincs flash-attn, az `sdpa` mellett tehát kereszt-szennyeződés fenyeget:
    # a modell egy vers tanulása közben látná az előzőt. A mérés integritása
    # fontosabb a sebességnél.
    ap.add_argument("--packing", type=int, default=0, help="1 = BFD packing (ld. a kommentet!)")
    # ⚠️ NE állítsd 0-ra. A GatedDeltaNet torch-fallbackje (nincs fast path)
    # a backwardhoz minden köztes rekurrens állapotot megőriz, és a GB10
    # unified memóriájában ez az EGÉSZ GÉPET elviszi, nem csak a folyamatot:
    # a batch=8/gc=0 próbán a node újraindult. Mérés, nem óvatosság.
    ap.add_argument("--grad-ckpt", type=int, default=1,
                    help="1 = gradient checkpointing (KELL, ld. a kommentet)")
    ap.add_argument("--data", default=str(Path(__file__).resolve().parent.parent / "data"))
    ap.add_argument("--out", default=str(Path.home() / "lora-study" / "runs"))
    ap.add_argument("--run-id", default="")
    ap.add_argument("--print-modules", action="store_true", help="csak a modulnevek kiírása")
    return ap.parse_args()


def load_split(data_dir: Path, author: str, split: str) -> list[dict]:
    """jsonl → TRL „conversational prompt-completion” formátum.

    A chat template alkalmazását a TRL végzi a tokenizerrel, tehát a dataset
    modellfüggetlen marad — ugyanez a fájl megy a 2B-re és a 9B-re is.
    """
    rows = []
    path = data_dir / "dataset" / author / f"{split}.jsonl"
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            ex = json.loads(line)
            rows.append(
                {
                    "prompt": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": ex["prompt"]},
                    ],
                    "completion": [{"role": "assistant", "content": ex["completion"]}],
                    "task": ex["task"],
                }
            )
    return rows


def resolve_targets(model, names: tuple[str, ...]) -> tuple[list[str], int, int]:
    """A célmodulok feloldása a NYELVI toronyra szűkítve.

    Visszaad: (modulnév-lista, talált nyelvi modul, kihagyott vizuális modul).
    """
    language, vision = [], 0
    for full_name, _ in model.named_modules():
        leaf = full_name.rsplit(".", 1)[-1]
        if leaf not in names:
            continue
        if any(tag in full_name for tag in ("visual", "vision_tower", "vision_model", "image")):
            vision += 1
        else:
            language.append(full_name)
    return language, len(language), vision


def main() -> int:
    args = parse_args()
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
    from trl import SFTConfig, SFTTrainer

    set_seed(args.seed)
    data_dir = Path(args.data)
    alpha = args.alpha or 2 * args.rank
    run_id = args.run_id or (
        f"{args.author}_{Path(args.model).name}_{args.targets}_r{args.rank}"
        f"_e{args.epochs:g}_s{args.seed}"
    )
    out_dir = Path(args.out) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[{run_id}] modell betöltése: {args.model}")
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        dtype=torch.bfloat16,
        # NEM "auto"/"sequential": a unified memory miatt a sharded betöltés
        # a page cache-t és a CUDA-tenzorokat ugyanabból a poolból eszi.
        device_map={"": torch.cuda.current_device()},
        attn_implementation="sdpa",
    )
    load_s = time.time() - t0
    print(f"    betöltve {load_s:.0f} s alatt · {sum(p.numel() for p in model.parameters())/1e9:.2f}B paraméter")

    targets, n_lang, n_vision = resolve_targets(model, TARGET_SETS[args.targets])
    n_layers = len({int(p) for t in targets for p in t.split(".") if p.isdigit()})
    total_layers = len(getattr(model, "model", model).layers)
    print(f"    célmodulok ({args.targets}): {n_lang} nyelvi modul "
          f"{n_layers}/{total_layers} rétegben, {n_vision} vizuális KIHAGYVA")
    if args.print_modules:
        for name in targets[:8]:
            print("      ", name)
        return 0
    if not targets:
        print("HIBA: egyetlen célmodul sem található — ellenőrizd a TARGET_SETS neveit")
        return 1

    peft_config = LoraConfig(
        r=args.rank,
        lora_alpha=alpha,
        lora_dropout=args.dropout,
        target_modules=targets,  # teljes modulnevek, vizuális torony nélkül
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"    tanítható: {trainable/1e6:.1f}M / {total/1e9:.2f}B ({trainable/total:.3%})")

    train_rows = load_split(data_dir, args.author, "train")
    val_rows = load_split(data_dir, args.author, "val")
    train_ds = Dataset.from_list(train_rows)
    val_ds = Dataset.from_list(val_rows)
    print(f"    dataset: {len(train_ds)} train / {len(val_ds)} val példa")

    steps_per_epoch = max(1, len(train_ds) // (args.batch * args.accum))
    save_steps = max(1, int(steps_per_epoch * args.save_frac))
    print(f"    {steps_per_epoch} lépés/epoch · checkpoint minden {save_steps}. lépésnél "
          f"({args.save_frac:g} epoch)")

    sft_config = SFTConfig(
        output_dir=str(out_dir),
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=args.batch,
        gradient_accumulation_steps=args.accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        bf16=True,
        # ⚠️ adamw_8bit: a CUDA 13-as konténerben eltörik (runbook 4. szakasz)
        optim="adamw_torch",
        max_length=args.max_length,
        # A példák mediánja ~230 token, p90 ~790: padding-alapú batchelésnél a
        # számítás nagy része padding-tokenre menne. A BFD (best-fit-decreasing)
        # packing több rövid példát fűz egy szekvenciába, a példahatárokat
        # position_ids-szal megőrizve — a completion-only maszkolás így is él.
        packing=bool(args.packing),
        packing_strategy="bfd",
        completion_only_loss=True,  # a promptra ne tanuljon, csak a versre
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=save_steps,
        save_strategy="steps",
        save_steps=save_steps,
        save_total_limit=None,  # az A1 epoch-görbéhez MINDEN checkpoint kell
        report_to=[],
        seed=args.seed,
        data_seed=args.seed,
        gradient_checkpointing=bool(args.grad_ckpt),
        dataset_num_proc=4,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        processing_class=tokenizer,
    )

    t1 = time.time()
    result = trainer.train()
    train_s = time.time() - t1
    trainer.save_model(str(out_dir / "final"))

    stats_path = data_dir / "dataset" / args.author / "stats.json"
    corpus_stats = json.loads(stats_path.read_text(encoding="utf-8")) if stats_path.exists() else {}
    run_log = {
        "run_id": run_id,
        "model": args.model,
        "author": args.author,
        "lora": {
            "rank": args.rank, "alpha": alpha, "dropout": args.dropout,
            "targets": args.targets, "n_target_modules": n_lang,
            "n_layers_touched": n_layers, "n_layers_total": total_layers,
            "n_vision_modules_skipped": n_vision,
            "trainable_params": trainable, "total_params": total,
        },
        "training": {
            "epochs": args.epochs, "lr": args.lr, "batch": args.batch,
            "accum": args.accum, "max_length": args.max_length, "seed": args.seed,
            "grad_checkpointing": bool(args.grad_ckpt), "packing": bool(args.packing),
            "steps_per_epoch": steps_per_epoch, "save_steps": save_steps,
            "train_examples": len(train_ds), "val_examples": len(val_ds),
        },
        "corpus": corpus_stats,
        "timing": {"load_s": round(load_s), "train_s": round(train_s)},
        "metrics": {k: float(v) for k, v in result.metrics.items()},
        "env": {
            "torch": torch.__version__,
            "gpu": torch.cuda.get_device_name(0),
            "hostname": os.uname().nodename,
        },
    }
    (out_dir / "run.json").write_text(json.dumps(run_log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[{run_id}] KÉSZ · tréning {train_s/60:.1f} perc · loss {result.metrics.get('train_loss', float('nan')):.4f}")
    print(f"    kimenet: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
