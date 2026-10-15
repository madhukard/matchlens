# Try MatchLens in three minutes

[Open the match room](https://matchlens-dev.redforest-787f42f7.westus2.azurecontainerapps.io) · [Watch the demo](https://www.youtube.com/watch?v=qdtIEEIp8bE) · [Source](https://github.com/madhukard/matchlens)

No account, API key or payment is needed for the browser demo. All match events and teams are fictional. The public view reads a saved, reviewed Azure run; opening it does not start model generation. One serving replica is kept running to avoid scale-from-zero delays during tool discovery.

1. Select moment 5, **Goal reported**. Harbor leads 1–0.
2. Select moment 6, **Goal corrected**. The score returns to 0–0. Open **Show me why** to inspect the revised goal.
3. Change between fan and analyst, then English and Spanish. The same correction should remain clear in every version.
4. Open the review trace. The analyst selects facts, the critic challenges the selection, the editor adapts the story, and the verifier checks the result. Rejected explanations are withheld; the current statistics remain available.

For the comparison with a single agent, read [evaluation.md](evaluation.md). The earlier four-case result in the video is preserved. Additional cases and unsuccessful attempts are reported separately; automated validators and model opinions are not human verification.

## Client scope

The browser demo and Claude Code tool calls have been tested. The ChatGPT plugin is installed, but its native interactive rendering has not yet been confirmed by the owner. Copilot CLI was blocked by the account's organization policy on third-party MCP servers. Neither is required to use the browser demo. No claim is made that all three hosts have passed acceptance testing.

## What this prototype does not show

It does not connect to a real football broadcast or licensed match feed. It does not infer the reason for an overturned goal, or establish tactical causality from aggregate event counts. Six authored batches are processed in order, waiting for narrative review between batches. A live-feed pilot is a separate, deferred project.
