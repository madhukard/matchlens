# MatchLens — the story changes when the evidence changes

**Category: Best Multi-Agent System**

A goal is reported. Seconds later, the event feed corrects it. The scoreboard is easy to fix; the AI story, translated summary and supporting citations can remain confidently wrong.

MatchLens makes that correction a first-class part of match intelligence. It reconciles versioned synthetic football events, computes the score and counts, and hands one evidence snapshot to four specialist agents built with the OpenAI Agents SDK. The match analyst selects the story and useful view. An evidence critic challenges its interpretation. An audience editor writes for fans and analysts in English and Spanish. A broadcast verifier checks every version before publication.

When the goal is voided, its old citation stops resolving, the score returns to 0–0, and every localized story must disclose the correction. The interface changes to a timeline so viewers can inspect the revised event. Review feedback can trigger one correction attempt. If the explanation still fails review, MatchLens shows current statistics and withholds the narrative.

## Experience

The match room combines an interactive pitch, event replay, count comparisons, supporting evidence and visible review history. Its view adapts to the approved explanation while keeping user controls available. The same read-only MCP server provides text and structured results to agent clients; MCP Apps carries the interactive view to compatible hosts. A standalone browser view gives judges immediate access without a model key or paid generation.

Try moment 5, “Goal reported,” then moment 6, “Goal corrected.” Select “Show me why” to inspect the revised goal. Change the audience and language to see how the presentation changes while the evidence stays fixed.

## Azure implementation

A manual Azure Container Apps job uses managed identity to call a dedicated Azure OpenAI deployment. It publishes a private Blob run ledger containing facts, agent handoffs, rejected drafts, latency and usage. A separate serving identity has read-only storage access and no inference role. An exclusive lease prevents concurrent publishers, while call, token and timeout limits bound each generation run. The public application cannot start paid generation.

The repository and Azure resource group are isolated from existing Dhisana services. All teams and events are fictional; no licensed match footage, tracking or customer data is used.

## Evidence and tradeoffs

The repository includes a paired single-agent/multi-agent evaluation, full synthetic run ledgers, automated regression tests and reproducible client checks. Earlier unsuccessful trials are retained and explained. In live testing, the verifier caught a Spanish draft that confused pass attempts with completions; publication was withheld. That exposed and led to a regression-tested fix in how reviewer feedback reached the editor.

The extra review calls cost tokens and latency. The small, same-model-graded evaluation is exploratory rather than proof of general superiority. Deterministic code remains the right tool for score arithmetic; agents add value in selecting, challenging and adapting explanations.

## Current scope

The demonstration uses six accelerated authored event batches and waits for review between batches. It is not a subsecond real-world broadcast feed. Model reviewers can share errors, and evidence links do not guarantee every sentence is correct. Actual host acceptance and account-policy restrictions are listed in the verification document; MCP protocol support alone is not presented as proof that every ChatGPT, Claude or Copilot account is connected.
