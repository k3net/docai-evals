#!/usr/bin/env python3
"""Live serving-layer regression for quoted/literal Qwen tool markers.

Six prompts that make the model write a `<tool_call>` marker it does not mean as a call,
each run with and without `tools` in the request, streaming and non-streaming.

What is measured is the *serving layer's* answer, not the model's quality: does the content
survive, is a tool call invented, what does `finish_reason` say.

For every prompt the raw generation is also captured through
`/v1/chat/completions/render` -> `/v1/completions`, which bypasses the tool and reasoning
parsers entirely. That separates a parser failure (raw text complete, API answer truncated)
from a model failure (raw text already truncated), and it preserves the token sequence so the
parse can be replayed offline against any build.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

TOOLS = [{
    "type": "function",
    "function": {
        "name": "Bash",
        "description": "Run a shell command.",
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string", "description": "the command"}},
            "required": ["command"],
        },
    },
}]

# (id, prompt, does a genuine tool call belong here?)
#
# The prompts are Hungarian, unaccented, exactly as measured — this is a Hungarian
# document-AI stack and the marker behaviour was first seen on Hungarian traffic. English
# glosses follow each one; they are not what was sent.
CASES = [
    # "Explain the literal string <tool_call>, without calling a tool."
    ("1-prose-marker",
     "Magyarazd el a `<tool_call>` literal sztringet, eszkozhivas nelkul.",
     False),
    # "Show in an ```xml code block what a Bash tool call looks like in the Qwen format,
    #  then summarise in one sentence after the block."
    ("2-fenced-xml",
     "Mutasd meg egy ```xml kodblokkban, hogyan nez ki egy Bash eszkozhivas "
     "a Qwen formatumban, majd a kodblokk utan foglald ossze egy mondatban.",
     False),
    # "Write out exactly an empty <tool_call></tool_call> wrapper and explain what it means."
    ("3-empty-wrapper",
     "Irj le pontosan egy ures `<tool_call></tool_call>` wrappert, "
     "es magyarazd el, mit jelent.",
     False),
    # "List the contents of the /tmp directory."
    ("4-genuine-call",
     "Listazd ki a /tmp konyvtar tartalmat.",
     True),
    # "Write one sentence, then the <tool_call> marker, then one more sentence."
    ("5-marker-between-prose",
     "Irj egy mondatot, aztan a `<tool_call>` markert, aztan meg egy mondatot.",
     False),
    # "Document the Qwen tool-call XML format in detail, with several examples in code
    #  blocks. Do not call a tool."
    ("6-documenting-prose",
     "Reszletesen dokumentald a Qwen tool-call XML formatumot, "
     "tobb peldaval, kodblokkokban. Ne hivj eszkozt.",
     False),
]


def post(url: str, path: str, body: dict, timeout: int = 900):
    req = urllib.request.Request(
        url.rstrip("/") + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def chat_body(model: str, prompt: str, tools: bool, max_tokens: int) -> dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "top_p": 1,
        "max_tokens": max_tokens,
    }
    if tools:
        body["tools"] = TOOLS
        body["tool_choice"] = "auto"
    return body


def chat(url, model, prompt, tools, stream, max_tokens):
    body = chat_body(model, prompt, tools, max_tokens)
    body["stream"] = stream
    if not stream:
        d = post(url, "/v1/chat/completions", body)
        ch = d["choices"][0]
        m = ch["message"]
        return {
            "content": m.get("content") or "",
            # NOTE: the field is `reasoning`, not `reasoning_content`.
            "reasoning": m.get("reasoning") or "",
            "tool_calls": [t["function"]["name"] for t in (m.get("tool_calls") or [])],
            "finish_reason": ch.get("finish_reason"),
        }

    req = urllib.request.Request(
        url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    content = reasoning = ""
    names: list[str] = []
    finish = None
    with urllib.request.urlopen(req, timeout=900) as resp:
        for raw in resp:
            line = raw.decode().strip()
            if not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload == "[DONE]":
                break
            ch = json.loads(payload)["choices"][0]
            delta = ch.get("delta") or {}
            content += delta.get("content") or ""
            reasoning += delta.get("reasoning") or ""
            for t in (delta.get("tool_calls") or []):
                name = (t.get("function") or {}).get("name")
                if name:
                    names.append(name)
            finish = ch.get("finish_reason") or finish
    return {"content": content, "reasoning": reasoning,
            "tool_calls": names, "finish_reason": finish}


def raw_generation(url, model, prompt, tools, max_tokens):
    """The model's own output with no tool or reasoning parser in the path."""
    rendered = post(url, "/v1/chat/completions/render",
                    chat_body(model, prompt, tools, max_tokens))
    d = post(url, "/v1/completions", {
        "model": model,
        "prompt": rendered["token_ids"],
        "temperature": 0,
        "top_p": 1,
        "max_tokens": max_tokens,
        "skip_special_tokens": False,
        "logprobs": 0,
    })
    ch = d["choices"][0]
    lp = ch.get("logprobs") or {}
    return {
        "prompt_tokens": len(rendered["token_ids"]),
        "text": ch["text"],
        "finish_reason": ch["finish_reason"],
        "stop_reason": ch.get("stop_reason"),
        "completion_tokens": d["usage"]["completion_tokens"],
        "last_tokens": (lp.get("tokens") or [])[-8:],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", default="qwen38-flash-next-nvfp4")
    ap.add_argument("--max-tokens", type=int, default=700)
    ap.add_argument("--out", required=True, help="results JSON")
    ap.add_argument("--raw-dir", help="directory for the raw generations (one .txt per case/arm)")
    args = ap.parse_args()

    raw_dir = Path(args.raw_dir) if args.raw_dir else None
    if raw_dir:
        raw_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for name, prompt, expect_call in CASES:
        for tools in (True, False):
            raw = raw_generation(args.url, args.model, prompt, tools, args.max_tokens)
            if raw_dir:
                (raw_dir / f"{name}-tools{int(tools)}.txt").write_text(raw["text"])
            for stream in (False, True):
                r = chat(args.url, args.model, prompt, tools, stream, args.max_tokens)
                rows.append({
                    "case": name, "tools": tools, "stream": stream,
                    "expect_tool_call": expect_call,
                    "content_len": len(r["content"]),
                    "reasoning_len": len(r["reasoning"]),
                    "tool_calls": r["tool_calls"],
                    "finish_reason": r["finish_reason"],
                    "empty_content": len(r["content"]) == 0,
                    "raw_len": len(raw["text"]),
                    "raw_completion_tokens": raw["completion_tokens"],
                    "raw_finish_reason": raw["finish_reason"],
                    "raw_last_tokens": raw["last_tokens"],
                    "content": r["content"],
                    "reasoning": r["reasoning"],
                })
                flag = ""
                if r["tool_calls"] and not expect_call:
                    flag = f"  <== PHANTOM CALL {r['tool_calls']}"
                elif not r["content"] and not r["tool_calls"]:
                    # raw shorter than the parsed answer would be impossible; compare the two
                    flag = ("  <== EMPTY ANSWER (model-side: raw is truncated too)"
                            if raw["text"].count("</think>") == 0
                            else "  <== EMPTY ANSWER (parser-side: raw contains </think>)")
                print("%-22s tools=%-5s stream=%-5s content=%-5d reasoning=%-5d raw=%-5d "
                      "finish=%-10s calls=%s%s"
                      % (name, tools, stream, len(r["content"]), len(r["reasoning"]),
                         len(raw["text"]), r["finish_reason"], r["tool_calls"], flag),
                      flush=True)

    Path(args.out).write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    phantom = sum(1 for r in rows if r["tool_calls"] and not r["expect_tool_call"])
    empty = sum(1 for r in rows if r["empty_content"] and not r["tool_calls"])
    print(f"\n{len(rows)} requests · phantom tool calls: {phantom} · empty answers: {empty}")
    print(f"written: {args.out}" + (f" · raw: {raw_dir}" if raw_dir else ""))


if __name__ == "__main__":
    main()
