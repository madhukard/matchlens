# MatchLens

An evidence-first football match room: an interactive pitch, event replay, exact statistics, and reviewed AI narratives. Built with the **OpenAI Agents SDK**, **MCP Apps**, and **Azure**.

This MVP uses fictional Harbor FC and Summit United and deterministic synthetic events. It contains no licensed Premier League feeds, real player tracking, betting predictions, or Dhisana customer data.

## Run locally

Python 3.12 required.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.lock
pip install -e . --no-deps
uvicorn matchlens.app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. MCP endpoint: http://127.0.0.1:8000/mcp.

```sh
pytest -q
ruff check matchlens tests
```

## How the agents work

1. Python computes statistics from immutable, validated event records.
2. The match analyst uses an Agents SDK function tool to retrieve that evidence and creates structured claims.
3. An evidence reviewer checks those claims against the same events.
4. A narrative agent adapts the approved analysis for fans or analysts in English or Spanish.
5. A second review checks the final narrative. Invalid event IDs or failed reviews stop publication.

Narratives are generated **offline**, then saved atomically. The public service exposes only read-only tools and never receives a model credential. Eight saved variants cover 55–65 minutes and the full match, two audiences, and two languages. Other windows return exact statistics with an explicit “AI not generated” message. Model review reduces errors but is not human verification.

To regenerate with Azure, set `MATCHLENS_PROVIDER=azure`, `MATCHLENS_MODEL` to your deployment name, and `AZURE_OPENAI_ENDPOINT`. Supply `AZURE_OPENAI_API_KEY` through your secret manager, or use Azure identity with the appropriate inference role. For OpenAI, set `MATCHLENS_PROVIDER=openai` and `OPENAI_API_KEY`.

```sh
python -m matchlens.intelligence
```

The command makes paid model calls with bounded turns and timeouts. It does not load `.env` automatically. Never commit credentials. Tracing is disabled and Responses requests use `store=False`.

## Clients

- **ChatGPT:** MCP Apps resource renders the interactive match room. Connect the hosted `/mcp` endpoint using an account that supports custom apps, or install the private MatchLens plugin.
- **Claude Code:** HTTP MCP tools provide structured and text results. Its terminal does not render this embedded UI; open the web app for the pitch.
- **GitHub Copilot in VS Code:** MCP tools, with interactive rendering in supported MCP Apps clients.
- **Microsoft Copilot Studio:** connect the Streamable HTTP server as an MCP tool. Text/tool compatibility is provided; the ChatGPT UI is not assumed to render in every Copilot surface.

See [connection instructions](docs/connections.md), [current SDK research](docs/research.md), and [Azure operations](docs/azure.md).

## Boundaries and next steps

This is a working synthetic-data demonstration, not a production match-data service. Real feeds need licensing, ingestion, provenance and retention controls. Authenticated tenant data needs OAuth and authorization before exposure. Arbitrary live questions need an authenticated generation job, rate limits and a budget policy. Keep future Dhisana integration behind an adapter; this repository and Azure resource group are independent.
