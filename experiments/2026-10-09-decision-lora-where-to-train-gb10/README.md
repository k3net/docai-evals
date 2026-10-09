# Where is it worth training a decision adapter? — one recipe, two tasks, opposite results (Qwen3.6-35B-A3B-FP8, GB10)

**Date:** 2026-10-03 → 2026-10-09 · **Reproducibility:** R1 (code, data, per-item read-outs; round 2's
public-benchmark rows as hashed references, rebuilt from upstream — see §7) · **Card:** [eval-card.yaml](eval-card.yaml)
· **Decision:** [decision-record.md](decision-record.md) · **Pre-registered protocols (Hungarian):**
[protocol/](protocol/) · **Round 1 adapter and dataset:**
[`Qwen3.6-35B-A3B-invoice-decision-lora`](https://huggingface.co/k3dani/Qwen3.6-35B-A3B-invoice-decision-lora),
[`hu-invoice-catalog-decisions`](https://huggingface.co/datasets/k3dani/hu-invoice-catalog-decisions) (Hugging Face)

> We trained a small LoRA adapter on a served chat model so that it answers with one label token — one of the
> offered options, or "none of these" — with a calibrated probability. The bar was not the raw model but the same
> model untrained and carefully calibrated. On matching invoice lines to catalogue articles the adapter won by
> **13.7 points** of automated coverage at 95 % precision. On tool selection, with the same recipe, it **lost** to
> the calibrated base model. The recipe did not change; where the base model was weak did. Two pre-registered
> rounds, eleven hypotheses, 15 654 test items, and one external model compared on the same items.

---

## 1. What was the measurement for?

Two places in DocAI need a machine decision that knows when not to decide: assigning purchase-invoice lines to the
article catalogue, and choosing which tool an agent calls for a request. In both, an uncertain decision must go to
a person instead of being booked automatically, so the model has to give a calibrated probability, not only an
answer. The obvious candidate is a small decision adapter on the instance that already serves chat. Round 1 asked
whether it beats the calibrated base model on invoice lines; round 2 asked whether the same recipe transfers to tool
selection.

Both protocols — hypotheses with refutation criteria, primary endpoints, statistics, and the publication rule,
including what happens if the adapter fails — were fixed before any arm touched the test set: round 1 on
2026-10-03, round 2 on 2026-10-08. Later changes are dated in each protocol's log (`Napló`), mistakes included.

## 2. On what task and dataset?

The decision has the same form in both rounds: given an item and 2–10 candidates, answer with one label token
`A`–`J`, or `X` when none fits. The label probability restricted to the label tokens is the confidence.

| | round 1 · invoice line → article | round 2 · tool selection |
|---|---|---|
| item | a Hungarian purchase-invoice line (supplier, free text, quantity, unit, unit price) and candidate articles | a request (with history) and candidate tools with descriptions |
| data | **synthetic**: an invented catalogue (3 514 articles) and suppliers generated from the aggregated purchasing profile of one real business; no real row is in it | **public**: BFCL v3 (incl. live), When2Call, xLAM, MASSIVE hu-HU mapped onto our 62-tool general catalogue, generated Hungarian catalogue requests, EU-180k |
| train / val / test | 5 593 / 1 006 / 3 534 in four layers + 2 107 with 16 new suppliers | 14 513 / 3 524 / 10 013; the scored pool is 7 561 items over five layers |
| "none of these" in test | 25 %, mostly forced (the right article removed from the list) | 33 %, mostly genuine irrelevance (BFCL-live, When2Call) |
| "none of these" in training | built the same way as in test | 80 % forced, 20 % natural (499 When2Call "cannot answer", 255 chit-chat) |
| labels | constructed; two independent LLM judges (Llama-3.3-70B, Mistral Small 4) pre-filtered, then a stratified human review (424 items); residual noise 0.40 % (upper 1.36 %) | benchmark gold for BFCL / When2Call; the scored Hungarian layers reviewed in full by a GPT-based agent with a blind human audit; residual 1.2 % (upper 2.4 %), above the 2 % gate |

Round 1 test layers: `T-belso` (seen supplier and article, unseen pair), `T-szallito`, `T-kozeli` and `T-tavoli`
(two held-out category branches, near and far). The supplier layer turned out not to be held out (§5.3); a
pre-registered addendum (00b) measured 16 genuinely new suppliers. Round 2 pool: `T-BFCL`, `T-BFCL-live`,
`T-When2Call`, `T-hu` (the reviewed MASSIVE subset) and `T-katalogus`.

Datasets here: [dataset/r00/](dataset/r00/) (the three evaluation splits, byte-identical to Hugging Face) and
[dataset/r01/](dataset/r01/) (its [README](dataset/r01/README.md) explains the full and the reference rows).
Hashes: [corpus_manifest.json](corpus_manifest.json).

## 3. Which models and configurations were compared?

One served model, `Qwen/Qwen3.6-35B-A3B-FP8`, on vLLM 0.30.0 (`vllm/vllm-openai:v0.30.0`, `sha256:8a69ffad…`), one
DGX Spark (GB10, 128 GB). Every arm of a round runs on the same instance, so paired differences cancel instance noise.

| arm | what it is |
|---|---|
| `L0` raw read-out | the base model's label probabilities, restricted to the label tokens |
| **`L1★` calibrated read-out** | the same averaged over four option orders, with a temperature fitted on the validation set — the best the model gives without training, and **the baseline** |
| **`L3` decision adapter** | LoRA r16 on the attention and GatedDeltaNet projections and the shared-expert MLP (none on the routed experts), 1 epoch, cross-entropy on the present labels + 0.5·Brier, ε = 0.05, in round 2 with 30 % option permutation; trained in BF16 on a de-quantised copy, served on the FP8 checkpoint; temperature-calibrated; three seeds |
| `L2a` probe (round 1) | a linear probe on the layer-40 hidden state, HF engine |
| `L0n` native tool calling (round 2) | the chat template with `tools`, greedy — did it call, and which tool |
| `S2` thinking (round 2, post hoc) | items below the L3 threshold re-decided by the base model in thinking mode |
| JEV-27B, JEV-9B, JEV-Gemma4-26B-A4B (round 2, external) | AutoTrust's distilled decision models, not run by us: their published per-item probabilities on the Decision Index (When2Call MCQ, CLINC150+OOS) |

## 4. Which metrics?

- **Coverage at 95 % precision (`lef@95`, primary):** the share of scored items the arm assigns to an option above a
  threshold τ. τ is chosen on the validation set: the smallest threshold above which the one-sided 95 %
  Clopper–Pearson lower bound of precision is at least 0.95. On test, precision below 0.93 is a **precision
  failure**. Its upper bound is the ceiling — the share of items that have a correct option.
- **AURC (co-primary):** area under the risk–coverage curve of the arm's own assignments; also reported cut to a
  common coverage, because an arm that assigns more gets a longer curve.
- **ECE** (15 equal-mass bins); **X-coverage**: the share of "none of these" items whose top label is `X`,
  threshold-free (round 2, H5).
- **Statistics:** hierarchical bootstrap (seed × cluster), 10 000 replicates, the validation set resampled and τ
  re-chosen in every replicate; Holm correction over co-primary endpoints; exact supplier permutation for the
  new-supplier layer.
- **Post hoc (round 2):** call/no-call separation on When2Call — AUROC of the call probability (1 − P(X) for our
  arms, P(tool call) for JEV) and the false-call rate at 90 / 95 % recall of correct calls.

## 5. What was the result?

Full sheets (Hungarian): [results/r00/eredmenylap.md](results/r00/eredmenylap.md) ·
[results/r01/eredmenylap.md](results/r01/eredmenylap.md) · interpretation:
[protocol/01-F4-ertelmezes.md](protocol/01-F4-ertelmezes.md).

### 5.1 Round 1 — invoice line → article: the adapter wins

| arm (vLLM, pooled test, 3 020 scored, ceiling 0.756) | lef@95 | precision | AURC | ECE | X-precision / X-coverage |
|---|---|---|---|---|---|
| L0 | 0.596 | 0.957 | 0.0370 | 0.048 | 0.850 / 0.385 |
| L1★ | 0.616 | 0.975 | 0.0273 | 0.043 | 0.891 / 0.434 |
| **L3** (3 seeds; range) | **0.752** [0.745–0.761] | 0.979 | **0.0018** | **0.010** | 0.945 / **0.957** |

- **H1 holds:** +13.7 points [4.8; 21.0], AURC −0.0255 [−0.0300; −0.0213]. L3 sits practically at the ceiling.
- **The gain is the "none of these" cases.** At the 95 % target, 42 of L1★'s 46 errors are "none of these" lines
  booked to an article. X-coverage rises from 0.43 to 0.96. At 70 % coverage the error rate falls from 4.8 % to
  0.4–0.5 %.
- **H2 — it generalises:** held-out category branches +9.8 points [1.7; 15.5]; 16 new suppliers (00b)
  **+19.5 points [10.2; 29.2]**, positive on all 16, exact supplier permutation p = 3.1·10⁻⁵.
- **The size of the gain depends on the share of "none of these":** +13.7 at the test's 25 %, +3.5 when thinned to
  10 %, +1.1 at 5 %.
- **H4 (probe):** L2a beats L1★ by 6.4 points [0.95; 13.3] but stays below L3. **H5:** ECE 0.043 → 0.010. H6 (a
  separate decision head) was not run.

### 5.2 Round 2 — tool selection: the adapter loses

| arm (pool, 7 561 scored, ceiling 0.669) | lef@95 (/ceiling) | precision | AURC | ECE | X-precision / X-coverage |
|---|---|---|---|---|---|
| L0 | 0.684 (1.02) | 0.893 ⚠ | 0.0333 | 0.056 | 0.912 / 0.762 |
| **L1★** | 0.717 (1.07) | 0.882 ⚠ | **0.0331** | **0.023** | 0.919 / **0.762** |
| L3 (3 seeds; range) | 0.767 (1.15) [0.758–0.775] | 0.840 ⚠ | 0.0609 | 0.088 | 0.964 / 0.673 |
| L0n native tool calling | call rate 0.674 | 0.850 | — | — | — / 0.735 |

⚠ precision failure. A coverage/ceiling ratio above 1 means the arm assigns "none of these" items to a tool.

- **H1 refuted on both endpoints.** Coverage +4.9 points [3.6; 6.6], but precision fails for every seed
  (0.83–0.85); AURC is significantly better for the base model (+0.0279 [0.0219; 0.034]). Cut to a common
  coverage it is the same: at 50 % coverage the error rate is 4.9 % for L1★ and 7.3–8.0 % for L3.
- **H5 refuted:** X-coverage −8.9 points [−11.4; −6.3]; non-X accuracy +1.4.
- **H3 holds, but not because of the adapter:** at native tool calling's operating point L3 is 3.4 points more
  precise at equal coverage and covers 7.4 points more at equal precision — L1★ gives +5.7 and +5.1 at the same
  point, without training.
- **H4 holds:** the round-2 adapter and the round-1 adapter loaded together on one instance, under serial and c = 16
  mixed traffic, agree with single-adapter instances within the noise floor of two fresh instances (all four
  conditions).
- **H2 formally "generalises"** (T-BFCL-live + When2Call +5.3 points, T-hu +5.1), because its definition judged the
  coverage difference without a precision condition. A pre-registered rule, left as written; nothing rests on it
  once H1 fails.
- **No arm keeps 95 %:** τ chosen on validation gives 88 % precision on test even for the base model — the
  validation "none of these" items (forced, xLAM and MASSIVE) do not represent the test's genuine irrelevance.

### 5.3 Why the result flipped (post hoc, descriptive)

**Little left to gain.** On items that have a correct tool, the untrained model already assigned 93–100 % of BFCL
and When2Call items at 97–100 % precision; L3 takes that to 98–100 %. The base model was trained for tool calling,
and not for invoice-line matching — in round 1, L1★ stood at 0.616 under a 0.756 ceiling.

**Where there was something to gain, training made it worse.** The precision drop comes entirely from "none of
these" items:

| source (X items) | n | L1★: X-coverage / assigned @95 | L3 (3 seeds): X-coverage / assigned @95 |
|---|---|---|---|
| BFCL irrelevance | 240 | 0.858 / 0.142 | 0.717–0.738 / 0.263–0.283 |
| BFCL-live irrelevance | 875 | 0.657 / 0.331 | 0.504–0.560 / 0.432–0.482 |
| When2Call "cannot answer" | 1 035 | 0.775 / 0.210 | 0.689–0.730 / 0.269–0.309 |

80 % of the training "none of these" items were forced: the same request with the right tool removed. What that
teaches is "if a similar tool is listed, call it". The test put genuinely irrelevant requests next to close but
wrong tools. In round 1 the test's "none of these" items were forced in exactly the training's way, so the same
lesson matched. 499 When2Call-type genuine irrelevance items in training (13 % of the training X) did not
counterbalance it.

**Source conventions burn in.** In T-hu the review corrected 40 MASSIVE labels; L3 gives the old label on 18–24
of them, all above τ (the base model on 8). Without those 40, L3 is better on T-hu (AURC 0.0011–0.0019 vs 0.0028).

**Two post-hoc repairs did not help.** Thinking mode on the items below τ: 1 743 items, 96 % of them "none of
these", 95 % of those recognised — but L3's errors sat above τ, confidently. A two-stage decision (the base model's
P(X) decides whether to call, L3 picks the tool) keeps X-coverage at the base level but adds only ~1 point of
coverage (0.726 vs 0.717), and the validation τ still fails on precision.

### 5.4 A public soft-target model on the same items (F5b)

Is hard-label training the problem — would a model distilled on a teacher's full distribution keep calibration?
[AutoTrust published](https://huggingface.co/datasets/autotrust/jev-decision-index-results) the per-item
probabilities of their distilled decision models on the Decision Index. We rebuilt the gold from the benchmark
kit's pinned sources (`kor01/eszkozok/f5b_jev.py`; their published accuracies are reproduced exactly on both
tracks) and compared on the 2 328 When2Call items that our round-2 test shares with it (1 293 correct calls,
1 035 "cannot answer"):

| | AUROC call vs no call | false calls @90 % correct calls | @95 % | calls on "cannot answer" |
|---|---|---|---|---|
| **L1★ calibrated base** | **0.964** | 8.6 % | **14.1 %** | 22.5 % |
| L3 (3 seeds) | 0.945–0.959 | 9.5–11.7 % | 15.7–17.3 % | 27–31 % |
| JEV-27B | 0.949 | 9.7 % | 37.3 % | 6.2 % |

JEV-27B's low call rate is a more cautious operating point, not a better separation: it also skips 13 % of the
correct calls. Threshold-free it lands at our adapter's level, and both fall short of the calibrated base model.
On CLINC150 out-of-scope requests JEV-27B recognises 38 % (in-scope accuracy 89 %); its Gemma-based sibling, which
saw CLINC's training split, 67 %. The frames differ — JEV chooses among four response modes, our arms among tools
plus X — the items are the same. This is not a fault of JEV: its card measures teacher fidelity and accuracy on a
fixed option set, and its authors' published results are what made this comparison possible.
[results/f5b/f5b_jev.json](results/f5b/f5b_jev.json).

### 5.5 Serving

Two adapters on one instance work (round 2, H4). Enabling LoRA support at all changes the instance: with
`--enable-lora`, vLLM 0.30 switches the MoE FP8 kernel (DeepGEMM → Triton) for every request, including those
without an adapter. About 6 % of uncertain decisions flip and the instance can land in a different numeric mode per
restart; no accuracy loss is detectable at ±1.3 points (round 1, H3 refuted on its condition (d)). A decision costs
~160 ms one at a time and ~15 decisions/s concurrently on one GB10; the adapter request adds 3–10 %.

## 6. What product decision followed?

See [decision-record.md](decision-record.md). In short: the invoice-line adapter is a real gain and stays — it is
published with its serving note. The tool-selection adapter is **not published**, by the pre-registered rule: on
the held-out test the calibrated base model is better or equal, and whoever downloaded it would be worse off than
with a careful read-out of the base model. Tool selection in DocAI continues with the calibrated read-out (L1★)
and no adapter. The next round — a general Hungarian decision adapter over many task families — inherits four
rules: train only where the calibrated base model is weak; train several kinds of "none of these", not only forced
ones; anchor to the base model on the "none of these" items; choose the threshold on target-traffic data.

## 7. What are the limits of the measurement?

- **One model, one quantisation, one engine, one hardware.** Where another base model is weak has to be measured
  again; that is the point of the result.
- **Round 1 is synthetic**, from one generator family, with mostly constructed "none of these" items; validation on
  real customer data happens separately and is not published. The tenant profile the generator used is not
  published; the frozen dataset is.
- **The round-1 gain depends on the real share of "none of these"** (+13.7 at 25 %, +3.5 at 10 %).
- **Round 2's Hungarian labels** carry an estimated residual noise of 2.4 % at the upper bound, above the
  pre-registered 2 % gate. The reviewer was a GPT-based agent; every label correction it made is human-confirmed
  (`meta.atnezes.forras` in [dataset/r01](dataset/r01/README.md)).
- **Round 2's public-benchmark rows are references, not rows** (BFCL is test-only by protocol; xLAM's generator
  licence is still being checked). They are rebuilt from upstream with the published converter; per-row sha256
  allow checking a rebuild, but a clean-room rebuild has not been run. Scoring from the published read-outs is
  verified ([code/verify_package.py](code/verify_package.py)).
