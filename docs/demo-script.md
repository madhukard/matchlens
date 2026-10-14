# MatchLens demo — target 105 seconds

Record the actual deployed application. Use a completed, approved six-frame run, explicitly labelled as a recorded synthetic scenario. Do not present replay as an active real-world match. No music or third-party footage is needed.

| Time | Screen/action | English narration or caption |
| --- | --- | --- |
| 0–12 s | Match room, fictional teams visible | A goal is reported. Then the feed corrects it. Can your AI explanation keep up? MatchLens turns synthetic football events into evidence-linked stories. |
| 12–27 s | Select moment 5, show 1–0 and reviewed story | The analyst selects a story. An evidence critic checks it, an editor adapts it, and a verifier checks every audience and language version. |
| 27–45 s | Select moment 6; 0–0, correction banner and sequence | A revised event voids the goal. The score changes, the old citation is superseded, and all stories must acknowledge the correction. The UI switches to its timeline. |
| 45–58 s | Show me why; select voided goal | Every explanation links to versioned evidence. The feed does not say why the goal changed, so MatchLens does not invent a reason. |
| 58–72 s | Analyst, Spanish; compare a prior phase | Fans get a short update. Analysts get counts and window caveats. Both are available in English and Spanish. |
| 72–87 s | How this was checked; actual trace | Agents share a fixed evidence snapshot. A rejected draft gets one correction attempt. If review still fails, current statistics remain visible and the narrative is withheld. |
| 87–105 s | Architecture/evaluation caption over app | Built with OpenAI Agents SDK, MCP and isolated Azure services. Four paired cases: multi-agent 4/4 published, baseline 2/4, with greater latency and token use. Small exploratory evaluation, not a reliability guarantee. |

End with the public repository and demo links only after publication is approved. State host acceptance accurately: do not imply Claude Code or Copilot passed while authentication or organization policy blocks them. The browser demonstration and MCP protocol test are independently reproducible.

## Recorded artifact

`dist/matchlens-demo.mp4` is 1:53, 1920×1080, H.264 with English captions and no audio. It starts with a labelled replay still of the reported goal, followed by actual screen capture of the Azure correction review and audience controls. The last trace frame is held for the evaluation caption. No generation latency is sped up or represented as subsecond. Extracted opening, correction and closing frames were visually inspected. Publication remains an owner action/approval.
