# SDK and API research — 14 October 2026

Official documentation was reviewed in Chrome; package versions were verified against PyPI and installed locally. Pinning prevents silent API drift. Recheck release notes before upgrades.

| Component | Verified release | Decision |
|---|---|---|
| OpenAI Agents SDK (Python) | 0.23.1 | `Agent`, `Runner`, `function_tool`, typed outputs, bounded multi-agent workflow |
| OpenAI Python | 3.31.0 | Responses API through `OpenAIResponsesModel` |
| MCP Python SDK | 2.3.0 | Current `MCPServer`; Streamable HTTP, structured tools, MCP Apps resources |
| FastAPI | 0.143.1 | Web preview, health and same-origin tool adapter |
| Azure Identity | 1.26.0 | Optional Azure identity for offline generation |

Sources: [Agents SDK quickstart](https://developers.openai.com/api/docs/guides/agents/quickstart?lang=python), [Agents SDK package](https://pypi.org/project/openai-agents/), [OpenAI Python package](https://pypi.org/project/openai/), [MCP package](https://pypi.org/project/mcp/).

## GPT-6 and Azure

The [official OpenAI announcement](https://x.com/OpenAI/status/2107894997538525580) and [model guide](https://developers.openai.com/api/docs/guides/latest-model) describe the GPT-6 generation. [Azure Responses documentation](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/responses) describes the `/openai/v1/` endpoint. The API model string in Azure is the **deployment name**.

Azure's eastus catalog and a successful new deployment verified `gpt-6-sol`, version `2026-09-22`, GlobalStandard for this subscription. This does not establish availability in every region/account. MatchLens's model remains configurable. GlobalStandard may process requests globally; use only synthetic demo evidence here and assess regional requirements before private data.

## Intelligent UI and interoperability

ChatGPT's native Intelligent UI is not treated as a separately available public API. MatchLens uses documented **MCP Apps**: a `text/html;profile=mcp-app` resource, tool `ui.resourceUri`, JSON-RPC `ui/initialize`, host tool calls, and model-context updates. The UI is portable where a host supports MCP Apps; the backend tools remain useful elsewhere.

- [OpenAI app quickstart](https://developers.openai.com/plugins/build/app-quickstart)
- [ChatGPT UI integration](https://developers.openai.com/plugins/build/chatgpt-ui)
- [MCP Extensions specification](https://github.com/openai/mcp-extensions/blob/main/docs/spec.md)
- [Claude Code MCP](https://code.claude.com/docs/en/mcp)
- [VS Code MCP Apps support](https://code.visualstudio.com/blogs/2026/01/26/mcp-apps-support)
- [Copilot Studio existing MCP server](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent)

Copilot Studio uses Streamable HTTP. “Copilot support” does not mean all Microsoft Copilot products accept custom MCP or render the same UI. Each host needs its own connection and acceptance test.

## Hackathon fit

[Event landing page](https://events.microsoft.com/flow/microsoft/plmshackathon/registration/page/landing) and [official rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md) were consulted. The new-repository approach isolates the submission from Dhisana. Public repository publication and an under-two-minute demo are submission preparation steps; no registration, eligibility claim or submission is implied by this implementation. Confirm the current organizer packet and data rights before submitting.
