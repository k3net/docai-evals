#!/usr/bin/env python3
"""Replay a captured raw generation through the Qwen3 parser, streaming and non-streaming.

The live probe showed the same prompt producing different answer lengths in streaming and
non-streaming mode. That is not evidence of a parser bug on its own: the two API calls are two
separate generations, and greedy output on this stack is not bit-stable across cache states.

This script removes that confound. It takes a raw generation captured with the parsers bypassed
(`agentic_toolcall_probe.py --raw-dir`) and feeds **the identical text** through both paths:

  * non-streaming - the adapters' `extract_reasoning` / `extract_tool_calls` on the whole string;
  * streaming     - `StreamingParserEngine.feed()` in chunks, then `finish()`.

Any difference is then the parser's, not the model's.

    python3 replay_raw_through_parser.py results/raw-generations/*.txt

CPU only: no GPU, no model, no weights. Run it inside the image whose parser you want to measure.

---

Magyar háttér. A vLLM-ben streaming és non-streaming tool-parse két külön kódút, és ismert, hogy
csonkolt kimeneten eltérhetnek (vllm#47903, vllm#47137). A saját élő szondánk mutatott ilyen
gyanút, de kontroll nélkül nem volt jelenthető, mert a két hívás két külön generálás volt.
Ez a szkript a nyers szöveget rögzíti, és csak a parse-t variálja.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, os.environ.get("VLLM_TEST_TREE", "/tt"))

from tests.parser.engine.conftest import make_mock_tokenizer  # noqa: E402
from vllm.parser.engine.events import EventType  # noqa: E402
from vllm.parser.engine.streaming_parser_engine import StreamingParserEngine  # noqa: E402
from vllm.tool_parsers.qwen3_engine_tool_parser import Qwen3EngineToolParser  # noqa: E402

VOCAB = {"<think>": 1, "</think>": 2, "<tool_call>": 3, "</tool_call>": 4}
CHUNKS = [1, 7, 10_000]


def make_request():
    req = MagicMock()
    req.tools = []
    req.tool_choice = "auto"
    req.include_reasoning = True
    return req


def non_streaming(text: str) -> dict:
    """Amit a nem-streamelő kiszolgálóút ad ugyanerre a szövegre."""
    adapter = Qwen3EngineToolParser(make_mock_tokenizer(VOCAB), [])
    request = make_request()
    reasoning, content = adapter._parser_engine.extract_reasoning(text, request)
    info = adapter.extract_tool_calls(text, request)
    calls = [c.function.name for c in (getattr(info, "tool_calls", None) or [])]
    rest = getattr(info, "content", None)
    return {
        "reasoning_len": len(reasoning or ""),
        "content_len": len(content or ""),
        "tool_calls": calls,
        "tool_parser_content_len": len(rest or ""),
    }


def streaming(text: str, chunk: int) -> dict:
    cfg = Qwen3EngineToolParser(make_mock_tokenizer(VOCAB), [])._parser_engine.parser_engine_config
    engine = StreamingParserEngine(cfg, None)
    events = []
    for i in range(0, len(text), chunk):
        events.extend(engine.feed(text[i:i + chunk], []))
    events.extend(engine.finish())
    join = lambda t: "".join(e.value for e in events if e.type == t)  # noqa: E731
    return {
        "reasoning_len": len(join(EventType.REASONING_CHUNK)),
        "content_len": len(join(EventType.TEXT_CHUNK)),
        "tool_calls": [e.value for e in events if e.type == EventType.TOOL_NAME],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()

    out = []
    for path in args.files:
        text = Path(path).read_text()
        ns = non_streaming(text)
        st = {c: streaming(text, c) for c in CHUNKS}
        # A streaming karakterösszege minden darabolásnál ugyanaz kell legyen,
        # és egyeznie kell a non-streaming összegével.
        ns_total = ns["reasoning_len"] + ns["content_len"]
        st_totals = {c: v["reasoning_len"] + v["content_len"] for c, v in st.items()}
        row = {
            "file": os.path.basename(path),
            "raw_len": len(text),
            "closes_think": text.count("</think>") > 0,
            "non_streaming": ns,
            "streaming": st,
            "non_streaming_kept": ns_total,
            "streaming_kept": st_totals,
            "chunk_sizes_agree": len(set(st_totals.values())) == 1,
            "modes_agree": len({ns_total, *st_totals.values()}) == 1,
        }
        out.append(row)
        print("%-34s raw=%-5d ns=%-5d st=%-18s chunks_agree=%-5s modes_agree=%s%s"
              % (row["file"], row["raw_len"], ns_total,
                 str(list(st_totals.values())), row["chunk_sizes_agree"],
                 row["modes_agree"],
                 "" if row["modes_agree"] else "   <== PARSER DIVERGENCE"))

    diverging = [r["file"] for r in out if not r["modes_agree"]]
    print("\n%d files · streaming/non-streaming divergences: %d %s"
          % (len(out), len(diverging), diverging or ""))
    print(json.dumps(out, indent=2, ensure_ascii=False), file=sys.stderr)


if __name__ == "__main__":
    main()
