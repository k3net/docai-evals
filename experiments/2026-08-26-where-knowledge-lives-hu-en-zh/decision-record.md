# Decision record — attach the source, do not translate the prompt

**Date:** 2026-08-26 · **Status:** in force ·
**Experiment:** [where-knowledge-lives-hu-en-zh](README.md)

## Decision

For Hungarian document work we do **not** translate prompts into English, and we do not treat
prompt language as a quality lever. Where the model is weak — Hungarian-specific subject matter —
the answer is **retrieval and source attribution**, not a different prompt language and not a
bigger model.

Second, and narrower: when we compare a base checkpoint with a post-trained one, the comparison
must hold the **prompt format** constant, or report the split.

## The rule that produced it

Fixed before the mechanistic run ([dataset/d3b-protokoll.md](dataset/d3b-protokoll.md)): positive
evidence for a lexical English pivot requires a sign test below 0.05 **and** an effect of at least
+0.02 Jaccard, measured at layer 10 over the question tokens. Absence of positive evidence would be
reported as absence of evidence, not as proof of absence.

## What the measurement said

| Question | Outcome |
|---|---|
| Does English prompting help when the knowledge is not English-sourced? | No reliable advantage was detectable. Chinese-only knowledge: 63% in Chinese, 53% in English, 42% in Hungarian. Hungarian-only: 7% in Hungarian, 13% in English, 20% in Chinese. English is not the best language in either main round — but it *is* in the raw-prompt control round (ZH 68% English vs 58% Chinese; HU 20% vs 13%), so this is "no detectable average gain", not "English never wins". |
| Does the model reach the concept through an English word? | No positive evidence. The concept pulls towards its own English approximation (+0.020, p = 0.021), but equally towards the same approximation in a third language; the English-specific part is +0.001 [−0.006; +0.009]. |
| Is there a shared representation at all? | Yes, and it is thin: all 9 cross-language comparisons significant at layer 16, the hump shape confirmed in 6 of 9 cells, but the absolute overlap is 0.19 against a 0.13 random baseline. |
| Does the model signal what it does not know? | No, and post-training makes it worse. On Hungarian-only items the number of confident fabrications is flat (23 → 26 → 25); what disappears is evasion (14 → 10 → 3). |

## What we do differently

**1. Hungarian prompts stay Hungarian.** No translation layer in front of Hungarian document
pipelines. The measurement gives no reason to expect a gain, and a translation step costs latency
and adds a second place for meaning to be lost.

**2. Weak Hungarian knowledge is a retrieval problem.** The 7% cell is the strongest argument for
the product: the model does not reliably *produce* Hungarian-specific facts, and the instruct
variant answers confidently anyway. Whether those facts are absent from the weights is a question
this measurement cannot settle — a failure to generate is not a demonstration of absence, and the
product decision does not depend on which of the two it is. Every Hungarian factual claim in a customer-facing answer needs a document
behind it and a citation in front of it.

**3. Fluency is not a confidence signal.** The chat template does not create more fabrication, it
removes the hedging that used to mark uncertainty. Anything that reads "the model sounded sure"
must be treated as no signal at all in review UIs and acceptance criteria.

**4. Model comparisons hold the prompt format constant.** Two thirds of the apparent base →
instruct gain here was the chat template, not the weights. Any future checkpoint comparison in this
repository either fixes the format or publishes the split.

## What would reopen it

- **A second model family** on the same frozen corpus. Everything here is Qwen3.5-9B; the Llama
  literature agrees in direction, but that is not a measurement of our stack.
- **A paired Hungarian vs. English instruction experiment on real documents** (same document, same
  context, KIE and RAG, field-level F1 and hallucination). The conclusion above is measured on
  short encyclopaedic questions only, and this is the experiment that would extend or overturn it
  for the production case.
- **A causal test.** The shared middle-layer features are correlational evidence. A steering or
  ablation experiment on those features would decide whether they carry the concept — and, if they
  do, whether a Hungarian answer can be improved from knowledge acquired in Chinese.
- **Any evidence of a distributed, non-lexical pivot.** All three probes here are lexical or
  feature-level; a pivot that never surfaces as a word would be invisible to them.
