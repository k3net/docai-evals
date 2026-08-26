# Where does the knowledge live — does a multilingual model reach Hungarian facts through English?

**Date:** 2026-08-26 · **Reproducibility:** R1 (code + public corpus + full per-item results)
· **Card:** [eval-card.yaml](eval-card.yaml) · **Decision:** [decision-record.md](decision-record.md)
· **Corpus:** [dataset/](dataset/) · [corpus_manifest.json](corpus_manifest.json)

> "Prompt in English, the AI thinks in English anyway" is common advice in Hungarian AI circles.
> This measurement asks what is actually true in it — behaviourally, and inside the model.

The interesting part is not whether a model answers a Hungarian question. It is *how* it gets
there. If a multilingual model reaches language-bound knowledge by translating the question into
English first, then translating the answer back, that has consequences for every non-English
document pipeline. If instead the knowledge sits in a shared, language-independent representation,
the practical advice changes: the language of the prompt matters far less than the presence of the
source.

---

## 1. What was the measurement for?

DocAI processes Hungarian business documents with multilingual LLMs. Two questions follow directly
from that, and both were open:

- **Should we translate Hungarian prompts into English?** The advice is widespread, and if true it
  is cheap to act on.
- **How much does a model actually know about Hungarian-specific subject matter, and does it tell
  us when it does not?** This decides whether the answer is a bigger model or a retrieval layer.

The measurement was designed to answer both, and to separate the behavioural answer (what comes
out) from the mechanistic one (what happens in the middle layers).

## 2. On what task and dataset?

**Corpus.** 70 items in three languages (Hungarian, English, Chinese), frozen on 2026-08-22 and
published here in full:

| group | n | selection criterion |
|---|---|---|
| **ZH-only** | 19 | article on zh.wikipedia or Baidu Baike, none on en/hu Wikipedia (Wikidata sitelinks) |
| **HU-only** | 15 | article on hu.wikipedia, none on en/zh |
| **UNI** | 20 | article on all three wikis — shared knowledge, the control group |
| **UNT** | 16 | untranslatable concepts (8 Hungarian, 8 Chinese) |

70 items × 3 languages = 210 prompts, plus one well-translatable control word per UNT concept
(*segítség / help / 帮助* …) × 3 languages = **258 prompts** in total. The D3 measurement adds
16 English approximation prompts (and 16 third-language ones) on top.

The group names are shorthand. "ZH-only" means the item has an article on the *Chinese* Wikipedia
and none on the English or Hungarian one; whether the model's training corpus also contained it
only there is not verifiable, and four items carry a mention-level trace in another language
(flagged in the corpus). Throughout this experiment "source language" means this Wikipedia proxy,
not proven provenance.

**Why untranslatable concepts.** The UNT group is the trap set for the translation hypothesis. The
Hungarian *kaláka* is about reciprocity — help that must be returned; the English "mutual aid /
helping out" loses that. The Chinese *热闹* is warm, positive bustle; "noisy / crowded" is
negative. Each concept carries pre-registered native meaning components, distortion markers, an
English approximation and a control word from the same semantic field, so the loss can be scored.

**Prompt.** Deliberately minimal, unformatted continuation, because the base model does not follow
instructions and any wrapper would inject a language signal:

```text
hu:  Kérdés: {q}\nVálasz:
en:  Question: {q}\nAnswer:
zh:  问题：{q}\n回答：
```

## 3. Which models and configurations were compared?

Base model **Qwen3.5-9B-Base** and its post-trained sibling **Qwen3.5-9B**, served on a DGX Spark
GB10 (`sm_121a`), greedy decoding, seed 0, thinking disabled. Three variants, so that the effect
of the weights and the effect of the prompt format can be separated:

| variant | model | prompting |
|---|---|---|
| **base + raw** | Qwen3.5-9B-Base | raw continuation |
| **instruct + chat** | Qwen3.5-9B | chat template |
| **instruct + raw** (control) | Qwen3.5-9B | raw continuation |

The two checkpoints share a bit-identical tokenizer, so items pair across variants.

Four measurements come out of a single forward pass per prompt: (A) the generated answer,
(B) the layer-by-layer logit lens reading, (C) sparse-autoencoder feature activations,
(D) the untranslatability analysis. The SAE is `Qwen/SAE-Res-Qwen3.5-9B-Base-W64K-L0_50` — all 32
layers, 65,536 features, TopK-50.

**Judging.** Every answer is scored by **Qwen3.6-35B** against a fixed rubric
(correct / partial / incorrect / hallucination). On top of that, every ZH, HU and UNT answer
(102 + 48 per variant, **450 judgements**) was re-judged item by item by a second, stronger
judge, **GPT-5.6 Sol**. This second pass is machine judging, not human annotation — see the
limitations.

## 4. Which metrics?

