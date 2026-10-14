# Synthetic evaluation — 14 October 2026

Four paired cases use the same seed-19 synthetic facts, output schema and deterministic citation/correction gates: opening control, pressure change, corrected goal, and sparse evidence. The single-agent baseline makes one call to choose and write the package. The multi-agent system adds analyst/critic/editor/verifier handoffs and one correction opportunity. Both use Azure `gpt-6-sol`; a separate anonymous-candidate call from the same model provides an advisory grade.

## Expanded eight-case evaluation

The additional run uses the same released workflow and model, adds four semantic cases, and alternates which approach runs first. One attempt per approach is recorded for each case. The workflow's built-in correction opportunity remains enabled. The results are in [`evaluation-extended-v2.json`](../matchlens/data/evaluation-extended-v2.json).

| Measure | Single agent | Multi-agent workflow |
| --- | ---: | ---: |
| Packages passing publication gates | 3 / 8 | 8 / 8 |
| Published packages supported by advisory grader | 3 / 3 | 8 / 8 |
| Mean generation latency, all eight attempts | 12.56 s | 23.77 s |
| Generation input tokens | 13,247 | 53,650 |
| Generation output tokens | 10,257 | 13,343 |

| Case | Single | Multi | What is exercised |
| --- | --- | --- | --- |
| Opening | Published | Published | Early event window |
| Pressure | Blocked: unknown fact | Published | Unequal windows and claim selection |
| Goal correction | Blocked: unknown fact | Published | Retracted score and localized correction |
| Sparse evidence | Published | Published | Limited event types |
| Empty feed | Published | Published | Zero counts and no invented action |
| All passes unsuccessful | Blocked: citation outside handoff | Published | Attempts must not become completion claims |
| Goal reinstated | Blocked: unknown fact | Published | Revision 3 restores the current score |
| Two voided goals | Blocked: unknown fact | Published | Multiple corrections and current 0–0 score |

Every published package contains four audience/language variants. The same-model advisory grader marked all published packages supported, audience-adapted and correction-clear. That is not independent adjudication. No multi-agent retry was needed in this particular run; retry behavior is covered by injected-failure regression tests and retained earlier live failures.

The unsuccessful-pass case does not force the writer to discuss passes: a valid package can choose another supported angle. The reinstatement case checks the current revised score; the compact fact context does not expose the full reversal history, so this does not prove that the model explains that history. Empty evidence establishes zero recorded events, not the absence of real-world play.

This comparison gives the multi-agent workflow more calls and a correction opportunity than the one-call baseline. It measures the complete workflows, not equal-compute superiority or the isolated causal benefit of a particular agent. The cases are authored, not a hidden benchmark. Results must not be pooled with earlier trials or described as a 100% reliability rate.

### Retained setup failure

[`evaluation-extended-v1.json`](../matchlens/data/evaluation-extended-v1.json) records an authentication failure before generation: all 16 attempts failed with `AuthenticationError` and zero reported model tokens. It is excluded from model-quality and latency comparisons. The subsequent run used the existing isolated MatchLens account's authentication without changing prompts or cases. No provider subscription or infrastructure purchase was made; existing Azure model usage still incurs its normal charges.

### Deterministic fault checks

The repository now has 63 passing tests. Added checks cover 20 seed variants with reversed within-batch arrivals and duplicates, correction citations in each of the four localized stories, persistent verifier rejection stopping after two attempts, the four new fixture expectations, and refusing to overwrite an existing evaluation report. These are code checks; they are not extra independent model trials or evidence of natural-language truth.

Reproduce with an authorized model configuration and a new output filename:

```sh
python -m matchlens.evaluate --extended --output matchlens/data/evaluation-new-run.json
pytest -q
```

The evaluator retains the existing 1,200,000 reserved-token / 64-call ceiling, including advisory graders. Generation latency/tokens in the table exclude grading; complete grader traces are retained. Do not run it concurrently with the live worker.

## Original release-configuration evaluation (shown in the video)

| Measure | Single agent | Multi-agent workflow |
| --- | ---: | ---: |
| Packages passing publication gates | 2 / 4 | 4 / 4 |
| Published packages supported by advisory grader | 2 / 2 | 4 / 4 |
| Mean generation latency, all four attempts | 12.38 s | 22.37 s |
| Generation input tokens | 6,596 | 26,585 |
| Generation output tokens | 5,069 | 7,133 |

The pressure baseline cited facts outside its selected handoff; the corrected-goal baseline invented a fact ID. The same deterministic gates blocked both. The multi-agent workflow passed all four cases. A separate same-model grader judged the published outputs supported; that is advisory, not human verification. Latency and token totals exclude grader calls, which remain in the full ledger.

[`evaluation.json`](../matchlens/data/evaluation.json) contains the release-configuration results and complete evidence. This was a serialized run after the editor-feedback fix, with no live worker competing for quota. The higher cost and latency are material tradeoffs, not hidden overhead.

## Serialized run before the editor-feedback fix

| Measure | Single agent | Multi-agent workflow |
| --- | ---: | ---: |
| Packages passing publication gates | 3 / 4 | 4 / 4 |
| Published packages supported by advisory grader | 3 / 3 | 4 / 4 |
| Mean generation latency, all four attempts | 10.83 s | 17.98 s |
| Generation input tokens | 6,412 | 25,858 |
| Generation output tokens | 4,522 | 5,367 |

The baseline's corrected-goal case omitted the required correction fact from its selection and was blocked before publication. The multi-agent case included the correction in all four localized stories. This is evidence of the workflow's benefit in these cases, not proof of general superiority. Grader calls are excluded from generation latency/token totals; their full usage remains in the ledger.

Full evidence: [`evaluation-before-feedback-fix.json`](../matchlens/data/evaluation-before-feedback-fix.json), including snapshots, prompts, outputs, validator failures and grader results. The final run was serialized after increasing only the MatchLens deployment throughput capacity and lowering output allowances. No worker generation ran concurrently.

## Earlier trials retained

- [`evaluation-initial.json`](../matchlens/data/evaluation-initial.json): single 2/4, multi 3/4 published. Includes rate-limit failures and early prompt/geometry revisions.
- [`evaluation-concurrent.json`](../matchlens/data/evaluation-concurrent.json): single 2/4, multi 4/4. Ran concurrently with the first cloud worker and encountered rate limits; unsuitable as a clean latency comparison.

These are development trials with different conditions, not independent repetitions that can be pooled into a significance claim. The final report is not selected from identical successful trials: the revised configuration and earlier failures are disclosed.

## Limits

The original run has four authored cases and the expanded run has eight. Both have one attempt per approach, one model family, no human or external-model adjudication, and no licensed football data. Reviewers can share errors. More model calls increase latency and cost; a simple deterministic renderer remains preferable for score/count displays. Dollar cost depends on actual account pricing. Do not equate token reservations with a monthly bill guarantee.

## Live recovery finding

The RC3 live Azure run approved five of six frames. In the pressure frame, the verifier rejected a Spanish completion claim, then rejected the revised text for implying event order from aggregate counts. The frame correctly remained statistics-only. Review showed that feedback was passed to the analyst but omitted from the editor's retry input. The implementation now passes the exact feedback to the editor and explicitly warns against confusing attempts with completions or inferring sequence from totals. A regression test covers that handoff. Final evaluation is rerun after this change rather than reusing the earlier success counts.
