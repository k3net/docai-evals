#!/usr/bin/env python3
"""Round6 smoke: helyességi kapu + determinizmus egy szerverindításon belül."""
import argparse, json, urllib.request

PROMPTOK = [
    "Mennyi 17 * 23? Csak a számot írd.",
    "Sorold fel Magyarország három legnagyobb városát.",
    "Fordítsd angolra: A szerződés 2026. január 1-jén lép hatályba.",
    "Írj egy egymondatos összefoglalót a gépi tanulásról.",
]


def hivas(url, model, prompt, max_tokens, thinking):
    body = {
        "model": model, "temperature": 0, "top_p": 1, "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
        "chat_template_kwargs": {"enable_thinking": thinking},
    }
    req = urllib.request.Request(url + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.load(r)
    ch = d["choices"][0]
    return {
        "content": ch["message"].get("content") or "",
        "reasoning": ch["message"].get("reasoning_content") or "",
        "finish": ch.get("finish_reason"),
    }


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", required=True)
    a.add_argument("--model", default="qwen38-flash-next-nvfp4")
    a.add_argument("--ismetles", type=int, default=3)
    a.add_argument("--max-tokens", type=int, default=64)
    a.add_argument("--thinking", action="store_true")
    a.add_argument("--out", required=True)
    args = a.parse_args()

    ki, stabil, ures = [], 0, 0
    for p in PROMPTOK:
        futasok = [hivas(args.url, args.model, p, args.max_tokens, args.thinking)
                   for _ in range(args.ismetles)]
        szovegek = [f["content"] for f in futasok]
        s = len(set(szovegek)) == 1
        stabil += s
        ures += sum(1 for x in szovegek if not x.strip())
        ki.append({"prompt": p, "stabil": s, "futasok": futasok})
        print("%-9s %-52s hossz=%s finish=%s" % (
            "STABIL" if s else "INSTABIL", p[:52],
            [len(x) for x in szovegek], sorted({f["finish"] for f in futasok})))
        if not s:
            for i, x in enumerate(szovegek):
                print("     #%d %r" % (i + 1, x[:90]))
    json.dump(ki, open(args.out, "w"), indent=2, ensure_ascii=False)
    print("\n=> %d/%d stabil · üres válasz: %d · thinking=%s · mentve: %s"
          % (stabil, len(PROMPTOK), ures, args.thinking, args.out))


if __name__ == "__main__":
    main()