- **The JEV comparison** runs in a different frame on the same items, from the authors' published probabilities;
  the JEV models were not run.
- **The mechanism analyses (§5.3) are post hoc**: they explain, they do not change a verdict.
- **Throughput figures** come from one instance, one run each.
- **The round-1 supplier layer was not held out** — a generator bug put its 14 suppliers into training (found in
  the self-check, protocol log 2026-10-07); H2 on that layer is reported as not testable, and the 00b addendum
  measured 16 genuinely new suppliers.

## 8. Which DocAI article belongs to it?

- Research report (Hungarian, long form): https://docai.hu/kutatas/hol-erdemes-tanitani
- Blog (Hungarian): https://docai.hu/blog/hol-erdemes-tanitani · English: https://docai.hu/en/blog/where-to-train-the-model
- Background: [Döntési modellek: a modell, amely nem ír, csak dönt](https://docai.hu/blog/a-modell-amely-nem-ir-csak-dont)

## Reproduce

```bash
pip install -r code/requirements.txt
python3 code/verify_package.py
```

CPU only, about ten seconds. It checks every dataset file against [corpus_manifest.json](corpus_manifest.json)
(and round 1's splits against the Hugging Face manifest), then recomputes L0, L1★ and L3 for round 1 (test and the
16-new-supplier layer) and round 2 (every reported layer) from the published read-outs with the measurement's own
scoring code, and compares 1 491 published numbers. On 2026-10-09 all matched to within 1e-9. Not recomputed: the
bootstrap intervals (run `code/eszkozok/f4_elemzes.py`, `code/eszkozok/k00b_elemzes.py`,
`code/kor01/eszkozok/f4_elemzes01.py`), the HF-engine read-outs, serving, and the JEV comparison.

Re-running the read-outs needs a GPU, the public base model, and for round 1 the published adapter; the round-2
adapter is retrainable from `code/eszkozok/tren_lora.py` and the dataset (three seeds, several hours each on one
GB10).

## Layout

```text
protocol/   both pre-registered runbooks with their logs, the round-2 draft before fixing, interpretation (Hungarian)
code/       eszkozok/ (round 1 + shared: generator, read-out, training, analysis) · kor01/eszkozok/ (round 2) · verify_package.py
dataset/    r00/ the three evaluation splits of hu-invoice-catalog-decisions · r01/ full Hungarian rows, reference rows, catalogue
results/    r00/ result sheet, analyses, 00b, perf, read-outs · r01/ result sheet, analyses, H4, arm selection, read-outs · f5b/ JEV
```
