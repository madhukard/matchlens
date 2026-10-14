# Connect MatchLens

Demo URL: https://matchlens-dev.agreeablemushroom-147a503e.eastus.azurecontainerapps.io

MCP URL: https://matchlens-dev.agreeablemushroom-147a503e.eastus.azurecontainerapps.io/mcp

Transport: **Streamable HTTP**. Authentication: **None**, deliberately limited to synthetic, read-only public demo data. No model API key belongs in client configuration.

## ChatGPT

Use ChatGPT's custom app/developer connection flow, where enabled by your plan and workspace administrator. Create a connection named MatchLens using the MCP URL and no authentication. Enable it for the conversation and ask:

> Show MatchLens and explain what happened between minutes 55 and 65. Show the evidence on the pitch.

The `explain_moment` and `create_recap` tools advertise an MCP Apps resource. It includes fan/analyst controls, a pitch replay, evidence cards and English/Spanish narratives. The private plugin package under `integrations/matchlens/` includes the same server plus workflow instructions. Installation and permission settings are per account; a working endpoint alone does not mean every account has connected it.

## Claude Code

```sh
claude mcp add --transport http matchlens https://matchlens-dev.agreeablemushroom-147a503e.eastus.azurecontainerapps.io/mcp
```

Alternatively merge `integrations/claude.mcp.json` into the project's `.mcp.json`; do not overwrite existing servers. Use `/mcp` to check the connection. Ask for a recap or compare windows. Open the demo URL for the interactive pitch; do not expect a terminal to render the MCP App.

## GitHub Copilot in VS Code

Merge `integrations/vscode.mcp.json` into `.vscode/mcp.json`. Trust this synthetic demo server using VS Code's MCP connection flow and enable its tools in agent chat. Ask for the 55–65 minute evidence. A supported MCP Apps build can render the resource; otherwise use structured tool results and the web preview.

## Microsoft Copilot Studio

In the intended agent, choose **Tools → Add a tool → Model Context Protocol** (the exact labels may evolve). Use the MCP URL, Streamable HTTP and None authentication. Review the six discovered tools and test in the agent's test pane before publishing. This connection does not automatically install an app in consumer Microsoft Copilot or guarantee embedded HTML rendering in a Teams channel.

## Acceptance checks

1. Discover six tools: list_matches, get_match_snapshot, get_evidence, explain_moment, compare_match_windows, create_recap.
2. Default window: Harbor 3 shots, 3 high recoveries, 1 goal; score at 65 minutes is 1–1.
3. Full-match recap: final score 2–1; evidence includes both teams' goals.
4. Request an unknown match or reversed time range: it must fail validation.
5. Supporting hosts render the pitch; selecting an event updates model context through the MCP Apps bridge.
6. Non-UI clients receive equivalent structured and text evidence.

Host rendering should be verified separately in each client; protocol compliance alone is not a claim of an end-to-end test in every product.
