# Decision record — right model for the task, not one model for everything

**Date:** 2026-05-22 · **Status:** in force · **Experiment:**
[35b-vs-122b-business-tasks](README.md)

## Decision

Two models, routed by task. This is a routing decision, not a migration.

### The small model keeps

- **Interactive chat** — 2.6× the end-to-end latency on compound work is unacceptable in a chat
  box, and 6× on simple tool calls is worse.
- **Key information extraction** — it is measurably *better* here (F1 0.975 vs 0.938) at half the
  latency.
- **Per-document real-time processing** — single-document latency dominates.

### The large model takes

Scheduled and background work where quality outranks speed and a 5–15 minute window exists:

- cash-flow gap projection;
- supplier billing anomaly detection over 12–24 months of history;
- customer concentration risk;
- VAT position analysis;
- long-context analysis (50k–250k tokens) across multiple documents and years.

### Routing checklist

A task goes to the large model if **at least three** hold:

- [ ] three or more distinct tool calls with multi-step reasoning expected
- [ ] requires numeric inference (trend, percentage, ratio, concentration)
- [ ] compares multiple periods (2+ years) or entities (5+ partners)
- [ ] input over 32k tokens, or 5k+ tokens of output expected
- [ ] runs in the background, a 2-minute-plus SLA is acceptable
- [ ] the result goes to human review rather than straight to a user

The checklist exists so the routing decision does not get re-argued per feature. It is deliberately
mechanical.

## Why the evidence was efficiency, not accuracy

Pass counts tied on single-call tool use — 9/10 both ways, same failing scenario. Had we stopped
there, the conclusion would have been "no reason to run the bigger model", and it would have been
wrong.

What separated them was **21 tool calls versus 108** on compound scenarios. One model plans a
retrieval strategy; the other gropes toward one, once burning 67 calls without converging. That is
invisible on single-call tests and decisive on multi-step ones.

It also has a second-order benefit we did not set out to measure: a human reviewer can follow five
deliberate queries and cannot audit sixty-seven. For analysis that goes to human review, a compact
tool trace is part of the deliverable.

## The finding that surprised us

**A four-times-larger model is worse at extraction.** Careful reading of a short document against a
fixed schema does not reward scale — it rewards a model that has been prompted and tuned for
exactly that job. We had assumed a floor ("at least as good, just slower"); there was no floor.

Generalised: *model size helps where the task is composition, not where it is comprehension.*

## Conditions attached

1. **Speculative decoding stays on for the large model** — without it the latency gap widens to
   ~3.3× and the background use case thins out. Serving conditions:
   [bring-up decision record](../2026-05-22-qwen35-122b-nvfp4-bringup-gb10/decision-record.md).
2. **Human review stays in the loop** for the large model's output. It is routed to tasks whose
   results feed decisions, not to tasks whose results go straight to a user.
3. **The routing checklist is the interface.** New background features declare against it rather
   than picking a model by preference.

## What would reopen it

- **Native FP4 compute on this hardware**, which would put the large model in the small one's
  latency range and make the interactive verdict worth re-testing.
- **A mid-size distillate** — the plausible sweet spot between compound reasoning and interactive
  speed.
- **A blind-scored rerun.** The reasoning verdict deserves written rubrics and a blind judge; if it
  contradicted the tool-call evidence, this decision would need rebuilding.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) ·
[Article (HU): Mikor érdemes nagyobb AI-modellt használni — és mikor nem?](https://docai.hu/blog/122b-vs-35b-mikor-jobb-a-nagyobb-modell)*
