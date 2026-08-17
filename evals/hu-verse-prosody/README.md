# Eval suite: Hungarian verse prosody

A deterministic ruler for Hungarian verse form — syllable count, rhyme, rhyme scheme — plus a
style proxy that is independent of all three.

**Code:** [`scripts/hu_prosody.py`](../../scripts/hu_prosody.py) (standard library only, with a
self-test) · **Validation:** `code/validate_prosody.py` in
[the experiment](../../experiments/2026-08-14-lora-vs-reranker-hu-verse/)

Not a single line of this suite calls a model. The same code annotates the human corpus and scores
the generated output, which is the point: form is **measured**, never asked of an LLM.

---

## Why Hungarian verse is measurable

Three properties make this task unusually free of judgement calls:

- **Syllables are countable exactly.** Every Hungarian syllable has exactly one vowel as its
  nucleus, and the orthography admits no diphthongs. Counting vowels is therefore not an
  approximation of the rule — it *is* the rule. (`au`/`eu` in loanwords are two syllables:
  *a-u-tó* = 3, which is correct.)
- **Rhyme is a phoneme comparison**, not a spelling comparison, and the phoneme inventory is
  small and regular.
- **Stanza structure is literally countable.**

What remains hard is that Hungarian rhyme is predominantly **assonance**: the vowels match and the
consonants are treated loosely. *"Kezemben / verekednem"* is not a defect in Petőfi, it is the norm
of folk-register rhyme. Any detector strict enough to demand exact consonant codas throws away most
real Hungarian rhyme. That trade-off is measured below rather than assumed.

## What it measures

| Metric | Definition |
|---|---|
| `syllable_exact` | Share of lines whose syllable count matches the requested value exactly |
| `syllable_pm1` | The same within ±1 syllable |
| `stanza_count_ok` | Share of poems with the requested number of stanzas |
| `stanza_size_ok` | Share of stanzas with the requested number of lines |
| `rhyme_rate` | Share of line pairs scoring ≥ 0.6 on the rhyme scorer |
| **`rhyme_quality`** | `rhyme_rate` minus inflectional rhyme — the share that is not won by grammar |
| `rhyme_scheme_ok` | Share of stanzas whose detected scheme matches the requested one (AABB, ABAB, …) |
| `repeated_line_rate` | Share of repeated lines — a repeated stanza rhymes perfectly with itself |
| `out_of_dictionary_rate` | Word forms unknown to the Hungarian spellchecker |
| **`invented_word_rate`** | Unknown to the spellchecker **and** absent from the authors' 73k word forms |
| `distinct_2` | Distinct bigram ratio, as a crude diversity check |

Two of these exist because of a specific way to cheat, and both were designed before any model ran.

**`rhyme_quality`.** Hungarian is agglutinative, so any two words carrying the same suffix rhyme
automatically — *"virágokat / dolgokat"*. This is a legitimate device, not a trick: **37.7% of
Arany's own rhyming pairs** are inflectional. But it is also the cheapest possible way for a
generator to raise `rhyme_rate`, so the share that survives the exclusion is reported separately.

**`invented_word_rate`.** A spellchecker alone is useless here: it fails on **7.9%** of Arany's own
words, because his unknown words are real archaic Hungarian. A single-stage measure would read a
model's invented vocabulary as successfully learned archaism. The two-stage rule — unknown to the
dictionary *and* unseen in the 73k word forms of the corpus authors — separates archaism from
invention. Arany scores 0.000 on it by construction of the reference set; the interesting number is
what a model scores.

## Style, measured independently of form

Form and style are different axes, and a form ruler cannot see style. The suite therefore includes
a proxy that shares no code and no assumptions with the prosody module:

A **TF-IDF (word 1–2-gram + character 3–5-gram) + logistic regression** classifier trained to tell
Arany from Petőfi. It reads vocabulary and phrasing; it knows nothing about syllables or rhyme.

| | value |
|---|---:|
| holdout accuracy | **91.0%** |
| majority baseline | 59.0% |
| Arany F1 | 0.888 |
| Petőfi F1 | 0.924 |

