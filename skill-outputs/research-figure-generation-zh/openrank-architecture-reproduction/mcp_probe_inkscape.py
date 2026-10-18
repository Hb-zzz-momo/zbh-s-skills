from __future__ import annotations

import anyio
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


OUT = Path(__file__).resolve().parent
INKSCAPE_SERVER = Path(r"C:\Users\zbh\.agents\mcp-servers\inkscape-mcps")
PY312 = Path(r"C:\Users\zbh\AppData\Local\Programs\Python\Python312\python.exe")
WORKSPACE = Path(r"C:\Users\zbh\.agents\mcp-workspaces\inkscape\openrank-architecture")


async def main() -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    params = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "--directory",
            str(INKSCAPE_SERVER),
            "--python",
            str(PY312),
            "inkscape-mcp",
        ],
        env={
            "INKS_WORKSPACE": str(WORKSPACE),
            "INKS_MAX_FILE": "52428800",
            "INKS_TIMEOUT": "120",
            "INKS_MAX_CONC": "4",
            "INKS_INKSCAPE_BIN": r"D:\newapp\bin\inkscape.com",
        },
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
            (OUT / "mcp_inkscape_tools.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(json.dumps([tool["name"] for tool in payload], ensure_ascii=False))


if __name__ == "__main__":
    anyio.run(main)