- **Strict accuracy** per group × question language, with Wilson 95% intervals.
- **Confident fabrication rate**: share of *hallucination* labels among non-correct answers.
  Reported next to absolute counts, because the ratio moves when the denominator moves.
- **Intermediate readability** (logit lens): share of non-words in the top-20 per layer, and the
  language distribution of the readable tokens. The naive lens fails on this model (76% non-words
  on planes 0–23), so a rank-256 tuned lens was trained on a token-balanced 300k hu/en/zh
  Wikipedia sample (validation KL 2.85 → 1.03, non-words 76% → 31%).
- **Cross-language feature overlap** (SAE): Jaccard overlap of the feature union over the
  *question tokens* between two language variants of the same item, minus the same quantity for
  randomly paired items. Tested by item-level permutation at a pre-registered layer 16, Holm
  corrected over the 9 group × language-pair cells.
- **Pull towards the English approximation** (D3, pre-registered): whether the source-language
  concept sits closer to *its own* English approximation than to the other concepts'
  approximations. The follow-up question — whether that pull is English-specific, tested against
  the same approximation in a third language — is **exploratory**: it was added after the primary
  result was seen, and is what turns a positive primary result into "no positive evidence for a
  lexical pivot" rather than a confirmed negative.
- **Decoding pathologies**: truncation, repetition loops, self-evaluating suffixes — all flagged
  and reported per language, because all three are language-dependent and would otherwise be read
  as "Hungarian is worse".

Fixed before the run: layer 16 for the overlap test, layer 10 and the question-token span for D3,
a sign test as the primary D3 statistic, and a smallest effect size of interest of +0.02 Jaccard.

## 5. What was the result?

**Knowledge crosses the language border, asymmetrically.** Chinese-only knowledge asked in
Hungarian: 42% (in Chinese: 63%). Hungarian-only knowledge asked in Chinese: 20%. The universal
control group is 90–100% in all three languages, so the questions themselves are not hard.

**The most uncomfortable cell: Hungarian-only knowledge asked in Hungarian is 7%** — worse than
the same knowledge asked in English (13%) or Chinese (20%). On the untruncated, non-degenerate
subset it is 0% (n = 6). n = 15 makes these intervals wide and overlapping; the ordering holds in
this sample and repeats on the instruct variant (20 / 27 / 33%), but it is not a population
ranking.

**There is a shared middle layer, and it is thin.** All 9 group × language-pair comparisons are
significant at layer 16 (permutation test, raw p = 0.001, Holm ≤ 0.009). The shape matters more
than the point test: the excess is small at the embedding, peaks around layers 9–11 (UNI:
+0.095…+0.137) and shrinks again towards the output. Both pre-registered contrasts (middle minus
early, middle minus late) have intervals above zero in 6 of 9 cells. The absolute overlap stays
small (Jaccard ≈ 0.19 for the same item, ≈ 0.13 for random pairs): most of the representation
remains language-specific.

**No positive evidence for a lexical English pivot.** The English approximation never surfaces in
the middle-plane readings of non-English prompts (0/32, both lenses, both checkpoints) — but the
instrument is measurably insensitive, so this is weak evidence: on *English* prompts, where the
word is certainly relevant, it surfaces for only 3/16 concepts with the naive lens and 1/16 with
the tuned one.

The stronger test is D3. The source-language concept **does** sit closer to its own English
approximation than to the others' (+0.020, 13 of 16 concepts positive, sign test p = 0.021,
Wilcoxon p = 0.001; instruct +0.024). But it sits *just as close* to the same approximation
expressed in a third language: the English-specific part, after subtracting the language and
length baseline measured on the control words, is **+0.001 [−0.006; +0.009]**, while the concept's
excess towards its third-language approximation is +0.015 (p = 0.004). **The pull is semantic, not
English.**

**What is asymmetric is the reading, not the route.** On the base model, the middle-plane reading
of a *Hungarian* prompt is up to 58% strictly English words (an upper bound: the classifier's
precision on the English class is 75%, so the corrected lower bound is ~44%), while a *Chinese*
prompt reads 60–98% Chinese with the English share never above 18%. On the post-trained model the
Hungarian figure drops to ~26%.

**Post-training: mostly the prompt format, and the evasion disappears rather than the fabrication.**
Base → instruct+chat improves 16 items and degrades 4 (McNemar p = 0.012; item-clustered
permutation p = 0.030). Splitting it: swapping the weights alone is +2 items net (9/7, p = 0.804),
switching to the chat template is +10 (13/3, p = 0.021; clustered p = 0.020). On the Hungarian-only
group the number of confident fabrications is flat across the three variants (23 → 26 → 25); what
disappears is evasion (14 → 10 → 3), which is why the *rate* climbs from 62% to 89%.

## 6. What product decision followed?

