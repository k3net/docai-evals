# Fine-tuning vs. a deterministic selector — what a LoRA actually buys

**Date:** 2026-08-14 · **Reproducibility:** R1 (code + public data + full per-item results)
· **Card:** [eval-card.yaml](eval-card.yaml) · **Decision:** [decision-record.md](decision-record.md)
· **Task definition:** [evals/hu-verse-prosody](../../evals/hu-verse-prosody/)

> A LoRA adapter and a best-of-8 reranker both make a model's output more regular.
> Which one earns its cost — and are they buying the same thing at all?

This is the only experiment in this repository that runs on a **public** corpus, so it is also the
only one a reader can re-run end to end and land on our exact numbers. We used that freedom
deliberately: the question is methodological, and the answer transfers to production work where
the data cannot be published.

---

## 1. What was the measurement for?

Style fine-tuning is the default answer whenever a model's output "does not sound right". It is
also expensive to evaluate honestly, because the obvious comparison — fine-tuned model vs. raw
model — is rigged. The fine-tuned model always wins that one.

The question worth answering is whether fine-tuning beats **the best thing you can do without
training**: a good prompt plus a cheap deterministic post-filter. If it does not, the GPU hours
bought nothing.

Hungarian verse is an unusually good testbed for this, because the form is brutally measurable.
Syllable count is the number of vowels — Hungarian orthography has no diphthongs, so this is the
rule itself, not an approximation. A rhyme either holds or it does not. A stanza is four lines or
it is not. No literary judgement is needed, only correct code.

The findings then transfer to the production question this repository exists for: when a document
AI system produces output in the wrong shape, is that a training problem or a scoring problem?

## 2. On what task and dataset?

**Corpus.** The complete poems of Arany János (485 poems, 50,221 lines) and Petőfi Sándor
(852 poems, 30,642 lines) from the Hungarian Electronic Library (MEK). Both are public domain:
Hungarian copyright runs 70 years past the author's death, so protection expired in 1952 and 1919
respectively. The originally intended target style — Romhányi József's rhymed animal verse — is
protected until 2053 and was dropped for that reason.

`code/fetch_corpus.py` downloads the source archives and records their sha256 in
[corpus_manifest.json](corpus_manifest.json), so a third party can verify they got the same bytes.
We re-ran this on 2026-08-17 from a clean directory: both hashes matched, and every number in this
README reproduced bit-for-bit.

**Task.** Three generation task types built from the corpus (`write` a poem to a form
specification, `continue` a given opening, complete a rhyming `couplet`), split at **work level**
so that no poem contributes to both training and evaluation. 50 held-out generation prompts,
scored across the arms — 800 generations in total.

**Ground truth.** None, in the annotation sense. Every metric is deterministic and computed by the
same code on the human corpus and on the model output. That shifts the burden onto the measuring
instrument, which is why it was validated first — see section 4.

## 3. Which models and configurations?

Base model **Qwen3.5-9B**, served through vLLM on a DGX Spark GB10 (`sm_121a`), sampling
temperature 0.8, thinking off. Six arms plus a human reference:

| Arm | Training | Prompt | Selection |
|---|---|---|---|
| **B0** | — | plain instruction | first sample |
| **B1** | — | + 4 Arany poems as examples (15.7× longer) | first sample |
| **B2** | — | as B1 | **best of 8** by `form_score()` |
| **C** | LoRA, 3 epochs | plain instruction | first sample |
| **C2** | LoRA, 3 epochs | plain instruction | **best of 8**, same scorer as B2 |
| **C_ep1** | LoRA, **1 epoch** | plain instruction | first sample |
| **GOLD** | — | — | the original poems, same ruler |

**B2 is the real opponent.** It trains nothing: it samples eight times and keeps the most regular
candidate, scored by the same deterministic prosody code that later grades every arm. Comparing
the LoRA to B0 instead would have produced a flattering and useless result.

