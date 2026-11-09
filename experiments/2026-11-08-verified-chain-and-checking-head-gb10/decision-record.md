# Decision record — keep the computable steps in code; check the chain on fresh real data next; close the head question with a narrowed claim

**Date:** 2026-11-08 · **Status:** adopted (rounds 05a–08 closed 2026-11-08) ·
**Experiment:** [verified-chain-and-checking-head-gb10](README.md) · **Previous decision:**
[general-decision-lora-negative-gb10](../2026-10-15-general-decision-lora-negative-gb10/decision-record.md)

## Decision

1. **The chain's next step is a fresh real-data sample, not a product specification.** The evidence that the chain
   works is synthetic: the pre-registered trap-item result (K2), the repair round on fresh synthetic items (J), and the
   natural-mix closure counts (K3). The protocol's own wiring (D9 in the 08 runbook) would let a passing K2 go to a
   product specification; we do not take that step on synthetic evidence. The next step is a pre-registered check on
   about 150 **fresh real bank items** with the threshold fixed in advance: the chain's bindings and the model's own
   closures reported separately, each against a ≤ 2 % target (the round 08 D10 decision, 2026-11-06), new closures
   descriptive. The 262 items of round 07B / K08V are development numbers and do not count.
2. **The checking head's question is closed, with a narrowed claim and no product use.** The pre-registered gain in
   round 08 (G5, K1(a): L-RN − L-S AUROC +0.186, Holm interval [0.111; 0.269]) is arithmetically right but measures a
   construction artefact: a text-only TF-IDF classifier separates the two classes at 1.000. With the matched control
   M (+0.144 [0.085; 0.211], text-only 0.998) the pre-registered reading is "not evidence"; with minimal pairs N (+0.075
   [0.028; 0.131], text-only 0.699) it is "the claim stands in a narrowed form": this rule family, this construction,
   these heads. At the operating point N is unusable (undecidable items closed above threshold 77.7 % with the head,
   37.9 % with the model's own score), and on real bank items the head does not beat the model's own score (0.910 and
   0.911, development numbers). K1(b), the wrong-reading question, is not decidable. No product benefit is claimed
   and no further control is planned.
3. **Publication: the article and this package now; a study and a dataset later.**
   - The blog article ([English](https://docai.hu/en/blog/dont-train-what-you-can-compute),
     [Hungarian](https://docai.hu/blog/amit-ki-lehet-szamolni)) and this evidence package are published now.
   - No Hugging Face dataset or model in this round. The later study will carry a dataset, so the synthetic item
     files, generated texts and per-item outputs are not released here; the package publishes the generators and code,
     the frozen protocols, the manifests and the aggregate machine outputs.
4. **Rules the next round inherits:**
   - **Run the text-only baseline before freezing any constructed contrast.** The G5 surface test took minutes and
     would have caught the artefact; rounds M and N exist because it was run late.
   - **A real-data chain does not extract references with the model.** On real payment notes the model extracted 30 of
     93 verbatim references and the chain could bind 22 items; the deterministic search for candidate invoice numbers
     bound 70 with 0 errors (K08V, development numbers). The 08B plan uses the search.
   - **Report the model's own closures separately from the chain's bindings.** The chain's 0 / 70 hid the model-side
     error rate of 3.6 % (2 / 56) in the development sample.
   - **Do not expect coverage from the chain alone on a natural mix.** K3 shows no gain over the no-chain 07 head on
     the rule family; the chain's value is on trap items and in the safety of its bindings (363 bindings, 0 wrong, on
     the bank family's natural test).

## The rules that produced it (fixed before the analysis, D12 and addenda)

| round | frozen | rule | result |
|---|---|---|---|
| 05a | 2026-10-29 | ≥ 2 of 3 held-out layers: ΔAURC (S+N) interval below zero, precision ≥ 0.93 where a working point exists, MTX guard | **does not advance** (S3 0/3; S5 1/3): the frozen head does not transfer; the 05b gate stays closed |
| 06 | 2026-10-31 | reliability head on the target domain: ≥ 2 of 3 families improve, average AURC ratio ≤ 0.90, upper bound < 1 | **met** (0.205 [0.187; 0.224]), with the decomposition reporting that the rule "`NONE` last" explains 72% of the average gain |
| 07 | 2026-11-01 | four-state prompt: K1 ratio rule; K2 "brings it in" / "improves on top" | K1 met (0.507); the prompt alone does not bring the head in (−29.6 points); the head improves on top (+27.9 points, closure error 2.5%) |
| 07 K3 | 2026-11-01 | trap items, pre-registered readings | no arm recognises the skipped-calculation error (B1-4R 0.452 [0.393; 0.507]; B1-4S 0.413 reversed) |
| 08 D12 | 2026-11-04 | chain: correct ≥ 90 %, false pass ≤ 2 % (K2); K1 reading table (Holm); K3 natural mix | K2 correct 97.5–98.9 %, **false pass target failed on the fault family (3 / 91 = 3.3%)**; K1(a) "improves materially" (+0.186), K1(b) not decidable; K3 natural mix: L-RN − L-S +9.3 / +4.7 points, not from targeted training |
| 08 J | 2026-11-05 | fresh trap items, same targets **plus no false exclusion and no false binding** | met on all three families (correct 98.6–100.0 %, false pass 0 / 197, 0 / 210, 1 / 220) |
| 08 M | 2026-11-06 | matched control: if matching holds, keep/reject; if matching fails and the head wins, "not evidence" | matching failed; the head still won (+0.144 [0.085; 0.211]): "not evidence" |
| 08 N | 2026-11-08 | minimal pairs: "narrowed claim stands" if L-RN − L-S lower bound > 0 and estimate ≥ 0.05 and L-RN above the best text-only model | met (+0.075 [0.028; 0.131], 0.872 against 0.699) |

Separately documented, not part of a rule: the first N audit failed its gate at 3 / 30, a filter was written from
those errors and a fresh 30 passed at 0 / 30.

## What we learned that the rules did not ask

- **Most of the head's early gain was state conventions, not reliability.** In round 06, 72% of the average AURC gain
  over the base model's own score comes from moving `NONE` answers last, with no training, and under lenient correctness
  the gain disappears (ratio 0.965 [0.881; 1.063]). In round 07 the four-state prompt recovered part of it directly.
- **Confidence is reversed where a calculation is skipped.** On trap items the model's confidence and the head are
  at or below chance on the error itself; with unchanged thresholds, natural-test closure errors of 1.3–3.8 % become 27–100
  % on trap items. Giving the computed value recovered most of it (29 → 100 %, 52 → 94 %, 24 → 67 %; exploratory,
  upper bound).
- **Extraction is the weak link on real text.** Synthetic extraction loses 0.5–1.1 points against oracle fields; on
  real payment notes the model brought out only 30 of 93 references that were verbatim in the note.
- **The chain's errors are safe-direction and bounded.** All pre-registered false passes were caught extraction errors,
  no false exclusion and no false binding in the pre-registered measurements; two extraction error types (80 for 800 mOhm,
  "40%" read as an amount) remain unfixable by the repair.

## What would reopen it

- **A fresh real-data sample that fails the chain** (bindings or model closures above the ≤ 2 % target under the
  pre-registered threshold), or passes it: the second would justify a discussion of a product specification, which
  this package deliberately does not make.
- **A checking-head construction that beats a text-only baseline by more** on a family other than expense rules, with the
  text-only model run first and a working point that holds at equal error rate on fresh data.
- **A different generator or subject model.** The numbers rest on one synthetic generator, three families, and one
  subject model, engine build and machine.
- **A real-data sample of undecidable items**, which this round does not contain.