See [decision-record.md](decision-record.md). In short: for Hungarian document work, do not
translate the prompt — attach the source. The model is weak on Hungarian-specific facts, and the
instruct variant hides that weakness behind fluent, confident prose.

## 7. What are the limits of the measurement?

- **One model family, one size.** Everything here is Qwen3.5-9B.
- **Small n.** 19/15/20 items per group; the per-cell intervals are wide. The strong claims rest on
  paired tests and on the joint behaviour of the 9 language pairs, not on single cells.
- **Wiki presence is a proxy** for training-corpus presence, not a substitute for it.
- **The second judging pass is also machine judging**, run with the author's own rubric on a corpus
  the author assembled; there was no blind human evaluation.
- **The D2 instrument is weakly sensitive** (positive control: 3/16 and 1/16), so its zero is weak
  evidence, and a distributed, non-lexical English pivot would be invisible to all three probes.
- **The SAE was trained on the base model** and explains ~60–65% of residual variance on these
  short prompts (FVU 0.35 base, 0.37 instruct on question tokens; worst layer +0.047, inside the
  0.05 gate fixed in advance).
- **The tuned lens leaks**: answer depth may only be read off the naive lens, and its
  train/validation split is token-level, so the KL improvement is likely optimistic.
- **Decoding pathologies are present**: truncation grows 43 → 64 → 86 out of 258 across the three
  variants, which biases the measured improvement downward and the fabrication rate upward.

## 8. Which DocAI article belongs to it?

Planned: *"Angolul promptoljak? Megmértük, mi történik közben a modell fejében"* on
[docai.hu/blog](https://docai.hu/blog), plus the full study under `docai.hu/kutatas`. The study is
in Hungarian and includes the complete method chapter; this directory holds the machine-readable
side of the same work.

---

## Directory layout

```text
dataset/                 the corpus and every prompt actually sent (+ the D3 protocol, fixed before the run)
code/                    every script, from corpus building through the measurements to the report generators
reports/                 generated reports, base + raw prompting            (Hungarian)
reports_instruct/        the same for instruct + chat template
reports_instruct_raw/    the same for the control variant
figures/, figures_*/     figures per variant (the reports link to them relatively)
results*/                per-item judgements (scores.csv, d1_scores.csv), judge outputs, generated answers (gen.jsonl)
environment.md           measured environment: hardware, versions, SAE and model checkpoints
```

In `scores.csv` two columns are sources and one is derived: `judge` is the Qwen3.6-35B verdict,
`manual` is the GPT-5.6 Sol verification verdict (empty where that answer was not re-judged), and
`final` is `manual` if non-empty, else `judge`. Group on `final`, not on `judge` — the reports do.
The rule lives in one place and is enforced:

```bash
python3 code/check_scores.py          # exits non-zero if any final != (manual or judge)
python3 code/check_scores.py --fix    # recompute the derived column
```

Not published here: the residual dumps (~1.4 GB per variant) and the SAE activation `.npz` files
(80 MB across the five result directories) — both regenerate from the prompts with `code/run.py`
and `code/run_sae.py`. Every number in the reports is derived from what is in this directory.

The logit-lens *outputs* are published (`lens_rank*.json`, `lens_index*.json`, `lens_vocab*.json`,
`lens_top*.npz` — 3.2 MB for the two main variants), which is what lets Measurement B and the D2
control be re-checked without a GPU.

---

## Reproducing this from a clean clone

Every path in `code/` is relative to this directory, and the two entry points below are all a
reader needs. Analyses need `numpy` and `matplotlib`; nothing else.

```bash
cd experiments/2026-08-26-where-knowledge-lives-hu-en-zh
pip install -r requirements.txt
python3 code/smoke_repro.py
```

The smoke test copies the experiment into a temporary directory and works there, so it never writes
into your checkout. It rebuilds all 290 prompts from `dataset/items.jsonl` and checks them against
the committed files byte for byte, verifies the derived `final` column, then re-runs Measurement A
(all three variants), Measurement B (base + instruct), the D2 control, the token-length table and
the base-vs-instruct comparison — comparing every regenerated report against the committed one.
It exits non-zero on any mismatch, and CI runs it on every push.

What it cannot cover is printed as skipped rather than passed over: `analyze_c.py`, `analyze_d.py`,
`analyze_d3b.py` and `analyze_d3b_x.py` read `results*/sae/`, which is not committed. Those need a
GPU re-run of `code/run_sae.py` — see [environment.md](environment.md) for the machine and the
container, and `code/run_spark.sh` for the invocation.

⛔ Two report generators refuse to write a stub over a full report when their inputs are missing
(`code/analyze_extra.py --allow-missing-sae`, `code/d2_control.py --allow-missing-lens` override it
deliberately). Without that guard, running the analyses in a clone that lacks the SAE or lens
outputs silently replaced published findings — including the D2 null result — with a one-line
placeholder.
