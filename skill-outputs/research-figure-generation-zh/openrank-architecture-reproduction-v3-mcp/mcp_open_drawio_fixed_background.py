from __future__ import annotations

import anyio
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


OUT = Path(__file__).resolve().parent
SOURCE = OUT / "openrank_architecture_reproduction.fixed-background.drawio.xml"


def serialise_result(result) -> dict:
    payload = {"content": []}
    for item in result.content:
        payload["content"].append(item.model_dump() if hasattr(item, "model_dump") else str(item))
    if getattr(result, "structuredContent", None) is not None:
        payload["structuredContent"] = result.structuredContent
    return payload


async def main() -> None:
    content = SOURCE.read_text(encoding="utf-8")
    params = StdioServerParameters(command="npx", args=["-y", "@drawio/mcp"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "open_drawio_xml",
                arguments={"content": content, "dark": "auto"},
            )
            (OUT / "mcp_open_drawio_fixed_background.json").write_text(
                json.dumps(serialise_result(result), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    print(OUT / "mcp_open_drawio_fixed_background.json")


if __name__ == "__main__":
    anyio.run(main)