Trained on 7,195 text blocks from the training split, validated on 432 held-out blocks. Applied to
generated text, `author_clf_acc` is the share attributed to the target author.

The suite declares its own kill-switch: **below 75% holdout accuracy the classifier is too weak to
support any statement about generated style**, and the metric must not be interpreted. The report
prints that warning automatically.

## Validating the ruler — the part that must come first

A measuring instrument that has not been measured is an opinion. Three independent checks, all run
before any model was trained.

### A — Syllable counter against external truth

The Toldi, Toldi estéje and János vitéz are written in Hungarian alexandrines: twelve syllables per
line. This is literary-historical fact, established independently of us, which makes it usable as
ground truth.

| Work set | expected | lines | exact match | within ±1 | median |
|---|---:|---:|---:|---:|---:|
| Hungarian alexandrines (3 works) | 12 | **4,125** | **99.7%** | 99.8% | 12 |

Distribution over the whole corpus (80,193 lines) for context: 12 syllables 38.3%, 8 → 16.9%,
10 → 13.0%, 6 → 6.2%, 11 → 5.5%, 9 → 5.4%. Median 11, mean 10.2.

### B — Rhyme detector against a control group

The design is the placebo arm of a drug trial. Take the real rhyme positions — for Arany, lines 1–2
and 3–4 of a quatrain — and take **the same lines re-paired across different stanzas**. Same
author, same vocabulary, same period, same everything except the intent to rhyme.

| Scorer variant | threshold | Arany (1–2, 3–4) | Petőfi (2–4) | **control** | separation |
|---|---:|---:|---:|---:|---:|
| **v1 additive, coda optional** *(in use)* | 0.6 | **85.4%** | 64.7% | **10.1%** | **+64.9** |
| v1 additive, coda optional | 0.8 | 77.7% | 50.5% | 4.2% | +59.9 |
| v2 — coda mandatory | 0.6 | 79.2% | 57.1% | 5.7% | +62.5 |
| v2 — coda mandatory | 0.8 | 77.7% | 50.5% | 4.2% | +59.9 |
| v3 — vowels only | 0.6 | 87.4% | 72.4% | 21.1% | +58.8 |
| v3 — vowels only | 0.8 | 75.9% | 40.9% | 6.0% | +52.4 |

*(Separation = mean of the two authors' real-position rates minus the control rate. On Arany alone
the gap at the chosen setting is 85.4% − 10.1% = **75.3 points**.)*

v1 at 0.6 maximises the separation, so that is what runs. **Its price is nameable:** two matching
vowels can substitute for a missing coda match, so the pair *"isten / kell"* scores 0.4 — below
the threshold, but closer than it deserves. v2 would tighten that, at the cost of losing Petőfi's
genuine *"svábság / adósságát"*. The measurement says we would lose more than we gain.

Threshold choice, on the real-vs-control separation:

| threshold | real rhyme positions | control | separation |
|---:|---:|---:|---:|
| 0.4 | 98.4% | 29.5% | +68.9 |
| **0.6** | **93.5%** | **10.0%** | **+83.5** |
| 0.8 | 81.3% | 3.9% | +77.4 |
| 1.0 | 58.6% | 1.1% | +57.5 |

Both 0.6 (assonance) and 0.8 (exact rhyme) are reported in every experiment, because a permissive
threshold alone could flatter a result.

### C — The same code, two authors, opposite patterns

The strongest check, because nothing in it was tuned per author. Which line pair rhymes in a
quatrain:

| Author | quatrains | 1–2 | 1–3 | 1–4 | 2–3 | 2–4 | 3–4 | control |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Arany János | 3,481 | **86.0%** | 14.4% | 11.5% | 10.5% | 21.0% | **84.8%** | 10.9% |
| Petőfi Sándor | 3,350 | 35.6% | 15.1% | 10.9% | 10.5% | **64.7%** | 34.9% | 9.9% |

Arany rhymes on 1–2 and 3–4: **couplet rhyme**. Petőfi on 2–4: the **folk half-rhyme**, the base
form of Hungarian song. Same code, same threshold, opposite patterns — textbook literary history,
recovered from measurement rather than assumed.

