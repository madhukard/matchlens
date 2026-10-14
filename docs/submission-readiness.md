# Submission readiness — Inside the Game

Target category: **Best Multi-Agent System**. Review date: 14 October 2026.

## Official requirements

Sources: [event landing page](https://events.microsoft.com/flow/microsoft/plmshackathon/registration/page/landing), [official rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md).

The event page visibly confirms registration. Submission closes 27 October 2026 at 11:59 PM Pacific. The entry needs a public GitHub repository, a public demo video shorter than two minutes on an accepted video platform, English materials or translation, and working free judge access through judging. Registration is not project submission.

## Judge-facing proposition

MatchLens handles the moment a broadcast explanation becomes wrong: a reported goal is corrected. A revision-aware evidence ledger updates the score, retracts the superseded citation and requires all four localized narratives to disclose the correction. Four bounded agents select, challenge, adapt and verify the explanation; the UI changes to a correction timeline. When review fails, viewers receive current statistics instead of a confident stale story.

## Evidence gates

| Criterion (20% each) | Demonstration | Remaining gate |
| --- | --- | --- |
| Technical implementation | Azure managed identities, private Blob, manual worker, public read-only MCP, validated revisions | Six-frame / 24-variant live check passed; final image check recorded in verification |
| Agentic innovation | Four roles, shared evidence, bounded correction, explicit failure mode | Completed: 4/4 multi vs 2/4 baseline; latency/cost limits disclosed |
| Impact and usefulness | Corrected score, inspectable evidence, two audiences and languages | Demonstration and user review; no invented adoption metrics |
| UX and presentation | Adaptive pitch/comparison/timeline, replay, citations, review disclosure | Browser and bridge checks passed; 1:53 captioned demo prepared; publication/native hosts remain |
| Category adherence | Multi-agent workflow and single-agent baseline | Show measurable tradeoffs; do not claim statistical superiority from four cases |

## Release gates still open

- Six-frame live acceptance and 1:53 video inspection passed. Final v0.2.0 deployment and public acceptance checks passed; evidence is recorded in `verification.md`.
- ChatGPT native conversation rendering requires acceptance evidence; the reference harness is insufficient.
- Claude Code 2.1.300 authentication and live MCP acceptance passed: frames 4/5 returned 1–0 then 0–0, revised goal evidence resolved, and superseded evidence was rejected.
- Copilot CLI testing encountered an organization policy blocking third-party MCP servers. Do not bypass that policy or claim that host passed.
- The owner authorized publication and the repository is now public: https://github.com/madhukard/matchlens.
- The 1:53 video is recorded, captioned and visually inspected at `dist/matchlens-demo.mp4`. The owner selected the Dhisana.ai YouTube account. Its existing channel is Madhukar Devaraju (@MadhukarDevaraju); upload awaits the explicit YouTube terms acknowledgement.
- Recommended project branding: **MatchLens by Dhisana**. Official rules sections 3 and 4.10 allow organizations with an authorized individual representative. Use the company’s exact registered legal name in legal entrant fields; confirm it and final portal fields before owner submission.

No award, selection or perfect reliability is promised. This document records unresolved gates, not a certificate of submission readiness.
