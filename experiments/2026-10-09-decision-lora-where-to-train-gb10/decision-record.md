# Decision record — keep the invoice-line adapter, no adapter for tool selection, train only where the base is weak

**Date:** 2026-10-09 · **Status:** adopted (round 1 published 2026-10-07; round 2 closed 2026-10-09) ·
**Experiment:** [decision-lora-where-to-train-gb10](README.md)

## Decision

1. **Invoice line → catalogue article: the decision adapter stays.** It automates 13.7 points more at 95 %
   precision than the calibrated base model, 19.5 points more with unseen suppliers, and recognises "none of these"
   in 96 % of cases instead of 43 %. Adapter and dataset are public on Hugging Face
   ([adapter](https://huggingface.co/k3dani/Qwen3.6-35B-A3B-invoice-decision-lora),
   [dataset](https://huggingface.co/datasets/k3dani/hu-invoice-catalog-decisions)), with the serving note below on the
   model card.
2. **Tool selection: no adapter.** The calibrated read-out (L1★: four option orders averaged, temperature fitted on
   validation data) continues in DocAI. The round-2 adapter is **not published**: on the held-out test the
   calibrated base model is better or equal, so whoever downloaded the adapter would be worse off with it.
3. **Serving.** With LoRA support enabled, vLLM 0.30 switches the MoE FP8 kernel for every request on the instance,
   with or without an adapter: about 6 % of uncertain decisions flip, with no detectable accuracy loss. An instance
   shared with existing traffic has to account for that; the model card says so. Several task-specific adapters can
   share one instance: two adapters together, under parallel load, answer as each does alone.
4. **The next round inherits four rules.** A general Hungarian decision adapter over many task families:
   - train a task family only where the calibrated base model is weak; where it is near its ceiling, the family
     goes into training at a small share only;
   - train several kinds of "none of these": natural unanswerable requests, out-of-scope requests with close
     options, missing preconditions — not only the forced kind (the right option removed);
   - anchor the adapter to the base model on "none of these" items, because the calibrated base model separated
     call from no-call best;
   - choose the threshold on data drawn from the target traffic, because a validation-set threshold did not carry
     95 % precision to a different kind of test for any arm.

## The rule that produced it (fixed before the test, both rounds)

| result | dataset | adapter | study |
|---|---|---|---|
| H1 holds and H2 generalises on every pre-registered layer | public | public (with notes) | full |
| H1 holds, H2 does not generalise on a layer | public | no | "the gain does not generalise" |
| H1 holds, H2 undecidable on a layer | public | no | states the need for a larger layer |
| **H1 fails** | public | **no** | "the calibrated logit is enough" — a publishable negative result |

Round 1: H1 holds (+13.7 points [4.8; 21.0]; AURC −0.0255); H2 generalises on the category layers and, in the
pre-registered addendum, on 16 new suppliers (+19.5 [10.2; 29.2]); H3 (no change to LoRA-free traffic on a
LoRA-enabled instance) fails → the round-1 protocol's "H1 holds, H2 generalises, H3 fails" row: adapter public with a
note. The note describes the measured kernel switch instead of the pre-registered wording ("HF/peft only, vLLM
serving not verified"), because the adapter does work in vLLM (protocol log, 2026-10-07). Round 2: H1 fails — precision below the failure line for all three seeds
(0.83–0.85 against 0.93) and AURC in the base model's favour (+0.0279 [0.0219; 0.034]) → dataset, read-outs and study
public, adapter not.

## What we learned that the rule did not ask

The same recipe gained where the base model was weak (round 1: L1★ at 0.616 under a 0.756 ceiling) and hurt where it
was strong (round 2: 93–100 % of items with a correct tool already assigned at 97–100 % precision). The probable
reason is the base model's training — tool calling yes, invoice-line matching no. And the training's "none of
these" items must look like production's: forced ones teach "call the similar tool".

## What would reopen it

- **A different base model or engine build.** Where the base is weak has to be re-measured; the round-1 kernel
  switch is vLLM-0.30-specific.
- **For invoice lines: a production "none of these" share far below 25 %.** The gain is +3.5 points at 10 % and +1.1
  at 5 %; at that point the adapter's cost (training, serving with LoRA enabled) has to be weighed again. Measured on real traffic
  before relying on the synthetic figure.
- **For tool selection: an adapter trained under the four rules above** that beats L1★ on a held-out test with
  genuine irrelevance, at a threshold chosen on target-like data.
- **A serving fix** in vLLM that keeps the MoE kernel unchanged with LoRA enabled would remove the caveat for shared
  instances (re-run round 1's H3, `code/eszkozok/f4_h3.py`).
