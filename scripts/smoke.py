"""Exercise a running MatchLens server through the official MCP client."""

import asyncio
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def check(url: str) -> None:
    async with streamable_http_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert len(tools.tools) == 6
            result = await session.call_tool("explain_moment", {})
            assert not result.is_error
            data = result.structured_content
            assert data["match"]["synthetic"]
            assert data["stats"]["harbor"]["high_recoveries"] == 3
            resource = await session.read_resource("ui://matchlens/match.html")
            assert resource.contents[0].mime_type == "text/html;profile=mcp-app"
            assert "ui/initialize" in resource.contents[0].text
            bad = await session.call_tool("get_match_snapshot", {"match_id": "unknown"})
            assert bad.is_error
            print(
                f"PASS: tools, evidence, UI and validation; source={data['insight']['source']}"
            )


if __name__ == "__main__":
    asyncio.run(check(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/mcp"))
