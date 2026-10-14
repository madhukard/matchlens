# MatchLens — the story changes when the evidence changes

**Category: Best Multi-Agent System**

[Demo video (1:53)](https://www.youtube.com/watch?v=qdtIEEIp8bE) · [Public source](https://github.com/madhukard/matchlens) · [Working application](https://matchlens-dev.redforest-787f42f7.westus2.azurecontainerapps.io)

A goal is reported. Seconds later, the event feed corrects it. The scoreboard is easy to fix; the AI story, translated summary and supporting citations can remain confidently wrong.

MatchLens keeps the explanation in step with the corrected score. It records revisions to synthetic match events, calculates the statistics, and gives four specialist agents the same evidence snapshot through the OpenAI Agents SDK. The match analyst selects the story and useful view. An evidence critic challenges its interpretation. An audience editor writes for fans and analysts in English and Spanish. A broadcast verifier checks the four audience and language versions before they appear.

When the goal is voided, its old citation stops resolving, the score returns to 0–0, and every localized story must disclose the correction. The interface changes to a timeline so viewers can inspect the revised event. Review feedback can trigger one correction attempt. If the explanation still fails review, MatchLens shows current statistics and withholds the narrative.

## Experience

A casual fan can read a short update; an analyst can inspect the counts behind it. Both can replay events on the pitch, compare time windows and open the supporting evidence. The view follows the explanation, and the viewer can switch it at any point. The same read-only MCP server provides text and structured results to agent clients; MCP Apps carries the interactive view to compatible hosts. A standalone browser view gives judges immediate access without a model key or paid generation.

Try moment 5, “Goal reported,” then moment 6, “Goal corrected.” Select “Show me why” to inspect the revised goal. Change the audience and language to see how the presentation changes while the evidence stays fixed.

## Azure implementation

A manual Azure Container Apps job uses managed identity to call a dedicated Azure OpenAI deployment. It publishes a private Blob run ledger containing facts, agent handoffs, rejected drafts, latency and usage. A separate serving identity has read-only storage access and no inference role. An exclusive lease prevents concurrent publishers, while call, token and timeout limits bound each generation run. The public application cannot start paid generation.

The repository and Azure resource group are isolated from existing Dhisana services. All teams and events are fictional; no licensed match footage, tracking or customer data is used.

## Evidence and tradeoffs

In an eight-case synthetic comparison, the multi-agent workflow passed publication checks in all eight cases; the single-agent baseline passed three. Mean generation time was 23.77 seconds versus 12.56 seconds. The repository includes the outputs, full run records, regression tests and reproducible client checks. The failed trials are included too. In live testing, the verifier caught a Spanish draft that confused pass attempts with completions; publication was withheld. That exposed and led to a regression-tested fix in how reviewer feedback reached the editor.

Review takes extra time and model calls. The evaluation is small, and the advisory grader uses the same model family. It helps us find problems; it does not prove that multiple agents always outperform one. Deterministic code remains the right tool for score arithmetic; agents add value in selecting, challenging and adapting explanations.

## Current scope

The demonstration uses six accelerated authored event batches and waits for review between batches. It is not a subsecond real-world broadcast feed. Model reviewers can share errors, and evidence links do not guarantee every sentence is correct. Actual host acceptance and account-policy restrictions are listed in the verification document; MCP protocol support alone is not presented as proof that every ChatGPT, Claude or Copilot account is connected.
