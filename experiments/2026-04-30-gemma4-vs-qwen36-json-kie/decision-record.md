# Decision record — keep the incumbent extraction model

**Date:** 2026-04-30 · **Status:** in force · **Experiment:**
[gemma4-vs-qwen36-json-kie](README.md)

## Decision

The document pipeline keeps Qwen3.6-35B-A3B-FP8 as its extraction model. The Gemma 4 candidate is
not piloted, not shadow-deployed, and not revisited without a change in one of the conditions
below.

## Why

Not because of the F1 gap — that number is contaminated by self-baseline bias and we do not treat
it as a measurement of model distance. The decision rests on two things the bias cannot explain:

1. **Every line-item array failed.** Nine out of nine. The failure is structural (whole document
   lines copied into the product-name field), not a scoring artefact, and it would make per-product
   analysis, price tracking and item-level VAT checks unusable.
2. **The header errors are in the expensive classes.** Invented dates where the document states
   none, enum values filled instead of left empty, identifier formats silently substituted. These
   are the errors that pass validation and surface weeks later in reconciliation.

Switching also had no upside to weigh against this: the candidate was ~55 % slower per unit on the
same corpus.

## What this decision does not claim

- That the candidate model is worse in general. It was evaluated on one task, with a prompt tuned
  for the incumbent, against ground truth derived from the incumbent.
- That the incumbent is error-free. It is not — measured against corrected ground truth on the
  same corpus, it scores 0.975, and its own remaining errors are documented in
  [qwen36-fp8-vs-nvfp4-quality](../2026-07-16-qwen36-fp8-vs-nvfp4-quality/).

## What would reopen it

- **Corrected ground truth plus a re-tuned prompt.** The fair version of this comparison needs
  both. If a candidate is given a prompt developed against it, and both arms are scored against
  ground truth that neither produced, the result is worth having.
- **A fixed line-item failure.** If a later checkpoint extracts clean product names, the rest of
  the comparison becomes close enough to be worth rerunning.
- **A cost or availability change** that makes the incumbent unattractive to serve.

## Follow-through

The measurement changed how we run all subsequent model comparisons:

- **Sub-task scoring is mandatory.** Header and items are reported separately, always. An
  aggregate that averages a total sub-task failure into a passing grade is not a metric we accept.
- **A score of 1.000 is treated as a ground-truth defect**, not a result, and triggers a
  correction pass before the comparison is published.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) ·
[Article (HU): Gemma4-et néztem, MTP-t találtam](https://docai.hu/blog/gemma4-vs-qwen36)*
