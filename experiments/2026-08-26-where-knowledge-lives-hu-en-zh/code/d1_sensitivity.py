#!/usr/bin/env python3
"""D1 érzékenységvizsgálat — a kérdés KERETEZÉSE okozza-e a forrásnyelvi lemaradást?

    bash ~/lang-study/src/run_spark.sh src/d1_sensitivity.py

⛔⛔ MÉRT PROBLÉMA: a fagyasztott korpuszban a kínai-forrású fogalmak kérdése nyelvenként
MÁS keretet ad:
    hu:  „Mit jelent a kínai »关系« (guanxi) FOGALOM?”
    en:  „What does the Chinese CONCEPT '关系' (guanxi) mean?”
    zh:  „中文的“关系”一词是什么意思？”   ← 一词 = „szó”, sima szótári kérdés
A magyar/angol változat tehát KULTURÁLIS MAGYARÁZATOT kér, a kínai csak jelentést. Ez
önmagában megmagyarázhatja, miért ad a modell kínaiul általános szótári glosszát
(关系 = „emberek közti kapcsolat”), és miért marad ki belőle a kulturális komponens.

A korpusz fagyasztott, ezért NEM írjuk át — helyette 8 extra generálást futtatunk a
kínai-forrású fogalmakra SZIMMETRIZÁLT kínai kérdéssel (一词 → 这个概念 = „ez a fogalom”),
és megnézzük, visszahozza-e a komponenseket. Ha igen, a D1 forrásnyelvi lemaradása
KERETEZÉSI műtermék, és így kell leírni a dolgozatban.

Kimenet: results/gen_sens/{item}_zh.json
"""
import json
import pathlib
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

import gb10_patch
import scope_paths

MODEL = scope_paths.MODEL
ROOT = pathlib.Path("/work")
RES = scope_paths.res(ROOT)
STOPS = ["\nKérdés:", "\nQuestion:", "\n问题："]


def main():
    gb10_patch.patch(conv=True)
    tok = AutoTokenizer.from_pretrained(MODEL)
    think = tok.convert_tokens_to_ids("<think>")
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).to("cuda").eval()
    (RES / "gen_sens").mkdir(exist_ok=True)

    items = [json.loads(l) for l in (ROOT / "items.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    targets = [it for it in items if it.get("group") == "UNT" and it["src_lang"] == "zh"]
    print(f"{len(targets)} kínai-forrású fogalom, szimmetrizált kínai kérdéssel", flush=True)

    for it in targets:
        # 一词 („a szó”) → 这个概念 („ez a fogalom”), hogy a keret azonos legyen a hu/en változattal
        # ⚠️ Nem mind a 8 kérdés használja a `一词`-et (a 加油 pl. nem) — ott a puszta
        # „是什么意思" elé szúrjuk be a `这个概念`-et. Ha egyik sem fog, a tétel kimarad, nem hasal el.
        q0 = it["q"]["zh"]
        if "一词是什么意思" in q0:
            q = q0.replace("一词是什么意思", "这个概念是什么意思")
        elif "是什么意思" in q0:
            q = q0.replace("是什么意思", "这个概念是什么意思", 1)
        else:
            print(f"  {it['id']}: nem tudom szimmetrizálni ({q0}) — kihagyva", flush=True)
            continue
        out_f = RES / "gen_sens" / f"{it['id']}_zh.json"
        if out_f.exists():
            print(f"  {it['id']}: már megvan — kihagyva", flush=True)
            continue
        prompt = f"问题：{q}\n回答："
        torch.manual_seed(0)
        enc = tok(prompt, return_tensors="pt").to("cuda")
        with torch.no_grad():
            g = model.generate(**enc, max_new_tokens=800, do_sample=False, bad_words_ids=[[think]],
                               stop_strings=STOPS, tokenizer=tok,
                               pad_token_id=tok.pad_token_id or tok.eos_token_id)
        n_new = int(g.shape[1] - enc["input_ids"].shape[1])
        raw = tok.decode(g[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
        cut = raw
        for s in STOPS:
            cut = cut.split(s)[0]
        out_f.write_text(json.dumps({
            "item_id": it["id"], "lang": "zh", "concept": it["concept"], "prompt": prompt,
            "original_prompt": f"问题：{it['q']['zh']}\n回答：", "text": cut.strip(), "raw": raw,
            "n_new_tokens": n_new, "truncated": n_new >= 800}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {it['id']} ({it['concept']}): {n_new} token — {cut.strip()[:90]!r}", flush=True)

    print("KÉSZ")


if __name__ == "__main__":
    main()
