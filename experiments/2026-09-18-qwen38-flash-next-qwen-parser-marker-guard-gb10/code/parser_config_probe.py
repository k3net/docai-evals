#!/usr/bin/env python3
"""Does the Qwen3 literal-marker guard reach a `qwen3_coder` deployment, and what does it fix?

CPU only: no GPU, no model, no weights. It builds the parser exactly the way the serving layer
builds it for `--tool-call-parser qwen3_coder`, reads the resulting engine config, then drives a
`StreamingParserEngine` with four texts at three chunk sizes. Run the same script inside images
with and without the patches to get a like-for-like comparison.

    python3 parser_config_probe.py            # prints JSON on stdout

Requires vLLM's own test helper for a mock tokenizer, so run it from a vLLM source tree
(`tests/parser/engine/conftest.py` must be importable as `tests.parser.engine.conftest`).

---

Magyar háttér. A blazux/qwen3.8-Flash-DGX patch 12 és 13 guardjai a forrásban
`name == "qwen3"`-ra vannak kötve. A DocAI pinelt receptje viszont
`--tool-call-parser qwen3_coder --reasoning-parser qwen3` kapcsolókkal indul, ezért nem
magától értetődő, hogy a javítás egyáltalán aktív-e nálunk. A szonda ezért NEM a tesztek
alapértelmezett `qwen3_config()`-ját használja, hanem abból a parserből olvassa ki a configot,
amit a `qwen3_coder` kapcsoló ténylegesen példányosít.

A négy eset szándékosan választja szét a két patch hatáskörét:

    A  kódblokkban bemutatott hívás     -> patch 13 territóriuma
    B  prózában idézett marker          -> patch 12 territóriuma
    C  valódi hívás                     -> regressziós kontroll, mindig hívásnak kell lennie
    D  unfenced marker a reasoningben   -> egyik patch sem fedi, szándékosan

A mérőszám nem csak az, hogy keletkezik-e eszközhívás, hanem az is, hogy a modell szövegéből
hány karakter jut el a kimenetre. A B eset ugyanis patch nélkül sem fantom hívást okoz, hanem
szövegvesztést — pusztán a hívás-jelenlét vizsgálata ezt elfedné.
"""
from __future__ import annotations

import json
import os
import sys

# A vLLM teszt-fa helye (conftest.make_mock_tokenizer miatt kell).
sys.path.insert(0, os.environ.get("VLLM_TEST_TREE", "/tt"))

from tests.parser.engine.conftest import make_mock_tokenizer  # noqa: E402
from vllm.parser.engine.events import EventType  # noqa: E402
from vllm.parser.engine.streaming_parser_engine import StreamingParserEngine  # noqa: E402
from vllm.tool_parsers.qwen3_engine_tool_parser import Qwen3EngineToolParser  # noqa: E402

VOCAB = {"<think>": 1, "</think>": 2, "<tool_call>": 3, "</tool_call>": 4}
CHUNKS = [1, 7, 10_000]  # token-szerű, tördelt, egyben

# A qwen3_coder kapcsoló ezt az osztályt példányosítja; a configot tőle vesszük.
ADAPTER = Qwen3EngineToolParser(make_mock_tokenizer(VOCAB), [])
CFG = ADAPTER._parser_engine.parser_engine_config


def parse(text: str, chunk: int):
    engine = StreamingParserEngine(CFG, None)
    events = []
    for i in range(0, len(text), chunk):
        events.extend(engine.feed(text[i:i + chunk], []))
    events.extend(engine.finish())
    return events


def joined(events, event_type) -> str:
    return "".join(e.value for e in events if e.type == event_type)


def tool_names(events) -> str:
    return "".join(e.value for e in events if e.type == EventType.TOOL_NAME)


def prose_len(text: str) -> int:
    """A modell által írt szöveg hossza a csatorna-jelölők nélkül."""
    return len(text.replace("<think>", "").replace("</think>", ""))


FENCED = (
    "Igy nez ki egy eszkozhivas:\n\n"
    "```xml\n"
    "<tool_call>\n"
    "<function=Bash>\n"
    "<parameter=command>ls -la</parameter>\n"
    "</function>\n"
    "</tool_call>\n"
    "```\n\n"
    "Ennyi a formatum."
)
QUOTED = (
    "A `<tool_call>` marker nyitja a hivast, "
    "de most nem hivok eszkozt. Ez a valasz vege."
)
REAL = (
    "<tool_call>\n<function=Bash>\n"
    "<parameter=command>ls</parameter>\n</function>\n</tool_call>"
)
UNFENCED_REASONING = (
    "<think>A felhasznalo a formatumra kerdez. Peldaul: "
    "<tool_call>\n<function=Bash>\n"
    "<parameter=command>ls</parameter>\n</function>\n</tool_call>\n"
    "Ezt kell elmagyaraznom.</think>"
    "A formatum a fenti XML."
)

# (azonosító, szöveg, várunk-e eszközhívást, várjuk-e a teljes szöveg megőrzését, megjegyzés)
CASES = [
    ("A/fenced-xml", FENCED, False, True,
     "kodblokkban bemutatott hivas -> szoveg marad (patch 13)"),
    ("B/quoted-inline", QUOTED, False, True,
     "prozaban idezett marker -> szoveg marad (patch 12)"),
    ("C/genuine-call", REAL, True, False,
     "valodi hivas tovabbra is parse-olodik (regressziós kontroll)"),
    ("D/unfenced-reasoning", UNFENCED_REASONING, True, False,
     "SZANDEKOSAN NEM FEDETT: reasoningben, fence nelkul"),
]


def main() -> None:
    res = {
        "config_name": CFG.name,
        "validate_tool_preamble": getattr(CFG, "validate_tool_preamble", None),
        "guard_literal_tool_markers": getattr(CFG, "guard_literal_tool_markers", None),
        "cases": {},
    }

    for name, text, expect_call, expect_text, note in CASES:
        per_chunk = {}
        for chunk in CHUNKS:
            events = parse(text, chunk)
            content = joined(events, EventType.TEXT_CHUNK)
            reasoning = joined(events, EventType.REASONING_CHUNK)
            calls = tool_names(events)
            kept = len(content) + len(reasoning)
            per_chunk[chunk] = {
                "tool_call": bool(calls),
                "tool_name": calls,
                "reasoning_len": len(reasoning),
                "content_len": len(content),
                "kept_chars": kept,
                "input_chars": prose_len(text),
                "kept_ratio": round(kept / max(prose_len(text), 1), 3),
            }
        got_call = {v["tool_call"] for v in per_chunk.values()}
        got_full = {v["kept_chars"] == v["input_chars"] for v in per_chunk.values()}
        ok = got_call == {expect_call} and (not expect_text or got_full == {True})
        res["cases"][name] = {
            "note": note,
            "expect_tool_call": expect_call,
            "expect_text_preserved": expect_text,
            "got_tool_call": sorted(got_call),
            "got_text_preserved": sorted(got_full),
            "verdict": "PASS" if ok else "FAIL",
            "chunks": per_chunk,
        }

    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
