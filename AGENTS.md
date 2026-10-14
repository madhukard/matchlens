# MatchLens development

This is a separate project from Dhisana. Work in this repository and the MatchLens Azure resource group. Do not change Dhisana production infrastructure, databases or code as part of MatchLens work without a new explicit instruction.

- Python 3.12, Pydantic V2, OpenAI Agents SDK and official MCP Python SDK 2.x.
- Run `pytest -q`, `ruff check matchlens tests scripts` and `node --check matchlens/web/app.js` after relevant changes. Include tests for changed backend behavior.
- Numerical match statistics are deterministic Python calculations; text analysis uses the model workflow. Validate model output schemas and evidence IDs, and preserve review failures.
- Public MCP and preview routes are read-only. They must not hold inference credentials or trigger paid generation. Authentication and a budget policy are prerequisites to adding an on-demand generation service.
- All shipped match data is synthetic. Never present it as licensed or real Premier League data, and do not copy Dhisana tenant data into this repository.
- Keep HTML, CSS and JavaScript in separate source files; `html_bundle` embeds them into the MCP Apps resource. Test the bundled resource after formatting changes.
- Keep host integrations portable and provide text results for clients without MCP Apps rendering. Distinguish protocol tests from actual client acceptance tests.
- Azure scripts must scope every change to the intended subscription and `matchlens-dev-rg`. Do not use shared production identities, secrets or registries.
