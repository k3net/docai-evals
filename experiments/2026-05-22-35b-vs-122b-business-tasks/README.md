# When is a bigger model worth it? — 35B vs 122B on real business tasks

**Date:** 2026-05-22 · **Type:** extraction and multi-step reasoning quality ·
**Reproducibility:** R3 ·
**Article (HU):** [Mikor érdemes nagyobb AI-modellt használni — és mikor nem?](https://docai.hu/blog/122b-vs-35b-mikor-jobb-a-nagyobb-modell)

> The companion measurement — *what it costs to run the larger model* — is
> [qwen35-122b-nvfp4-bringup-gb10](../2026-05-22-qwen35-122b-nvfp4-bringup-gb10/).

## 1. What was the measurement for?

The larger model was running and roughly 2.5× slower. The instinctive question — "is it better?" —
turned out to be useless, because the answer was *better at one thing, worse at another, slower at
everything*. The measurement was designed to answer a more useful one: **better at what, and can we
afford it there?**

## 2. On what task and dataset?

Three instruments, deliberately different in kind, because "quality" fails differently on each:

| Instrument | Size | What it probes |
|---|---|---|
| [hu-invoice-kie](../../evals/hu-invoice-kie/) | 34 scored units | Careful reading — field extraction from Hungarian invoices |
| Single-call tool evaluation | 10 scenarios | Basic tool selection |
| [chat-business-scenarios](../../evals/chat-business-scenarios/), reasoning subset | 6 scenarios | Multi-step financial reasoning over a document corpus |

The reasoning scenarios are the real business tasks: cash-flow gap projection, supplier billing
anomaly detection, customer concentration risk, quarterly VAT position, multi-year financial
comparison, top-supplier external risk.

## 3. Which models?

| Arm | Model | Role |
|---|---|---|
| baseline | Qwen3.6-35B-A3B-FP8 | production model, ~3B active parameters |
| candidate | Qwen3.5-122B-A10B-NVFP4 | ~10B active parameters, ~4× the total size |

Same tool catalogue, same corpus, same prompts.

## 4. Which metrics?

Field-level extraction F1; scenario pass rate; **tool calls per passing scenario** — efficiency,
not just correctness; end-to-end latency; and a human reviewer's qualitative verdict on answer
quality.

Tool-call counts are the objective backbone here. The quality verdict is not, and we say so in §7.

## 5. What was the result?

### On the core task, the bigger model lost

| | 35B | 122B |
|---|---|---|
| Extraction F1 (34 units) | **0.975** | 0.938 |
| Latency per unit | 9.2 s | 17.9 s |

Two times slower and measurably *worse* at reading an invoice. Key information extraction rewards
careful reading of a short document against a fixed schema — model size does not help, and the
larger model's extra errors were the ordinary kind: an identifier normalised into a different
format, a field invented where the document says nothing, a line item padded with its billing
period.

**There is no extraction argument for the larger model.** That finding alone paid for the
measurement, because the intuition in the room had been the opposite.

### On single-call tool use, indistinguishable

| | 35B | 122B |
|---|---|---|
| Pass | 9/10 | 9/10 |
| Failing scenario | the same one | the same one |
| Total latency | 41 s | 246 s (6.0×) |

Identical results, six times the wall-clock. If this had been the whole evaluation, the correct
conclusion would have been "no reason to use the bigger model" — and it would have been wrong.

### On multi-step reasoning, the difference is real and it is about efficiency

Six compound business scenarios:

| | 35B | 122B |
|---|---|---|
| Total tool calls | 108 | **21** |
| Tool calls per passing scenario | 8.0 | **4.7** |
| Total latency | 360 s | 951 s (2.6×) |
| Reviewer verdict | — | better or equal on 5 of 6 |

**The larger model reaches the same or better answers with roughly five times fewer tool calls.**
On the multi-year financial comparison it used 5 tools where the smaller one used 7, and produced
a more complete answer. On supplier-anomaly detection, 6 versus 17. The smaller model's failure
mode is not wrong answers — it is *flailing*: more queries, worse synthesis, and on one scenario
67 tool calls without ever converging.

The concrete quality difference the reviewer flagged: on a monthly spending-trend question, the
smaller model computed the wrong growth rate. **Multi-step arithmetic over retrieved data is where
size paid.**

### Why efficiency matters more than the pass rate

The pass counts alone would have shown a tie. The tool-call ratio shows what is actually
different: one model plans a retrieval strategy, the other gropes toward one. That distinction is
invisible on single-call tests and decisive on compound ones — and it is also what makes the
larger model's output *reviewable*, because a human can follow five deliberate queries and cannot
follow sixty-seven.

## 6. What product decision followed?

Split by use case, not replaced. See [decision-record.md](decision-record.md): the small model
keeps everything interactive and every per-document task; the large one takes scheduled multi-step
analysis, with a written routing checklist.

## 7. Limits of this measurement

- **The reasoning verdict is a single non-blinded human review** over 6 scenarios. Tool-call counts
  and latency are objective; "better answer" is not. If the two signals had disagreed, we had no
  way to adjudicate — which is a design flaw in the evaluation, not a caveat about the result.
- **Three of the six reasoning scenarios failed for both models**, because the test corpus could
  not support them. The comparison effectively rests on three scenarios plus the efficiency
  statistics.
- **The extraction arm used a different variant** of the large model (a dense FP8 build) than the
  reasoning arm (the 4-bit MoE). Read the extraction result as *"a much larger model is not better
  at this task"*, not as a per-checkpoint measurement.
- **`n=1`** per scenario. Compound agent runs are not deterministic in tool count; repeated runs
  would give a distribution, and 108 vs 21 is far enough apart to survive that, while 5-vs-7 on a
  single scenario is not.
- **Same prompts for both models.** Prompts developed against the smaller model may under-serve the
  larger one, or vice versa.

## 8. The article

[Mikor érdemes nagyobb AI-modellt használni — és mikor nem?](https://docai.hu/blog/122b-vs-35b-mikor-jobb-a-nagyobb-modell) —
*„miért nem a 4× nagyobb modellt választottuk minden feladatra"*

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
