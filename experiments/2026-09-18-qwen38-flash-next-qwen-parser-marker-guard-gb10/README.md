# Qwen3.8-Flash-Next on vLLM: the answer that disappears has two causes, and only one of them is the parser

A Qwen3 deployment that serves tools will sometimes return an empty assistant message, or a tool
call the model never meant to make. Two downstream parser patches were added to the blazux recipe
in September 2026. One is proposed upstream as
[vLLM #56661](https://github.com/vllm-project/vllm/pull/56661) (still a draft); the fence guard
currently remains downstream-only. This round measures what they actually fix on a production
recipe, separates their effects from each other, and shows that a second, unrelated failure hides
behind the same symptom — one that no parser change can reach, because the model ends the turn
itself.

## 1. What was the measurement for?

Four questions:

1. Does the literal-marker guard reach **our** deployment at all? The patches are gated on
   `name == "qwen3"`, while we serve with `--tool-call-parser qwen3_coder`.
2. What does each patch fix **on its own**? The two are usually applied together, so their
   effects have not been separated.
3. Does adopting them perturb anything else in a serving stack that depends on a deterministic
   top-k kernel and on prefix caching across requests?
4. When the answer still disappears after both patches, where does it go?

## 2. On what task and dataset?

No ground truth and no scored answers. Two instruments:

- **parser probe (CPU)** — four hand-written texts fed straight into vLLM's streaming parser at
  three chunk sizes. No GPU, no model, no weights. Every comparison is one parser build against
  another on identical input.
- **live serving probe (GPU)** — six prompts that induce the model to write a `<tool_call>`
  marker it does not mean as a call, each with and without `tools`, streaming and non-streaming.
  For every prompt the **raw generation** is also captured through
  `/v1/chat/completions/render` → `/v1/completions`, which takes the tool and reasoning parsers
  out of the path entirely.

The regression gate reuses the round-4 threshold matrix over the same synthetic Hungarian
corpus (`D6.md`, 3052 tokens with the chat template), unchanged.

## 3. Which models and configurations were compared?

| arm | build | parser patches |
|---|---|---|
| no patch | `qwen38-flash-dgx:v029-validation-20260912T120351Z` (recipe on `vllm/vllm-openai:v0.29.0`) | none |
| patch 12 | the same image, `qwen-tool-preamble.patch` applied to site-packages at container start | 12 |
| patch 12+13 | `Dockerfile.v0.29` rebuilt at blazux `5be6637` | 12 + 13 |

Same checkpoint (`RadixArk/Qwen3.8-Flash-Next-NVFP4`, snapshot `7b71922`), same launch flags,
same box. **Patch 12** is the backport of
[vllm#56661](https://github.com/vllm-project/vllm/pull/56661) (draft; fixes
[vllm#56658](https://github.com/vllm-project/vllm/issues/56658)). **Patch 13** is the fence guard
from [blazux/qwen3.8-Flash-DGX#29](https://github.com/blazux/qwen3.8-Flash-DGX/pull/29), which has
no upstream PR at the time of writing.

### The image A/B is one variable, and that was verified rather than assumed

Between the pinned image and the rebuild, **8 of 28,459 `.py` files differ**, and the
deterministic top-k `.so` is byte-identical in both
(`a49272e17de15e785af8a63b8f122d363e6b1efb9fc28ff91ce4bfb8091fee7d`). Of the eight:

| file(s) | change | active here? |
|---|---|---|
| `vllm/parser/{qwen3,engine/*}.py` (3) | patches 12 + 13 | **yes — the intended change** |
| `vllm/parser/nemotron_v3.py` | patch 12's explicit opt-out | no (not our parser) |
| `qwen4_exp/nvidia/mtp.py`, `quantization/modelopt.py` | vllm#55513 backport | no — ModelOpt MIXED_PRECISION only; RadixArk is `quant_algo NVFP4` |
| `vllm_ple_mmap.py` | Prometheus phase counters | inert — `PROMETHEUS_MULTIPROC_DIR` unset (the server says so in the log); `fast_rows` still defaults to 512 in the module |
| `vllm_fp8_hybrid_modelopt.py` | MIXED_PRECISION coverage | inert — `VLLM_FP8_HYBRID` unset |

The recipe's `FAST_ROWS=0` default and its rewritten chat template both live in `serve.sh`; we
launch with an explicit `docker run`, so neither applies.

### Launch, identical on every arm

```text
vllm serve <RadixArk snapshot 7b71922>
  --served-model-name qwen38-flash-next-nvfp4 --load-format safetensors
  --max-model-len 262144 --max-num-seqs 4 --gpu-memory-utilization 0.78
  --enable-prefix-caching --enable-chunked-prefill --max-num-batched-tokens 8192
  -cc.cudagraph_mode=PIECEWISE -cc.splitting_ops=<the recipe's list>
  --no-enable-flashinfer-autotune --kv-cache-dtype auto
  --enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser qwen3
  --enable-prompt-tokens-details
  --speculative-config '{"method":"mtp","num_speculative_tokens":2}'

env: VLLM_QSA_DET_TOPK=1 VLLM_QSA_DET_LIB=/opt/llm/kernel-det/_C_det.so
     VLLM_QSA_EXACT_TOPK=0 VLLM_PLE_MMAP=1 VLLM_PLE_MMAP_PREWARM=0
     VLLM_PLE_MMAP_WORKERS=32 VLLM_USE_FLASHINFER_SAMPLER=1
```

Only the image changes between arms. The server confirms the pieces that matter in its log:
`QSADET active: /opt/llm/kernel-det/_C_det.so`, attention block size 1600, PLE mmap on, and
`PROMETHEUS_MULTIPROC_DIR is unset`.

## 4. Which metrics?

- **`guard_active`**: `validate_tool_preamble` and `guard_literal_tool_markers` on the engine
  config that `qwen3_coder` actually builds.
- **`tool_call_opened`** (primary): does the parser emit a `TOOL_NAME` event for text where no
  call was meant.
- **`kept_chars` / `input_chars`**: characters of the model's prose that reach the output, over
  the characters fed in. *This is the metric that separates the two patches* — the marker-in-prose
  case never produced a phantom call for us, it lost text, and a call-presence check alone would
  have scored it as passing.
- **`raw_vs_parsed`**: does the raw generation already end where the API answer ends.
- **`full_logprob_hash_variants`** and **`cached_prompt_tokens`**: the round-4 regression gate,
  definitions unchanged.

## 5. What was the result?

### 5.1 The guard does reach a `qwen3_coder` deployment

`qwen3_coder` resolves to `Qwen3EngineToolParser` → `Qwen3ParserToolAdapter` → `Qwen3Parser`,
whose `CONFIG_NAME` is `"qwen3"`. The probe reads `config.name == "qwen3"` on all three arms, and
`validate_tool_preamble` / `guard_literal_tool_markers` go `None` → `True`. Genuinely derived
configurations (`nemotron_v3`) do keep the old behaviour, which is what the gate is for.

This is worth stating because the gate reads as if `qwen3_coder` and `qwen3_xml` were excluded,
and the recipe's own recommended launch line uses `qwen3_coder`.

### 5.2 The two patches fix different cases, and neither fixes the third

Identical at all three chunk sizes (1 / 7 / 10000 characters):

| case | no patch | patch 12 | patch 12+13 |
|---|---|---|---|
| `<tool_call>` + `<function=` inside a ` ```xml ` block | phantom `Bash` call, **59/149 (40%)** | phantom `Bash` call, **59/149 (40%)** | no call, **149/149 (100%)** |
| inline quoted `<tool_call>` then prose | no call, **3/84 (4%)** | no call, **84/84 (100%)** | no call, **84/84 (100%)** |
| genuine tool call | parses | parses | parses |
| unfenced `<tool_call>` in reasoning | phantom call, 91/177 (51%) | 91/177 (51%) | 91/177 (51%) |

Patch 12 fixes its own case cleanly and **does not touch the fenced-code-block case at all**. The
fenced case is the one that yields a phantom tool call with `tools` present and `content: null`
without them — the symptom users describe as "the output dies on a backtick". Neither patch
changes the unfenced-reasoning case, which both authors document as a deliberate omission.

### 5.3 Adoption perturbs nothing else

Cross-request prefix-cache threshold matrix, four cells, four repetitions, one server start:

| cell | A | B | prediction | measured | B `cached_tokens` |
|---|---:|---:|---|---|---|
| A below, B above | 3199 | 3259 | FAIL | **FAIL** | `[0, 1600, 1600, 1600]` |
| A above, B above | 3219 | 3259 | PASS | **PASS** | `[0, 1600, 1600, 1600]` |
| both below | 3099 | 3169 | PASS | **PASS** | `[0, 0, 0, 0]` |
| A above, B below | 3219 | 3169 | PASS | **PASS** | `[0, 0, 0, 0]` |

4/4, and exactly the round-4 **control** pattern — correctly, since this image does not carry the
boundary stop. The known divergence is still there and nothing new joined it. Smoke: 4/4 prompts
stable over three repetitions, no empty answers. No `Xid`, no `NV_ERR_NO_MEMORY`, no worker
restart; `MemAvailable` floor 19,114 MiB over 935 samples.

### 5.4 On live traffic the phantom call is gone, but nine answers in twenty-four are empty

Six prompts × tools on/off × streaming/non-streaming, on the patched image:

| | count |
|---|---:|
| requests | 24 |
| **phantom tool calls** | **0** |
| genuine tool call returned where one belonged | 2/2 |
| empty assistant message with no tool call | **9** |
| of those, where the raw generation is equally truncated | **8** |

The phantom call is gone, which is what the fence guard is for.

The empty answers are a different matter. **8 of 9 empty responses were already truncated in raw
generation**: for those, the parser emitted exactly as many characters as the raw capture for the
same prompt contains (`reasoning_len == raw_len`), with no `</think>` anywhere in that raw text.
The ninth is `2-fenced-xml` without tools, where the parsed and raw lengths do not line up; it is
**not cleanly attributed** and we do not count it either way.

Two things this does not establish. The raw capture is a **separate request**, not the token stream
of the chat request it is compared against — greedy output here is not stable across calls (5.6
shows the same prompt generating different text on two calls), so this anchors what the model tends
to produce for a prompt rather than proving what that particular chat request emitted. And nine
observations over six prompts establish no rate.

### 5.5 The answer that still disappears ends before either parser can act

`Magyarazd el a <tool_call> literal sztringet, eszkozhivas nelkul.` ("Explain the literal string
`<tool_call>`, without calling a tool") with a `Bash` tool in the request returns `content: ""`,
`finish_reason: "stop"`, no tool call. That looks exactly like a parser eating the answer.

It is not. The same prompt through `/v1/completions` — no tool parser, no reasoning parser — gives
a raw generation of **1254 characters, 292 tokens, `finish_reason: stop`**, ending at the same
point. The last eight tokens:

```
' calling'  ' format'  ').'  ' The'  ' counterpart'  ' is'  ' `'  '<|im_end|>'
```

The model emits EOS (`<|im_end|>`, id 248046) itself, mid-sentence, still inside `<think>`, with no
`</think>` and no answer — cut off exactly where it was about to write the closing marker, having
already written `<tool_call>` five times in that turn.

We saw the same shape on an earlier server start with different wording (819 characters, 196
tokens, ending `' \`' '<tool_call>' '\`' ' and' ' \`' '<|im_end|>'`). The generation is not stable
across starts — consistent with round 3's finding — but the failure is.

This failure is outside the scope of both parser patches: the raw `/v1/completions` path bypasses
the tool and reasoning parsers, and the generation has already ended before either parser could
act. A fence-based guard cannot help here even in principle — there is no text to keep as text and
no call to suppress. We did not run this exact live raw-generation probe on the pre-patch image, so
we make no claim that the raw token sequence is identical there.

One further data point: the same prompt with **no** `tools` in the request returns a full
878-character answer, stable over three repetitions. The presence of tool definitions is what walks
the model into the marker in its own reasoning.

### 5.6 The streaming/non-streaming divergence is the model's, not the parser's — a negative result

The live probe looked like it had caught a parser bug: for `2-fenced-xml` without tools, the
non-streaming call returned 0 characters of content and the streaming call 1055, and for
`3-empty-wrapper` with tools, 2398 against 2352. vLLM has open issues in exactly this area
([#47903](https://github.com/vllm-project/vllm/issues/47903)), so it was tempting to report.

It does not survive a control. Those are two separate generations, and greedy output on this stack
is not bit-stable. Replaying **the identical captured raw text** through both code paths — the
adapters' `extract_reasoning` / `extract_tool_calls` for non-streaming, `StreamingParserEngine` in
chunks for streaming — gives, over all twelve raw generations and three chunk sizes:

> 12 files · streaming/non-streaming divergences: **0**

Every file agrees across modes and across chunk sizes. The live difference was the model producing
different text on the two calls. We report nothing to #47903.

What the replay does show is how much of the model's own text survives on the patched build:

| raw generation | kept | lost | why |
|---|---:|---:|---|
| `1-prose-marker` (no tools) | 1557 / 1565 | 8 | the `</think>` marker |
| `4-genuine-call` (no tools) | 457 / 465 | 8 | the `</think>` marker |
| `5-marker-between-prose` | 353 / 361 | 8 | the `</think>` marker |
| `4-genuine-call` (tools) | 108 / 213 | 105 | the tool-call markup, consumed as a real call — correct |
| `3-empty-wrapper` (tools) | 2581 / 2635 | 54 | marker terminals not re-emitted as text |
| `3-empty-wrapper` (no tools) | 1099 / 1199 | 100 | as above |
| `2-fenced-xml` (no tools) | 2022 / 2471 | 449 | the model writes the markup **unfenced** in reasoning — case D, documented as uncovered |

The 449-character loss is the uncovered case reproduced on real model output rather than on a
hand-written probe input, which is worth having. The smaller losses are the marker terminals
themselves: a user who asks the model to print `<tool_call>` verbatim does not always get it back.
That is an observation, not a diagnosis; we did not trace it.

## 6. What product decision followed?

The rebuilt image is adopted; see `decision-record.md`. The model-side termination is not fixed
by anything available and is carried as a known exposure.

## 7. What are the limits of the measurement?

- Patch 12 was measured as **blazux's backport onto v0.29.0**, not as vllm#56661's head on `main`.
  The upstream PR may have moved.
- The parser probe exercises the parser only. It says nothing about how often real traffic
  produces these texts.
- The frequency of the model-side termination was **not** measured on production traffic. It is
  reproduced, not quantified; the exposure is unknown in magnitude.
- The live probe covers six prompts in one language. Nothing here establishes a rate.
- One box, one GPU, one checkpoint. No second stack reproduced this round.
- The live arm was run on the patched image only. The no-patch and patch-12 arms are CPU-parser
  measurements; there is no live A/B of the serving layer across all three builds.
- The Hungarian KIE quality suite, the soak and the throughput sweep were not re-run. This is a
  maintenance validation, not a full acceptance pass.
- An earlier run of the live probe read the wrong response field (`reasoning_content` instead of
  `reasoning`) and its numbers are not published; the probe here reads the correct one.
- The raw generation is a third request, not the same call as the two chat requests it is compared
  with. It anchors *what the model tends to produce* for a prompt; the strict parser control is the
  replay in 5.6, which holds the text fixed.
- The replay covers twelve raw generations. A divergence rarer than that would not show up.

## 8. Which DocAI article belongs to it?

None yet. Predecessor:
[2026-09-14-qwen38-flash-next-prefix-cache-root-cause-gb10](../2026-09-14-qwen38-flash-next-prefix-cache-root-cause-gb10/),
whose threshold matrix is reused unchanged as the regression gate here.

## Layout

```text
code/parser_config_probe.py       # CPU: builds the parser the way qwen3_coder does, four cases x three chunk sizes
code/agentic_toolcall_probe.py    # GPU: six prompts x tools on/off x streaming, plus the raw generation per prompt
code/smoke.py                     # GPU: correctness gate and within-start determinism
code/replay_raw_through_parser.py # CPU: the same raw text through both parse paths - the 5.6 control
results/parser-probe-no-patch.json
results/parser-probe-patch12.json
results/parser-probe-patch12-13.json
results/agentic-toolcall.json     # live serving layer, patched image
results/raw-generations/          # model output with no parser in the path, one file per prompt/arm
results/replay-raw-through-parser.json        # streaming vs non-streaming on identical text
results/round6-cross-request-cells1234.json   # the round-4 gate, re-run on the patched image
results/smoke.json
docs/                             # Hungarian lab note
```

The cross-request probe (`checkpoint_probe.py`) is unchanged from the
[round-4 package](../2026-09-14-qwen38-flash-next-prefix-cache-root-cause-gb10/code/checkpoint_probe.py)
and is not duplicated here. Container logs and `docker inspect` dumps are kept internally; the
launch arguments are reproduced in this README.
