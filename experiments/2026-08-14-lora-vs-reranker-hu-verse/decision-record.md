# Decision record — score the output before you train the model

**Date:** 2026-08-14 · **Status:** in force ·
**Experiment:** [lora-vs-reranker-hu-verse](README.md)

## Decision

When DocAI output comes out in the wrong *shape*, the first attempt is a **deterministic scorer
over N samples**, not a fine-tune. Fine-tuning is reserved for what a scorer provably cannot buy:
register and voice, where the target cannot be expressed as a scoring function.

This is a decision about method and sequence, not a ban. Both techniques earned a place; the
measurement told us which one buys what.

## The rule that produced it

We fixed the acceptance criterion before running anything:

> The LoRA is worth its cost only if it beats **B2** — few-shot prompting plus a deterministic
> best-of-8 reranker — on the primary metrics. Comparing it to the raw model alone is a rigged
> comparison.

That sentence is the whole decision record. Everything below is what happened when we honoured it.

| Gate | Question | Outcome |
|---|---|---|
| **1 — form** | Does training beat the training-free selector on measurable structure? | ❌ **No** — worse on all six form metrics, and 3× the invented words |
| **2 — style** | Does training buy something the selector cannot? | ✅ **Yes** — 56.0% → 92.0% author recognition, selector held constant |
| **3 — safety** | Does the adapter memorise the training corpus? | ✅ Clean — gap +0.05 words, *smaller* than the base model's +0.10, zero 8-word spans |

Gate 1 is the surprise worth stating plainly: **64 minutes of GPU time lost to a few dozen lines of
scoring code.** Gate 2 is why the answer is not "don't fine-tune".

## Why both, and in this order

A selector maximises exactly what its scoring function measures. If the goal is expressible as a
score — syllable counts, JSON validity, field presence, line lengths, a required section order —
then sampling N times and keeping the best is cheaper, more predictable, and free of the side
effect we measured: the fine-tuned model invented words to satisfy the rhyme, because rhyme was
what the objective rewarded and vocabulary was not.

A selector also cannot buy what it cannot score. Adding the reranker to the prompt-only branch
moved author recognition by **−0.4 points** while improving every form metric. Register lives
outside the scoring function, so no amount of sampling surfaces it.

Hence the sequence: **express the goal as a score first.** Whatever survives as genuinely
unscoreable is the fine-tuning candidate — and by then you also have your baseline.

## What this binds

1. **Any fine-tuning proposal must name its training-free opponent** before the GPU is booked, and
   the opponent must be the best available one, not the raw model. Already repaid once: on a later
   classification measurement a plain TF-IDF baseline matched a 7,296-dimensional embedding
   pipeline on the classes it covered, which changed what that experiment was about.
2. **Checkpoint selection may not rest on validation loss when the loss is not the task.** Here the
   loss minimum sat at 1 epoch and the 3-epoch checkpoint was better on *every* measured axis. A
   50-item task measurement settled it in six minutes; run that instead.
3. **Overfitting and memorisation are measured separately.** A rising validation loss is not
   evidence of memorisation, and only a control arm — held-out items the base model has likely
   seen in pretraining — separates our contribution from inherited knowledge.
4. **On a hybrid architecture, enumerate the adapter targets.** Qwen3.5 is one: three quarters of
   its token-mixing layers are linear-attention blocks with a different parameter namespace, so the
   conventional attention-only recipe silently covers 8 layers of 32. Print the module list; do not
   copy a target set from a paper.
5. **Two-stage vocabulary checks for anything claiming archaic or domain register.** A spellchecker
   flags 7.9% of the human poet's own words. One-stage, the model's invented vocabulary would have
   read as successfully learned style.

## What would reopen it

- **A scoreable target that a selector still fails.** If best-of-N plateaus well below a
  fine-tuned arm on a metric we can compute, that is a direct counter-example and worth acting on.
- **Cost inversion.** Best-of-8 costs eight generations. On a high-volume path where inference is
  the bottleneck, a fine-tune that reaches the same quality single-shot wins on economics alone —
  note that the best arm here (LoRA + reranker) was already *faster* than the best training-free
  arm, because it needs no examples in the prompt.
- **A voice requirement in production.** So far our output targets have been structural. The first
  genuine register requirement — a Hungarian business-writing tone, a house style for generated
  documents — falls on the fine-tuning side of this decision, and the +36-point result is the
  evidence for trying it.
- **Copyrighted training material.** The memorisation result is clean, but it was measured on
  public-domain text with a 0.4% adapter. It does not transfer to protected corpora, and a
  measurement on those would need its own legal basis before its own gate.

Until then: write the scorer, keep the baseline, and fine-tune for the voice.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) ·
[Article (HU): Versel nekünk az AI — de tud-e Arany Jánosul?](https://docai.hu/blog/versel-nekunk-az-ai)*
