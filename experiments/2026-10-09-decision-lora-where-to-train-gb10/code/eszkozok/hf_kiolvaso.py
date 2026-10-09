"""HF-kiolvasás az „FP8-hű BF16” bázison (K0f betöltési kapu, K0d, F2 rejtett állapotok).

Betöltéskor KEMÉNY kapu: missing/unexpected/mismatched kulcs nem lehet — ez fogja
meg, ha az expertek csendben véletlen inicializálással maradnának. A kiolvasás
formátuma azonos a vLLM-es kiolvasóéval (kiolvaso.py), így a két motor soronként
összevethető.

Példa:
  python3 eszkozok/hf_kiolvaso.py --items adat/probe50.jsonl --out eredmenyek/F0/k0f/hf_probe.jsonl
  python3 eszkozok/hf_kiolvaso.py ... --hidden-layers 27,40 --hidden-out cache/hidden/val
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    BF16_BASE, NONE_TEXT, PPL_SZOVEGEK, PromptTokenizer, gold_label, label_mass, labels_for, permutation,
    read_jsonl, restricted, write_json, write_jsonl,
)


def load_model(path: Path, adapter: str | None = None, experts: str | None = None):
    """experts: None = a transformers alapértelmezése (grouped_mm, ha elérhető); "eager" a fake-quanthoz."""
    from transformers import AutoModelForCausalLM

    kw = {"experts_implementation": experts} if experts else {}
    model, info = AutoModelForCausalLM.from_pretrained(
        str(path), dtype=torch.bfloat16, device_map="cuda", output_loading_info=True, **kw
    )
    bad = {k: v for k, v in info.items() if v}
    if bad:
        raise SystemExit(f"BETÖLTÉSI KAPU BUKOTT: {json.dumps({k: sorted(v)[:20] for k, v in bad.items()}, ensure_ascii=False)}")
    if adapter:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, adapter)
    model.eval()
    return model, info


@torch.inference_mode()
def ppl_check(model, pt: PromptTokenizer) -> list[float]:
    out = []
    for s in PPL_SZOVEGEK:
        ids = torch.tensor([pt.tok.encode(s, add_special_tokens=False)], device="cuda")
        logits = model(ids).logits.float()
        nll = torch.nn.functional.cross_entropy(logits[0, :-1], ids[0, 1:])
        out.append(math.exp(nll.item()))
    return out


@torch.inference_mode()
def readout(model, pt: PromptTokenizer, items: list[dict], perms: list[int], prefill: str, none_text: str,
            hl: list[int], adapter: str | None) -> tuple[list[dict], dict[int, list]]:
    hidden: dict[int, list] = {i: [] for i in hl}
    rows = []
    for it in items:
        for p in perms:
            order = permutation(it, p)
            labs = labels_for(order)
            ids = pt.encode_item(it, order, prefill, NONE_TEXT[none_text])
            x = torch.tensor([ids], device="cuda")
            out = model(x, logits_to_keep=1, output_hidden_states=bool(hl))
            logp = torch.log_softmax(out.logits[0, -1].float(), -1)
            llp = {lab: logp[pt.label_ids[lab]].item() for lab in labs}
            probs = restricted(llp)
            pred = max(probs, key=probs.get)
            rows.append({
                "id": it["id"], "split": it.get("split"), "perm": p, "move_none": False,
                "order": order, "labels": labs, "gold_label": gold_label(it, order),
                "pred": pred, "conf": probs[pred], "probs": probs, "label_logprobs": llp,
                "label_mass": label_mass(llp), "sampled_id": int(logp.argmax().item()),
                "n_prompt_tokens": len(ids), "engine": "hf", "adapter": adapter,
            })
            for i in hl:
                hidden[i].append(out.hidden_states[i][0, -1].to(torch.float16).cpu())
    return rows, hidden


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--base", default=str(BF16_BASE))
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--perms", default="0")
    ap.add_argument("--prefill", default="")
    ap.add_argument("--none-text", default="alap", choices=sorted(NONE_TEXT))
    ap.add_argument("--hidden-layers", default="", help="pl. 27,40 — a hidden_states tuple indexei (0 = embedding)")
    ap.add_argument("--hidden-out", default="")
    ap.add_argument("--ppl", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--fakequant", default="none", choices=["none", "vllm", "fp32", "pow2"],
                    help="FP8 aktiváció-fake-quant (fakequant.py); a K0d-2 alapján")
    args = ap.parse_args()

    t0 = time.time()
    model, _ = load_model(Path(args.base), args.adapter, experts="eager" if args.fakequant != "none" else None)
    load_s = time.time() - t0
    fq_info = None
    if args.fakequant != "none":
        import fakequant

        fq_info = fakequant.install(model, args.fakequant)
    pt = PromptTokenizer(args.base)
    items = read_jsonl(Path(args.items))
    if args.limit:
        items = items[: args.limit]
    perms = [int(p) for p in args.perms.split(",")]
    hl = [int(x) for x in args.hidden_layers.split(",") if x]
    t1 = time.time()
    rows, hidden = readout(model, pt, items, perms, args.prefill, args.none_text, hl, args.adapter)
    write_jsonl(Path(args.out), rows)
    if hl:
        hd = Path(args.hidden_out)
        hd.mkdir(parents=True, exist_ok=True)
        for i in hl:
            torch.save(torch.stack(hidden[i]), hd / f"layer{i}.pt")
        write_jsonl(hd / "index.jsonl", [{"id": r["id"], "perm": r["perm"]} for r in rows])
    summary = {
        "n": len(rows), "acc": sum(r["pred"] == r["gold_label"] for r in rows) / max(1, len(rows)),
        "load_s": round(load_s, 1), "items_per_s": round(len(rows) / max(1e-9, time.time() - t1), 3),
        "ppl": ppl_check(model, pt) if args.ppl else None, "adapter": args.adapter, "fakequant": fq_info,
        "experts_implementation": getattr(model.config, "_experts_implementation", None),
    }
    write_json(Path(args.out).with_suffix(".summary.json"), summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
