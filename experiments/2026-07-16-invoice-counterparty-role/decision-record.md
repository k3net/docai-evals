# Decision record — the counterparty gate is now mandatory

**Date:** 2026-07-16 · **Status:** in force · **Experiment:**
[invoice-counterparty-role](README.md)

## Decisions

### 1. The quantisation candidate is rejected

Immediate consequence, recorded in full in the
[quantisation decision record](../2026-07-16-qwen36-fp8-vs-nvfp4-quality/decision-record.md).
Gate 2 of 3 failed; the canary phase never started.

### 2. The counterparty gate runs on every model or prompt change

Any change to the extraction model, its quantisation, its prompt or its sampling parameters must
pass this gate on a representative corpus before it reaches production. Aggregate F1 alone is no
longer sufficient evidence of "no regression".

**Threshold:** the candidate's own-as-partner rate must not be significantly worse than the
incumbent's under McNemar's exact test on at least 100 representative documents. "Not
significantly worse" — with a stated sample size — rather than a fixed percentage, because the
absolute rate depends on the tenant's document mix.

### 3. Validation corpora must be representative, not merely available

A generic test tenant is not a validation corpus. For extraction changes, the corpus must contain
documents where the tenant's own company appears in context — which in practice means real customer
documents, which in turn means the validation runs on our infrastructure and only aggregates are
published.

## Why this became a rule rather than a one-off finding

The measurement that mattered was cheap: a hundred stored requests, a deterministic replay, a
sixty-line script matching two fields against a known tax number. No LLM judge, no annotation
budget, no manual review.

The measurement it corrected was expensive-looking and wrong: a hand-validated golden corpus, a
field-typed comparison, frozen normalisation rules, four models scored by identical code — and it
reported equivalence for a model with a 2× regression in the field group that drives bookkeeping.

The difference was not rigour. It was corpus composition. That is a repeatable trap, so it gets a
repeatable defence.

## Architectural consequence — the better fix

The gate stops bad models from shipping. It does not fix the underlying fragility: **we are asking
a language model to solve an identity-matching problem we already have the data to solve
deterministically.**

The tenant's own registered names, tax numbers and addresses are in our own store. Deciding which
party on the invoice is the tenant should be post-processing against that store, not an inference
the model makes from context. If it were:

- the failure mode disappears for every model, quantised or not;
- the 40–69 % speed gain from 4-bit weights becomes available again, because the capability we
  were protecting is no longer the model's job;
- the counterparty gate becomes a regression test on deterministic code rather than a model
  evaluation.

This is on the roadmap and is the first thing that would reopen the quantisation question.

## What would reopen this decision

Nothing reopens the *gate* — it is cheap and it caught a real regression. The candidate rejection
is reopened by:

- own-vs-partner resolution moving out of the model (above);
- a Hungarian-calibrated or less aggressive 4-bit checkpoint passing the gate on 100+ documents;
- a larger cross-tenant corpus that changes the significance picture.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) ·
[Article (HU): Negyven százalékkal gyorsabb, és mégsem váltunk](https://docai.hu/blog/nvfp4-kvantalas-miert-nem-valtottunk)*
