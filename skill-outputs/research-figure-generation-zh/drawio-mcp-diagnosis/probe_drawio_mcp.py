from __future__ import annotations

import anyio
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


OUT = Path(__file__).resolve().parent


async def main() -> None:
    params = StdioServerParameters(
        command="npx",
        args=["-y", "@drawio/mcp"],
        env={},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            payload = []
            for tool in tools.tools:
                payload.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                )
            (OUT / "drawio_mcp_tools.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    anyio.run(main)