**The adapter.** r=32, α=64, dropout 0.05, 36,225,024 trainable parameters — 0.40% of 8.99B —
across **152 modules in all 32 layers**, 63.8 minutes of training.

That module count is the one architectural decision worth copying. Qwen3.5 is a **hybrid**: only
every fourth layer is classic attention (`q/k/v/o_proj`); the other 24 are
`Qwen3_5GatedDeltaNet` linear-attention mixers with a different parameter namespace
(`in_proj_qkv/a/b/z`, `out_proj`). The standard "adapt the attention projections" recipe would
therefore have touched **8 of 32** token-mixing layers and silently skipped three quarters of the
model. This class of mistake does not crash; it just underperforms.

## 4. Which metrics?

Two axes, deliberately kept separate, plus a control.

**Form** — syllable accuracy, stanza structure, rhyme rate, and `rhyme_quality`: the share of
rhyming pairs that are *not* mere inflectional rhyme. In an agglutinative language any two words
carrying the same suffix rhyme automatically, so `rhyme_quality` is the metric a model cannot win
with a grammatical trick.

**Style** — an independent TF-IDF + logistic-regression classifier trained to tell Arany from
Petőfi. On held-out poems it reaches **91.0%** accuracy against a 59.0% majority baseline. It
knows nothing about prosody; it reads vocabulary and phrasing.

**Memorisation** — `extraction_gap`: feed the model the first two lines of a poem and measure how
much it continues correctly, for trained poems *and* for held-out poems. The held-out arm is the
control, and it matters: those poems were never in our training set, but the Toldi and János vitéz
are in every large text corpus, so they are almost certainly in the base model's pretraining. Only
the **gap** is attributable to our fine-tuning.

### The instrument was validated before the model was trained

This was the least interesting work in the experiment and the reason every later number is
believable. Details in [evals/hu-verse-prosody](../../evals/hu-verse-prosody/); in short:

- **Syllable counter against external truth.** The Toldi, Toldi estéje and János vitéz are written
  in Hungarian alexandrines — twelve syllables per line, a literary-historical fact, not our
  assumption. Measured over 4,125 lines: **99.7%** exactly twelve.
- **Rhyme detector against a control group.** Real rhyme positions score 85.4%; the same lines
  re-paired across different stanzas — same author, same vocabulary, no rhyme intent — score
  **10.1%**. A 75-point separation means the detector finds rhyme, not similarity.
- **The same code, two authors, opposite patterns.** Arany's quatrains rhyme on lines 1–2 and 3–4
  (86.0% / 84.8%); Petőfi's rhyme on 2–4 (64.7%). That is couplet rhyme versus the folk half-rhyme
  of Hungarian song — textbook literary history, recovered from measurement with no per-author
  tuning.

## 5. What was the result?

### Form: the LoRA loses to the untrained baseline on every axis

| Metric | B1 (few-shot) | **B2 (few-shot + reranker)** | **C (LoRA)** | C − B2 | GOLD |
|---|---:|---:|---:|---:|---:|
| stanza count correct | 0.567 | **0.700** | 0.573 | **−0.127** | 1.000 |
| stanza size correct | 0.802 | **0.938** | 0.735 | **−0.203** | 0.982 |
| syllable count exact | 0.206 | **0.409** | 0.203 | **−0.207** | 0.800 |
| rhyme rate | 0.114 | **0.236** | 0.177 | **−0.059** | 0.577 |
| **rhyme quality** | 0.093 | **0.203** | 0.139 | **−0.064** | 0.400 |
| invented words *(lower is better)* | 0.019 | **0.013** | 0.044 | **+0.031** | 0.000 |

Sixty-four minutes of training loses to a few dozen lines of scoring code — and produces **three
times as many invented words** doing it.

The reason is not mysterious. The reranker maximises exactly what the table measures: it counts
syllables in eight candidates and keeps the best. A LoRA shifts a *tendency*; it offers no
guarantee about any individual poem.

