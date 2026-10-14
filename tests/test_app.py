import pytest
from fastapi.testclient import TestClient

from matchlens.app import UI_URI, app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as instance:
        yield instance


def rpc(client, method, params=None):
    return client.post(
        "/mcp",
        headers={"Accept": "application/json, text/event-stream"},
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}},
    )


def test_api_and_ui(client):
    assert client.get("/health").json()["model_calls_enabled"] is False
    assert "MatchLens" in client.get("/").text
    response = client.post("/api/tools", json={"name": "explain_moment"})
    assert response.status_code == 200
    assert response.json()["structuredContent"]["match"]["synthetic"]
    assert client.post("/api/tools", json={"name": "delete_match"}).status_code == 404
    assert (
        client.post(
            "/api/tools", json={"name": "explain_moment", "arguments": {"language": "xx"}}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/tools", json={"name": "get_evidence", "arguments": {"event_ids": "fake"}}
        ).status_code
        == 422
    )


def test_mcp_discovery_invocation_and_resource(client):
    result = rpc(
        client,
        "initialize",
        {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"},
        },
    )
    assert result.status_code == 200, result.text
    result = rpc(client, "tools/list")
    tools = result.json()["result"]["tools"]
    explain = next(t for t in tools if t["name"] == "explain_moment")
    assert explain["_meta"]["ui"]["resourceUri"] == UI_URI
    assert explain["annotations"]["readOnlyHint"] is True
    response = rpc(client, "tools/call", {"name": "explain_moment", "arguments": {}})
    assert response.status_code == 200, response.text
    data = response.json()["result"]["structuredContent"]
    assert data["stats"]["harbor"]["high_recoveries"] == 3
    resource = rpc(client, "resources/read", {"uri": UI_URI}).json()["result"]["contents"][0]
    assert resource["mimeType"] == "text/html;profile=mcp-app"
    assert "ui/initialize" in resource["text"]
    assert "/app.js" not in resource["text"]
    assert "/app.css" not in resource["text"]
    assert "--bs-body-bg" in resource["text"]


def test_mcp_rejects_bad_arguments(client):
    response = rpc(
        client,
        "tools/call",
        {"name": "explain_moment", "arguments": {"start_second": 4000, "end_second": 3000}},
    )
    data = response.json()
    assert data.get("error") or data["result"]["isError"]


def test_dns_rebinding_is_blocked(client):
    response = client.post(
        "/mcp",
        headers={"Host": "evil.example", "Accept": "application/json, text/event-stream"},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
    )
    assert response.status_code == 421