Resulting scheme distribution:

| Author | threshold | `AABB` | `ABAB` | `ABCB` | `AABA` | `ABCD` | `AAAA` | other |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Arany | 0.6 | **72.1%** | 4.4% | 5.3% | 2.0% | 1.0% | 10.0% | 5.2% |
| Arany | 0.8 | 63.4% | 3.4% | 5.7% | 1.4% | 3.1% | 5.4% | 17.6% |
| Petőfi | 0.6 | 23.1% | 8.3% | **42.2%** | 4.4% | 4.4% | 5.7% | 11.9% |
| Petőfi | 0.8 | 18.5% | 5.1% | **40.7%** | 1.3% | 17.2% | 2.1% | 15.1% |

`ABCB` is the half-rhyme, not a detection failure. `ABCD` means no rhyme was found at all, which is
where errors accumulate — so that bucket is the one reviewed by hand.

When an instrument reproduces something known independently, you can start trusting it where the
answer is not known in advance. That is the entire argument for spending two days on this before
training anything.

## What it does *not* measure

- **Quality.** Nothing here says whether a poem is good. A perfectly regular, perfectly rhymed,
  utterly dead quatrain scores well.
- **Meaning, imagery, coherence.** Not touched.
- **Metre.** Only syllable *counts*, not stress patterns or quantitative feet. Hungarian verse has
  both traditions; only the syllabic one is covered.
- **Whether the style proxy tracks style in general.** It separates two 19th-century Hungarian
  poets. Transfer to other authors, periods or genres is unmeasured.
- **Anything outside Hungarian.** The vowel set, digraphs, suffix list and assonance assumptions
  are language-specific by design.

## Corpus

Public-domain Hungarian verse from the Hungarian Electronic Library (MEK):

| Author | died | poems | lines | stanzas | source |
|---|---:|---:|---:|---:|---|
| Arany János | 1882 | 485 | 50,221 | 7,933 | MEK-00597 |
| Petőfi Sándor | 1849 | 852 | 30,642 | 5,217 | MEK-01006 |

Hungarian copyright expires 70 years after the author's death, so protection ended in 1952 and
1919. Source URLs and the sha256 of each archive are recorded in the experiment's
`corpus_manifest.json`; the fetch script verifies them, so a third party gets a bit-identical
corpus. **This is the only public corpus in this repository** — every other eval suite here runs on
customer documents that cannot be published.

Line recovery is reported as a guard against silent text loss: 92.3% for Arany, 89.0% for Petőfi
against a `<br>`+`<p>` upper bound of the source HTML. The remainder is navigation and
table-of-contents markup. The metric exists so that a parser dropping whole poems would be visible.

## Known limits

- **The inflectional-rhyme list is not a morphological analyser.** `SUFFIXES` in `hu_prosody.py` is
  a deterministic, hand-ordered list of common Hungarian endings. **Accusative plurals
  (`-okat`/`-eket`/`-akat`) are missing**, so *"virágokat / dolgokat"* — the textbook example of
  inflectional rhyme — is counted as rich rhyme. The direction of the bias is known and uniform:
  `rhyme_quality` is **overstated for every arm, including the human reference**. The list was
  frozen when the first experiment closed rather than silently re-scoring published figures; the
  module's self-test asserts the gap so it cannot be forgotten.
- **Lines containing digits are excluded from syllable checks.** "1848" has no defined syllable
  count without knowing how it is read aloud. `has_digits()` flags them.
- **Assonance is a threshold, not a fact.** 0.6 is chosen by maximum separation from a control
  group, which is defensible but not unique. Both thresholds are always reported.
- **The style proxy is binary.** It answers "Arany or Petőfi", not "how Arany-like". A text in
  neither style is still forced into one of the two.
- **`repeated_line_rate` catches only exact repeats.** A near-repeat with one word changed passes.

## Used by

- [lora-vs-reranker-hu-verse](../../experiments/2026-08-14-lora-vs-reranker-hu-verse/) — does a
  LoRA beat a deterministic best-of-8 selector, and are they buying the same thing?