### Style: the selector cannot buy it at all

| Arm | Attributed to Arany by the classifier |
|---|---:|
| B0 (raw) | 38.7% |
| B1 (+ examples) | 56.4% |
| **B2 (+ reranker)** | **56.0%** |
| **C (LoRA)** | **77.3%** |
| **C2 (LoRA + reranker)** | **92.0%** |

**B1 → B2 moves style by −0.4 points** while improving every form metric. This is not noise, it is
a consequence: a selector that counts syllables and compares line endings has no representation of
whether a text sounds like Arany.

**B2 → C2 is the clean isolation.** Same reranker, same 50 prompts, same `best_of=8`, same seed.
The only difference is the adapter: **56.0% → 92.0%, +36 points attributable to training alone.**

One puzzle worth resolving, because the obvious explanation is wrong. The reranker *does* improve
author recognition on the LoRA branch (77.3% → 92.0%) despite scoring only form. The tempting
reading — "Arany was a formal poet, so better form means more Arany-like" — is **refuted by B2**,
where the identical selector adds nothing. The selector amplifies what is already present in the
candidates; on the LoRA branch all eight candidates are Arany-ish, so picking the most regular one
also surfaces the most characteristic. *A selector amplifies; it does not create.*

### The price: invented words

The style gain is not free, and the interesting part is how nearly we mis-read it:

| | out-of-dictionary rate | truly invented |
|---|---:|---:|
| raw model | 0.021 | 0.015 |
| **LoRA** | **0.067** | **0.044** |
| **Arany János** | **0.079** | **0.000** |

At first glance the LoRA's 6.7% sits reassuringly close to Arany's 7.9% — as if it had learned the
archaic vocabulary. It had not. The spellchecker fails on Arany too, but *his* unknown words are
real old Hungarian. Only a two-stage measure separates the cases: a form absent from both the
dictionary **and** the 73k word forms of the two authors is not archaism, it is invention. On that
measure the LoRA is at 0.044 against Arany's 0.000.

The precise statement: the fine-tuning improves the rhyme rate and **pays for it with invented
words**. The model did not learn to rhyme; it learned that *rhyme matters more than the word*.
The same failure mode shows up as repeated lines — 9–12% of lines for the model, 0.7% for the
human — because a repeated stanza rhymes perfectly with itself and scores well if you do not
measure it separately.

### The validation loss points at the wrong checkpoint

| epoch | 0.5 | **1.0** | 1.5 | 2.0 | 2.5 | 3.0 |
|---|---:|---:|---:|---:|---:|---:|
| eval loss | 2.880 | **2.835** | 2.874 | 2.870 | 2.967 | 2.969 |

By the book, take the 1-epoch checkpoint and discard the rest. We measured both:

| | rhyme rate | syllable exact | repeated lines | author recognition |
|---|---:|---:|---:|---:|
| 1 epoch — the "correct" pick | 0.119 | 0.180 | 0.181 | 68.0% |
| 3 epochs — the "overfitted" one | **0.177** | **0.203** | **0.118** | **77.3%** |

The overfitted adapter is better on **every measured axis**. Next-token loss on held-out Arany
rewards guessing *his next word*; we wanted the model to write *in his manner*. The two move
together for one epoch and then separate. A fifty-task form measurement settled it in six minutes.

### Memorisation: the risk that did not materialise

| | trained poems | held-out poems | **our contribution** |
|---|---:|---:|---:|
| raw model | 1.48 words | 1.38 | +0.10 |
| **LoRA** | 1.24 | 1.19 | **+0.05** |

Zero verbatim spans of eight words or more, in any arm. The fine-tuned model's gap is *smaller*
than the base model's.

This contradicted our expectation ("memorisation arrives before style") and forces a distinction:
**overfitting is not memorisation.** A rising validation loss says the model is getting worse at a
general language task; it does not say the model is storing the text. At this corpus size, with a
0.4% adapter, on this task type, the model picked up the *statistics* of the style, not the words.

