# Eval suite: chat business scenarios

Whether an agent, asked a real business question in Hungarian over a company's own documents,
calls the right tools and reasons correctly over what comes back.

**Suite version:** 1.0 · **Scoring:** tool-call checks + LLM judge against a per-scenario rubric

## What it measures

Each scenario is a question a finance person would actually ask, plus:

- **which tools must be called** (with argument sub-matching), and which must not;
- **an iteration ceiling** — an agent that flails through twenty tool calls has failed even if it
  eventually answers;
- **a written rubric** the judge scores the final answer against, including explicit FAIL
  conditions.

Categories: `tool_calling`, `reasoning`, `summarization`, `no_tool`, `edge`.

The `reasoning` scenarios are the interesting ones. They require several tools, a computation
across them, and a conclusion — cash-flow gap projection, supplier billing anomalies, customer
concentration risk, quarterly VAT position. These are where model differences show up that
single-call tool tests cannot see: in one comparison a 35B and a 122B model both passed the same
number of single-call scenarios, and the larger model reached the same results with **5× fewer
tool calls** on multi-step ones.

## What it does *not* measure

- **Numeric correctness of the underlying data.** The tools return what the database holds; the
  eval scores whether the agent used them correctly.
- **Anything about a specific corpus's contents.** Scenarios are validated against a state of the
  test corpus, recorded in `validity_date`. When the corpus drifts, scenarios go stale — a red
  result may mean the data changed, not the model.

## Scoring

| Check | Rule |
|---|---|
| `tools_must_call` | every listed tool called at least `min_call_count` times; `args_must_contain` matched as a loose sub-match |
| `tools_must_not_call` | calling any of them fails the scenario outright |
| `max_iterations` | exceeding the agent-loop ceiling is a failure, not a timeout |
| `min_judge_score` | LLM judge score 0–5 against `judge_rubric` |

Schema: [../../schemas/chat-scenario.schema.json](../../schemas/chat-scenario.schema.json).

## Judge caveats — read before believing a judge score

The judge is another model. It fails in specific, repeatable ways, and the ones we have hit are:

1. **Reasoning tokens eat the answer.** With thinking enabled and a small output budget, the judge
   spends its tokens reasoning and returns empty content, which scores as a fail. Judges run with
   thinking off and an explicit token budget.
2. **The judge cannot see what it is not shown.** Ours scored answers on the chat text alone while
   part of the response was rendered in a separate canvas surface — so correct answers were marked
   incomplete until the judge input was fixed. If your agent has more than one output channel,
   make sure the judge receives all of them.
3. **Rubrics that only describe success score generously.** Every rubric here names explicit FAIL
   conditions ("general prose without concrete amounts = FAIL", "forecast presented as fact = point
   deduction").
4. **A judge cannot rescue a corpus problem.** In one run, 7 of 16 scenarios failed for **all three
   candidate models** — the test tenant simply had no financial data to answer them with. The judge
   correctly noted that the agent had reported missing data; the rubric expected an answer. Those
   scenarios measured the corpus, not the models.

## Hard rule: evaluations must not act

Scenarios are read-only. This is not a style preference — a scenario set of ours once included a
tool that sends email, and a run **sent a real message to a real external accountant** from a live
tenant.

Two safeguards followed, and both belong in any agent eval harness:

- the runner keeps a list of mutating tools and refuses to expose them, plus a per-run
  `excluded_tools` override;
- before every run, confirm which environment the tool endpoint points at.

Anything that writes, sends, deletes or bills is out of scope for evaluation. If a scenario needs
one, it needs a mock.

## Scenarios

[scenarios/](scenarios/) contains representative examples in the published schema. Tool names are
generic (`invoice_summary`, `outstanding_receivables`, `cashflow_forecast`); substitute your own
catalogue. Questions are in Hungarian because the system under test answers Hungarian users.

| Scenario | Category | What it probes |
|---|---|---|
| [601-cashflow-gap-projection](scenarios/601-cashflow-gap-projection.json) | reasoning | Multi-tool temporal reasoning, weekly breakdown, actionable recommendation, forecast-vs-fact labelling |
| [603-customer-concentration-risk](scenarios/603-customer-concentration-risk.json) | reasoning | Aggregation across partners, ratio computation, risk framing |
| [501-future-date](scenarios/501-future-date.json) | edge | Refusing to invent data for a period that has not happened |

## Known limits

- **Small suites drift.** Around 16 scenarios per run; several were unanswerable on the test
  corpus, which leaves fewer differentiating scenarios than the headline count suggests.
- **Judge variance.** Single judge, single pass. Differences of one scenario are not signal.
- **Tool catalogue coupling.** A scenario expecting a tool that does not exist in the tenant's
  catalogue fails for a reason that has nothing to do with the model. Check the catalogue before
  reading a red result as a regression.

## Used by

- [qwen35-122b-nvfp4-bringup-gb10](../../experiments/2026-05-22-qwen35-122b-nvfp4-bringup-gb10/)
- [qwen36-fp8-vs-nvfp4-quality](../../experiments/2026-07-16-qwen36-fp8-vs-nvfp4-quality/)

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
