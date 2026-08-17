"""Ugyanaz a demó-prompt egy OpenAI-kompatibilis vLLM endpointon (prod 35B).

A `demo_prompt.py` párja: a 9B-s ágakat lokálisan, `transformers`-szel futtatjuk,
a nagy prod modellt viszont csak API-n érjük el. Ami AZONOS a két script között —
és emiatt összevethető a kimenet:

  * `SYSTEM_PROMPT` és a user-prompt szó szerint,
  * a dekódolás: T=0,8 · top_p=0,9 · max 420 token,
  * `best_of` jelölt EGY hívásban (`n`), majd ugyanaz a `form_score()` reranker
    ugyanazzal a spec-kel (`n_stanzas=1`, `stanza_size=4`),
  * a döntetlen-feloldás: pontszám szerint csökkenő, egyenlőségnél a
    generálási sorrend dönt.

Ami ELTÉR, és amit ezért jelezni kell a cikkben: más modellcsalád és méret,
más kvantálás, és a szolgáltatás oldali sampler (a `seed` a szerverre megy).

    python3 code/demo_prompt_api.py --base-url http://HOST:PORT/v1 --model qwen36 \
        --prompt "..." --best-of 8 --seed 101 --label api_nothink
    python3 code/demo_prompt_api.py ... --thinking --max-tokens 1600 --label api_think
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# A mérőeszköz a repó közös scripts/ mappájában lakik — ld. annotate_corpus.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import hu_prosody as hp  # noqa: E402
from generate import SYSTEM_PROMPT, STYLE_DECODE, form_score  # noqa: E402

# A reasoning-blokk formája szolgáltatás-verziótól függ: külön mezőben jön
# (`reasoning` VAGY `reasoning_content` — a névre nem lehet építeni), vagy a
# content elején `<think>…</think>`-ként. ⚠️ Ha a reasoning külön mezős és a
# válasz `length`-be fut, a `content` ÜRESEN marad — a jelölt nem „rossz vers”,
# hanem el sem jutott a versig. Ezt a `finish_reason` mutatja meg.
REASONING_FIELDS = ("reasoning", "reasoning_content")
THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--base-url", required=True, help="pl. http://HOST:PORT/v1")
    ap.add_argument("--model", default="qwen36")
    ap.add_argument("--api-key", default="")
    ap.add_argument("--best-of", type=int, default=8)
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--thinking", action="store_true",
                    help="reasoning mód BE (a demó-ágak thinking nélkül futnak)")
    ap.add_argument("--max-tokens", type=int, default=STYLE_DECODE["max_new_tokens"],
                    help="thinking módban a reasoning is ide számol, ezért többet kell adni")
    ap.add_argument("--stanzas", type=int, default=1, help="a reranker spec-je")
    ap.add_argument("--stanza-size", type=int, default=4)
    ap.add_argument("--label", default="api")
    ap.add_argument("--out", default="data/generations")
    return ap.parse_args()


def strip_reasoning(choice: dict) -> tuple[str, str]:
    """Visszaadja a (vers, reasoning) párt — a reasoning csak naplóba kerül."""
    msg = choice.get("message", {}) or {}
    reasoning = " ".join(msg.get(f) or "" for f in REASONING_FIELDS).strip()
    content = msg.get("content") or ""
    inline = THINK_BLOCK.findall(content)
    if inline:
        reasoning = (reasoning + "\n" + "\n".join(inline)).strip()
        content = THINK_BLOCK.sub("", content)
    return content.strip(), reasoning


def call_api(args: argparse.Namespace) -> dict:
    payload = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": args.prompt},
        ],
        "n": args.best_of,
        "temperature": STYLE_DECODE["temperature"],
        "top_p": STYLE_DECODE["top_p"],
        "max_tokens": args.max_tokens,
        "seed": args.seed,
        "chat_template_kwargs": {"enable_thinking": bool(args.thinking)},
    }
    req = urllib.request.Request(
        args.base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {args.api_key or 'none'}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    args = parse_args()
    spec = {"n_stanzas": args.stanzas, "stanza_size": args.stanza_size}

    t0 = time.time()
    try:
        data = call_api(args)
    except urllib.error.HTTPError as exc:  # a szerver hibaüzenete informatív
        print(f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:800]}")
        return 1
    elapsed = time.time() - t0

    cands = []
    for choice in data.get("choices", []):
        text, reasoning = strip_reasoning(choice)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        cands.append({
            "text": text,
            "form_score": round(form_score(text, spec), 4),
            "n_lines": len(lines),
            "syllables": [hp.count_syllables(ln) for ln in lines],
            "rhyme_scheme": hp.rhyme_scheme(lines) if len(lines) >= 2 else "",
            "rhyme_pairs": [
                {
                    "a": lines[i].split()[-1] if lines[i].split() else "",
                    "b": lines[i + 1].split()[-1] if lines[i + 1].split() else "",
                    "score": round(hp.rhyme_score(lines[i], lines[i + 1]), 3),
                    "inflectional": hp.inflectional_suffix(lines[i], lines[i + 1]),
                }
                for i in range(len(lines) - 1)
            ],
            "finish_reason": choice.get("finish_reason"),
            "reasoning_chars": len(reasoning),
        })

    if not cands:
        print("A szerver nem adott jelöltet.")
        return 1

    order = sorted(range(len(cands)), key=lambda i: (-cands[i]["form_score"], i))
    winner = order[0]

    print(f"\n{'='*70}\nPROMPT: {args.prompt}")
    print(f"{args.model} · thinking={'BE' if args.thinking else 'KI'} · "
          f"best-of {args.best_of} · seed {args.seed} · {elapsed:.1f}s\n{'='*70}")
    for rank, i in enumerate(order, start=1):
        c = cands[i]
        mark = "★ GYŐZTES" if i == winner else f"  #{rank}"
        print(f"\n{mark}  form_score={c['form_score']:.3f}  sor={c['n_lines']}  "
              f"szótag={c['syllables']}  séma={c['rhyme_scheme']}  "
              f"rím>=0.6: {sum(p['score'] >= 0.6 for p in c['rhyme_pairs'])}"
              f"/{len(c['rhyme_pairs'])}")
        for ln in c["text"].splitlines():
            if ln.strip():
                print(f"      {ln}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"demo_{args.label}.json"
    out_path.write_text(json.dumps({
        "prompt": args.prompt,
        "system_prompt": SYSTEM_PROMPT,
        "model": args.model,
        "served_via": "openai-compatible endpoint",
        "adapter": None,
        "thinking": bool(args.thinking),
        "best_of": args.best_of,
        "seed": args.seed,
        "decode": {
            "temperature": STYLE_DECODE["temperature"],
            "top_p": STYLE_DECODE["top_p"],
            "max_tokens": args.max_tokens,
        },
        "spec": spec,
        "elapsed_seconds": round(elapsed, 1),
        "usage": data.get("usage"),
        "winner_index": winner,
        "candidates": cands,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
