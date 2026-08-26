#!/usr/bin/env python3
"""Fázis 0 döntés: elég-e a nyers completion-sablon, vagy few-shot kell?

MÉRT PROBLÉMA: a "Base" checkpoint a `Question: …\\nAnswer:` folytatásra
`<think>` blokkot nyit és csevegni kezd — 40 tokenben a válasz meg sem
jelenik. Ez a runbook §1 (max_new_tokens=40) és §3 (a logit lens az utolsó
prompt-token residualját nézi, feltéve hogy a KÖVETKEZŐ token a válasz)
alapfeltevését dönti meg, ezért mérünk, nem tippelünk.

Két sablon, ugyanazokon az itemeken, három nyelven:
  zero  — a runbook eredeti sablonja
  few2  — két semleges Q/A minta ELŐTTE, a prompt nyelvén

    bash ~/lang-study/src/run_spark.sh src/smoke_template.py
"""
import json, pathlib, time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import gb10_patch

MODEL = "Qwen/Qwen3.5-9B-Base"
ROOT = pathlib.Path("/work")

# Semleges, a korpuszon kívüli minták — a nyelvi hatás így szimmetrikus marad
FEWSHOT = {
    "hu": "Kérdés: Mi Franciaország fővárosa?\nVálasz: Párizs\n\n"
          "Kérdés: Hány lába van a póknak?\nVálasz: nyolc\n\n",
    "en": "Question: What is the capital of France?\nAnswer: Paris\n\n"
          "Question: How many legs does a spider have?\nAnswer: eight\n\n",
    "zh": "问题：法国的首都是哪里？\n回答：巴黎\n\n"
          "问题：蜘蛛有几条腿？\n回答：八条\n\n",
}
# A generálást a következő "Kérdés:" előtt vágjuk el (few-shotnál a modell tovább folytatja)
STOP = {"hu": "\nKérdés:", "en": "\nQuestion:", "zh": "\n问题："}


def main():
    gb10_patch.patch(conv=True)
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).to("cuda").eval()
    torch.manual_seed(0)

    prompts = [json.loads(l) for l in (ROOT / "prompts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    pick = []
    for grp, kind in (("ZH", "fact"), ("HU", "fact"), ("UNI", "fact"), ("UNT", "unt")):
        ids = sorted({p["item_id"] for p in prompts if p["group"] == grp and p["kind"] == kind})[:2]
        pick += [p for p in prompts if p["item_id"] in ids and p["kind"] == kind]

    out = []
    for p in pick:
        for variant in ("zero", "few2"):
            text = (FEWSHOT[p["lang"]] if variant == "few2" else "") + p["prompt"]
            enc = tok(text, return_tensors="pt").to("cuda")
            with torch.no_grad():
                g = model.generate(**enc, max_new_tokens=p["max_new_tokens"], do_sample=False,
                                   pad_token_id=tok.pad_token_id or tok.eos_token_id)
            raw = tok.decode(g[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
            cut = raw.split(STOP[p["lang"]])[0].strip()
            rec = {"item_id": p["item_id"], "group": p["group"], "kind": p["kind"], "lang": p["lang"],
                   "variant": variant, "expected": p["expected"], "raw": raw, "cut": cut,
                   "opens_think": "<think>" in raw[:40],
                   "hit": bool(p["expected"]) and p["expected"].lower()[:12] in cut.lower()}
            out.append(rec)
            print(f"[{p['group']:3s}/{p['lang']}/{variant:4s}] {p['item_id']:12s} várt={p['expected'][:24]!r:28s} "
                  f"think={rec['opens_think']} talált={rec['hit']}\n    {cut[:220]!r}", flush=True)

    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "00_smoke_template.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== ÖSSZESÍTÉS (faktuális itemek) ===")
    for variant in ("zero", "few2"):
        f = [r for r in out if r["variant"] == variant and r["kind"] == "fact"]
        print(f"  {variant:4s}: <think>-nyitás {sum(r['opens_think'] for r in f)}/{len(f)} · "
              f"várt válasz a kivágott szövegben {sum(r['hit'] for r in f)}/{len(f)}")


if __name__ == "__main__":
    main()