What this does **not** establish: that fine-tuning on copyrighted text would be safe. The
measurement is valid for what it measured.

### A free-prompt demonstration

Added after the measurement closed, for the article: what happens on a prompt nobody tuned for?

> *„Írj egy rövid, 4 soros, szépen rímelő verset a dokumentum kezelésről."*
> (Write a short, four-line, nicely rhyming poem about document management.)

No author named, no form specification. Both arms got the identical prompt, generated eight
candidates, and were selected by the identical reranker — the only difference is the adapter. Six
seeds on the LoRA arm, five on the raw arm; all 11 runs are in `generations/demo/` with every
candidate, its score and its rhyme analysis.

The illustrative pair (seed 101) landed on **exactly the same reranker score, 2.667 of 3**:

| | raw + reranker | LoRA + reranker |
|---|---|---|
| syllables | 11 · 11 · 11 · 11 | 10 · 9 · 9 · 9 |
| rhyming adjacent pairs | 2 of 3 | 2 of 3 |
| invented words | **0** | **2** (`hiess`, `fájtos`) |
| register | "the digital century shows a new way" | a clerk whose throat aches from the paperwork |

The form ruler cannot separate them — they tie. What differs is the thing it does not measure.

Two findings worth keeping from the demo:

- **The selector has no notion of topic either.** On one seed the highest-scoring LoRA candidate
  was a perfectly formed quatrain about a razor, with no connection to document management. Three
  candidates tied at the top and generation order broke the tie; a topical one was among them.
  Same blind spot as with style, now on content.
- **One line contains both vocabulary cases at once.** `Kerűlni az időt, amit elpocsótlam` —
  *Kerűlni* is absent from the spellchecker but **present in Arany's text** (his spelling): real
  archaism, correctly learned. *elpocsótlam* is in neither: an invented form. And the rhyme it was
  presumably reaching for scores 0.400, below the 0.6 threshold — the model invented a word and did
  not even get a rhyme for it.

The author classifier was deliberately **not** applied to these four-line pieces: it was trained on
7,195 blocks whose median is 8 lines and 46 words, and only 0.1% of that training material is as
short as these. The 91.0% accuracy does not transfer to this length.

## 6. What product decision followed?

Full record in [decision-record.md](decision-record.md). In short:

1. **Output shape is a scoring problem, not a training problem.** Where DocAI needs structurally
   regular output, the first attempt is a deterministic scorer over N samples — cheaper, more
   reliable, fewer side effects, and it never invents vocabulary.
2. **Never publish a fine-tuning result without a training-free opponent.** This is now a
   standing requirement for our own evaluations, and it has already paid for itself once: on a
   later classification measurement a plain TF-IDF baseline turned out to match a
   7,296-dimensional embedding pipeline on the classes it covered.
3. **Do not select a checkpoint on validation loss when the loss is not the task.** Measure the
   task on a few dozen items instead. It costs minutes.
4. **Adapt the mixers the model actually has.** On a hybrid architecture, enumerate the modules
   before copying a target-set recipe from a paper.

## 7. Limits of this measurement

Ten limitations are listed in the [eval card](eval-card.yaml); the ones that constrain the
conclusion most:

- **One author, one model, one seed.** Everything here is Arany János on Qwen3.5-9B from a single
  run. The corpus, the ruler and the pipeline are ready for Petőfi and his GOLD row is measured,
  but that training run did not happen.
- **The reranker arms are smaller.** B2 and C2 score 50 generations, the others 150, because
  best-of-8 costs eight times as much. Order-of-magnitude differences survive that; point
  estimates are noisier.
- **The reranker optimises the reported form metrics.** That is precisely why it belongs in the
  comparison as the baseline, but it means the form column is a selector benchmark rather than an
  independent verdict.
- **Even the best arm is not good.** C2 reaches 0.471 syllable accuracy against Arany's 0.800. It
  is the best of the arms, not "good" — and the ceiling is human, not 1.0.
