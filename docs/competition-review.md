# Competition release review

Review date: 14 October 2026. Target: Best Multi-Agent System. This is an internal assessment, not a judge's score or a submission receipt.

## Official packet and status

[Official rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md) and the [registration page](https://events.microsoft.com/flow/microsoft/plmshackathon/registration/page/landing) were rechecked. The rules file’s latest recorded commit is `d7d8fc3c8befddf3ba530a16ce1092390bae8d1b` (28 September 2026 UTC). The signed-in page confirms registration and directs entrants to an invitation to Innovation Studio for project submission. The actual submission form and any invitation-only notices have not been inspected. Registration is not submission.

Deadline: 27 October 2026, 11:59 PM Pacific. Judge access must remain available through 10 November 2026. The owner must confirm entrant eligibility, organization representation and the final submission terms before release. No portal submission or acceptance of competition terms has occurred.

| Requirement | Evidence | Disposition |
| --- | --- | --- |
| New project after registration opened, rule 4.3 | Repository history begins 14 October 2026 | Met by recorded project history; ownership remains owner attestation |
| Synthetic football data, rule 4.7 | Fictional teams and authored event stream | Met |
| Public repository, rule 4.4 | Public GitHub repository | Met |
| Public video under two minutes, rule 4.4 | Published 1:53 YouTube demonstration | Met |
| Free working judge access, rule 4.8 | Public Azure browser demo and read-only MCP | Verified now; owner must maintain through judging; cold-start delay observed |
| English materials, rule 4.9 | English proposal and burned-in video captions | Met |
| Entrant and representative, rules 3 and 4.10 | Organization permitted; project branding proposed as MatchLens by Dhisana | Legal identity, eligibility and authority require owner confirmation |
| Ownership and third-party rights, rules 4.6 and 4.11 | Project assets and dependency provenance documented | Owner attestation and applicable license compliance remain release checks |
| Required project form, rule 4 | Invitation-only Innovation Studio link requested | Unknown until form inspected |

## Criteria and acceptance evidence

Each criterion carries 20%. No numerical internal score is assigned without pretending to predict the judges.

| Criterion | Answer/evidence | Review finding |
| --- | --- | --- |
| Technological implementation | architecture.md, verification.md, automated tests | Separate Azure identities, read-only serving and correction ledger are concrete. Cold starts remain a usability limit. |
| Agentic design and innovation | live_agents.py, evaluation.md | Roles and rejection paths are explicit. Added model calls and correction attempts are part of the comparison, not controlled away. |
| Real-world impact | submission.md, judge-guide.md | A viewer can inspect and correct an explanation. No user study, adoption or licensed live-feed capability is claimed. |
| User experience and presentation | Browser demo, 1:53 video, judge guide | Immediate browser access is the primary judged surface. Native ChatGPT remains untested and Copilot policy-blocked. |
| Category adherence | Paired evaluation and rejection regression tests | Evidence supports purposeful collaboration on authored cases; it does not establish broad superiority or production reliability. |

## Claims and editorial review

The entry describes the user problem, what was built, an observed failure and what was changed. Generic claims of innovation, guaranteed accuracy, production readiness and universal host compatibility are excluded. The prose does not claim human-only authorship or completed independent human review. Any AI-use question in the actual form must be answered truthfully from the tool/model records and the review actually performed; that form has not yet been inspected.

Company security reports, customer references, staffing promises and unrelated Dhisana production certifications are not used as MatchLens evidence. Pricing, hired delivery teams and procurement insurance are not proposed commitments for this competition prototype.

## Owner release steps

Confirm the legal entrant and representative, inspect the actual Innovation Studio fields and notices, complete the native ChatGPT check if that integration is claimed as demonstrated, review the final text, and submit only with explicit owner authorization. Archive the exact submitted fields, artifact versions and receipt. The live-feed pilot remains deferred; no provider purchase is part of this release.
