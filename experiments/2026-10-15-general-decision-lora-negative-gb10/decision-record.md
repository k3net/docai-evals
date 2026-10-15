# Decision record — no general decision adapter; treat "none of these" as a separate, target-domain decision

**Date:** 2026-10-15 · **Status:** adopted (round 3 closed 2026-10-15) ·
**Experiment:** [general-decision-lora-negative-gb10](README.md) · **Previous decision:**
[decision-lora-where-to-train-gb10](../2026-10-09-decision-lora-where-to-train-gb10/decision-record.md)

## Decision

1. **No general decision adapter in DocAI.** The general adapter (G3) is not deployed for any task. Nothing changes
   relative to the previous round's decision: the task-specific invoice-line adapter stays where it was measured, and
   tool selection continues with the calibrated read-out of the base model (L1★).
2. **Publication: a negative result, not an adapter to use.** The results page closed the question the protocol left
   open: G3 cannot be published as a general decision adapter (H1), and publishing the training data is independent
   of H1. On 2026-10-15, after the result, that recommendation was overridden for the adapter, and it was decided to
   publish
   - the three G3 seeds as a research artifact labelled "do not use"
     ([adapter](https://huggingface.co/k3dani/Qwen3.6-35B-A3B-hu-general-decision-lora-negative-result));
   - the training and validation splits in two licence configurations, permissive and share-alike
     ([dataset](https://huggingface.co/datasets/k3dani/hu-general-decision-mix));
   - this evidence package: the frozen protocol, the analysis code, the aggregate results and the hash chain of the
     read-outs.

   This publication decision was not a pre-registered rule; the protocol log records it (2026-10-15).
3. **The research line stops here for now; "none of these" is the open question.** On product matching and tool
   selection, G3's decisions on items with a correct option were about as precise as the base model's, and the precision
   failures came from "none of these" items it confidently assigned to an option. A follow-up round was drafted and is
   parked (protocol log, 2026-10-15). The draft tests three separate questions:
   - JEV-35B measured with our own read-out and calibration on our held-out layers;
   - a trainable decision head against the current label read-out, with everything else held equal;
   - splitting "none of these" into types (one-step and two-step decisions).

   The results page's own suggestion, studying the `X` decision on its own (two-stage, target-domain fitting) rather
   than more general decision training, is an input to that draft, not a decision.

4. **Rules a next round inherits, if the line resumes:**
   - **calibrate on the target traffic's "none of these" distribution.** A validation threshold did not carry over
     to any held-out group, and a 200-item target sample under the Clopper–Pearson rule found no threshold where
     confident errors sit at the top of the ranking. That needs either a larger target sample or a rule that still
     gives a threshold in that case (for example, precision at a fixed coverage);
   - **reconsider the English backbone.** It helped on Hungarian tool selection (H4) and, by a post hoc observation,
     hurt on English irrelevance; if it stays, it goes with English irrelevance types;
   - **do not use an arithmetic family alone as a held-out layer** for single-token decisions without thinking, or
     report it separately: the HO-új verdict hinged on the totals family, where every arm was weak.

## The rule that produced it (fixed before the analysis, v1 of 2026-10-14)

H1 per held-out layer, G3 (mean of three seeds) against the calibrated base model, at the validation threshold:

| result on a layer | verdict |
|---|---|
| G3 precision < 0.93, or coverage@95 or AURC significantly against G3 after Holm (six tests) | **does not meet the requirements** |
| otherwise, at least one endpoint significantly better after Holm, all three seeds on the favourable side | generalises on that layer |
| otherwise | undecidable |

No single successful layer would have supported a claim for all task families. **Result:** "does not meet the
requirements" on all three layers. Coverage rose by +11.1, +8.9 and +7.2 points, but precision was 0.912, 0.866 and
0.905. AURC was significantly worse on HO-termék and HO-routing, and better on HO-új. The calibration hypotheses
failed too:

- the validation threshold did not hold 0.93 on any layer;
- the calibration-sample threshold did not exist on HO-termék and HO-routing;
- on HO-új it held, but there G3 matched the base model.

## What we learned that the rule did not ask

- **The failure is the "none of these" decision, not the option choice.** G3 accepted 25 % (HO-termék) and 28 %
  (HO-routing) of the "none of these" items above the threshold; the base model accepted 9 % and 15 %. Round 2's
  irrelevance failure reappeared in a model that never saw the routing group, despite four trained kinds of "none of
  these" and an anchor to the base model on them.
- **When "nothing fits" depends on the domain.** Round 1's adapter, trained in that domain, recognises 94 % of the
  invoice-line "none of these" items, the base model 42 %, G3 34 %.
- **The two-stage fix does not rescue it.** Letting the base model decide "none of these" removes G3's damage
  (exploratory, on already used test layers). At equal precision it covers what the base model covers.
- **What transfers:** more decisions on every group at base-level precision on answerable items, and the KIE
  validation group's natural "none of these" ("none of the line items is wrong", `X` recall 0.01 → 0.84).

## What would reopen it

- **A general adapter, or a two-stage or `X`-head variant, that beats L1★ at equal precision on a held-out group,**
  with the threshold chosen on target-like data, and with a held-out test not used before (this round's held-out
  layers are spent).
- **A different base model or engine build.** Where the base model is weak, and how it handles "none of these", has
  to be measured again.
- **A soft-target teacher that passes the gate.** This round could not test the planned soft target, because no
  candidate passed.
- **A cheaper calibration rule for small target samples** that yields a threshold despite confident errors and
  holds precision on a fresh test.