- **A known gap in the ruler, left in place.** The inflectional-rhyme list is a deterministic set
  of suffixes, not a morphological analyser, and accusative plurals (`-okat`/`-eket`) are missing —
  so `virágokat / dolgokat` counts as rich rhyme when it is not. This inflates `rhyme_quality` for
  **every** arm including GOLD, in the same direction. We froze the list when the measurement
  closed rather than silently re-scoring published numbers; the self-test in
  `scripts/hu_prosody.py` asserts the gap so it cannot be forgotten.

## 8. The hardware notes worth keeping

Three findings from the GB10, all of which cost real time:

**Gradient checkpointing is a requirement, not a precaution.** Without it the process did not die
with an out-of-memory error — **the whole node rebooted**. On unified memory there is no separate
pool to fall back on: if the GPU allocation eats system RAM, no surviving process handles it.

**We discarded a 2.6× speed-up on purpose.** Sequence packing would have cut an epoch from 36 to
14 minutes on the 2B trial run, but the library only guarantees example separation with certain
attention implementations, which are not available on `sm_121a`. Without separation the model sees
the previous poem while learning the current one — the training signal would be false, and it
would corrupt precisely the memorisation measurement that was the point. *2.6× faster is not a
bargain if it invalidates the measurement.* (Related trap: the library's own
`train_samples_per_second` reads **backwards** under packing — 0.613 vs 0.575, as if packing were
slower — because a "sample" there is a packed bundle, not a training example.)

**Compiling is not running.** `causal-conv1d` builds for this architecture, imports cleanly, and
makes the warning disappear — then the training **crashes at the first step** (exit 139). Model
loading still succeeds. The measurement was made with the slower working configuration.

## 9. The article

The story, in Hungarian: **[Versel nekünk az AI — de tud-e Arany
Jánosul?](https://docai.hu/blog/versel-nekunk-az-ai)**

## Files in this directory

| Path | What it is |
|---|---|
| `eval-card.yaml` | The machine-readable summary: arms, metrics, results, limitations |
| `decision-record.md` | What we changed as a result, and what would reopen the question |
| `code/` | The complete pipeline: fetch → corpus → annotate → dataset → train → generate → evaluate |
| `generations/` | Every generated poem, per arm, as JSONL — 800 generations plus extraction probes |
| `generations/demo/` | The free-prompt demonstration: 11 runs × 8 candidates, with scores and rhyme analysis |
| `results/` | Per-item metric rows and the author-classifier output |
| `reports/` | The generated measurement reports (Hungarian — these are the raw tool output) |
| `figures/` | Form comparison, memorisation control, training curve (Hungarian labels — they were drawn for the article) |
| `training/` | `run.json` (hyperparameters, timing) and the trainer state with the loss curve |
| `corpus_manifest.json` | Source URLs and sha256 of the MEK archives used |

### Re-running it

The corpus is not committed — it is 18 MB and MEK is the authoritative source — but it is fetched
with hash verification, so nothing is lost. Everything except the training step runs on CPU.

```bash
cd experiments/2026-08-14-lora-vs-reranker-hu-verse

python3 ../../scripts/hu_prosody.py     # self-test of the ruler
python3 code/fetch_corpus.py            # download from MEK, verify sha256
python3 code/build_corpus.py            # HTML -> poem-level JSON
python3 code/validate_prosody.py        # the instrument validation of section 4
python3 code/annotate_corpus.py         # prosody annotation
python3 code/build_dataset.py           # SFT split, work-level
python3 code/build_evalset.py           # the 50 evaluation prompts

# Scoring the published generations — no GPU, no model:
python3 code/evaluate.py --generations generations
python3 code/author_clf.py --score --generations generations
```

The last two commands reproduce every table in section 5. Training (`code/train_lora.py`) and
generation (`code/generate.py`) need a GPU; `--grad-ckpt 1` is mandatory — see section 8.
