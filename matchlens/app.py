"""FastAPI and official MCP SDK 2.x server with an MCP Apps resource."""

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import BaseModel, Field, validate_call

from matchlens import service

WEB = Path(__file__).parent / "web"
UI_URI = "ui://matchlens/match.html"
READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)
mcp = MCPServer(
    "MatchLens",
    version="0.1.0",
    instructions="Explore synthetic football matches. Use explain_moment for evidence-backed "
    "analysis and the interactive viewer; use get_evidence to verify claims. Never describe "
    "the fixture as real match data. Narrative source statistics_only means AI is unavailable. "
    "Tools never trigger paid generation or publish externally.",
)


def html_bundle() -> str:
    return (
        (WEB / "index.html")
        .read_text()
        .replace(
            '<link rel="stylesheet" href="/app.css" />',
            "<style>" + (WEB / "app.css").read_text() + "</style>",
        )
        .replace(
            '<script type="module" src="/app.js"></script>',
            '<script type="module">' + (WEB / "app.js").read_text() + "</script>",
        )
    )


@mcp.resource(
    UI_URI,
    mime_type="text/html;profile=mcp-app",
    meta={
        "ui": {"prefersBorder": False, "csp": {"connectDomains": [], "resourceDomains": []}},
        "openai/ui": {
            "preferredDisplayMode": "fullscreen",
            "availableDisplayModes": ["inline", "fullscreen"],
        },
    },
)
def match_view() -> str:
    """Interactive match replay, evidence timeline and audience controls."""
    return html_bundle()


def register_tool(name, fn, ui=False):
    meta = {"ui": {"resourceUri": UI_URI}} if ui else None
    mcp.tool(name=name, annotations=READ_ONLY, meta=meta)(fn)


# Explicit functions preserve meaningful signatures and portable JSON schemas.
register_tool("list_matches", service.list_matches)
register_tool("get_match_snapshot", service.get_match_snapshot)
register_tool("get_evidence", service.get_evidence)
register_tool("compare_match_windows", service.compare_match_windows)


@mcp.tool(annotations=READ_ONLY, meta={"ui": {"resourceUri": UI_URI}})
def explain_moment(
    match_id: str = "harbor-summit-demo",
    start_second: int = 3300,
    end_second: int = 3900,
    audience: service.Audience = "fan",
    language: service.Language = "en",
) -> CallToolResult:
    """Explain a window with saved insights and an interactive pitch; defaults to 55–65m."""
    data = service.explain_moment(match_id, start_second, end_second, audience, language)
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(data))], structuredContent=data
    )


@mcp.tool(annotations=READ_ONLY, meta={"ui": {"resourceUri": UI_URI}})
def create_recap(
    match_id: str = "harbor-summit-demo",
    audience: service.Audience = "fan",
    language: service.Language = "en",
) -> CallToolResult:
    """Retrieve the prepared full-match recap and evidence. Read-only; does not publish."""
    data = service.create_recap(match_id, audience, language)
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(data))], structuredContent=data
    )


hosts = ["127.0.0.1:*", "localhost:*", "testserver"]
public_host = os.getenv("MATCHLENS_PUBLIC_HOST")
if public_host:
    hosts.append(public_host)
# Explicit allowed host list retains DNS rebinding protection locally and in Azure.
mcp_app = mcp.streamable_http_app(
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=["http://127.0.0.1:*", "http://localhost:*"]
        + ([f"https://{public_host}"] if public_host else []),
    ),
)


@asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="MatchLens", version="0.1.0", lifespan=lifespan)


class ToolRequest(BaseModel):
    name: str
    arguments: dict = Field(default_factory=dict)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "synthetic": True,
        "model_calls_enabled": False,
        "saved_ai_insights": service.INSIGHTS.exists(),
    }


@app.get("/", response_class=HTMLResponse)
def index():
    return html_bundle()


@app.post("/api/tools")
def call_tool(request: ToolRequest):
    tools = {
        fn.__name__: fn
        for fn in (
            service.list_matches,
            service.get_match_snapshot,
            service.get_evidence,
            service.explain_moment,
            service.compare_match_windows,
            service.create_recap,
        )
    }
    fn = tools.get(request.name)
    if fn is None:
        raise HTTPException(404, "Unknown tool")
    try:
        # MCP validates its own tool schemas. REST receives identical Pydantic validation.
        return {"structuredContent": REST_TOOLS[request.name](**request.arguments)}
    except (ValueError, TypeError):
        raise HTTPException(422, "Invalid tool arguments") from None


REST_TOOLS = {
    fn.__name__: validate_call(fn)
    for fn in (
        service.list_matches,
        service.get_match_snapshot,
        service.get_evidence,
        service.explain_moment,
        service.compare_match_windows,
        service.create_recap,
    )
}
app.mount("/", mcp_app)
