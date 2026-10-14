# Verification — 14 October 2026

- 23 Python tests passed, including exact statistics, boundaries, input rejection, MCP discovery, resource bundling, reviewer rejection, bounded correction, atomic publication and all eight shipped artifact schemas/citations.
- Ruff, JavaScript syntax checking, dependency consistency and GitHub Actions passed.
- Eight narratives were generated through the real Azure `gpt-6-sol` deployment and the OpenAI Agents SDK. Both evidence reviews passed for every shipped artifact. Rejected attempts were not published.
- Azure Container Registry built the Linux image `matchlens:v0.1.0` successfully. Azure reports the westus2 app and environment Succeeded.
- Public `/health` returned `status=ok`, `saved_ai_insights=true`, `model_calls_enabled=false`.
- The official MCP Python client passed discovery, tool invocation, evidence checks, UI resource retrieval and invalid-input checks against the public HTTPS endpoint.
- Chrome verified the deployed narrative, clickable evidence and match view. Local Chrome checks covered audience changes, the full recap and a 390px viewport without horizontal overflow.
- A local MCP Apps host harness verified initialization, host-tool calls, selected-event model context, Spanish narrative/context consistency and host-theme handling.
- The private ChatGPT plugin listing is present under Installed with one MCP server and one skill. The account release is `pluginrel_6acfdfe94bd881919d1aeb273bf256d6`; plugin ID is `plugins_6acfdfe899388191af6dc5741e611de1`.

Not yet verified: rendering inside an actual ChatGPT conversation, a Claude Code session, a VS Code Copilot session, or a Copilot Studio agent. Their connection configurations and steps are included; a reference bridge test does not establish behavior in every host.

The original eastus environment stalled before app creation. Its deployment was canceled and deletion requested; the last observed state was ScheduledForDelete. The live service uses the successful westus2 environment, in the same new resource group. No existing Dhisana resource was changed.
