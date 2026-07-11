from __future__ import annotations

import anyio
import json
import shutil
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


OUT = Path(__file__).resolve().parent
SOURCE = OUT / "openrank_architecture_reproduction.svg"
INKSCAPE_SERVER = Path(r"C:\Users\zbh\.agents\mcp-servers\inkscape-mcps")
PY312 = Path(r"C:\Users\zbh\AppData\Local\Programs\Python\Python312\python.exe")
WORKSPACE = Path(r"C:\Users\zbh\.agents\mcp-workspaces\inkscape\openrank-architecture-v3-mcp")


def serialise_result(result) -> dict:
    payload = {"content": []}
    for item in result.content:
        payload["content"].append(item.model_dump() if hasattr(item, "model_dump") else str(item))
    if getattr(result, "structuredContent", None) is not None:
        payload["structuredContent"] = result.structuredContent
    return payload


async def main() -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    workspace_svg = WORKSPACE / "openrank_architecture_reproduction.svg"
    shutil.copy2(SOURCE, workspace_svg)

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

            validate = await session.call_tool(
                "dom_validate",
                arguments={"doc_type": "file", "doc_path": workspace_svg.name},
            )
            (OUT / "mcp_dom_validate.json").write_text(
                json.dumps(serialise_result(validate), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            clean = await session.call_tool(
                "dom_clean",
                arguments={
                    "doc_type": "file",
                    "doc_path": workspace_svg.name,
                    "save_as": "openrank_architecture_reproduction.cleaned.svg",
                },
            )
            (OUT / "mcp_dom_clean.json").write_text(
                json.dumps(serialise_result(clean), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            cleaned = WORKSPACE / "openrank_architecture_reproduction.cleaned.svg"
            export_results = {}
            for export_type, dpi in [("png", 96), ("pdf", None)]:
                target = f"openrank_architecture_reproduction.{export_type}"
                args = {
                    "doc_type": "file",
                    "doc_path": cleaned.name if cleaned.exists() else workspace_svg.name,
                    "actions": [],
                    "export_type": export_type,
                    "export_out": target,
                    "export_area": "page",
                    "timeout_s": 120,
                }
                if dpi is not None:
                    args["export_dpi"] = dpi
                result = await session.call_tool("action_run", arguments=args)
                export_results[export_type] = serialise_result(result)

            (OUT / "mcp_action_run_exports.json").write_text(
                json.dumps(export_results, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    for name in [
        "openrank_architecture_reproduction.cleaned.svg",
        "openrank_architecture_reproduction.png",
        "openrank_architecture_reproduction.pdf",
    ]:
        src = WORKSPACE / name
        if src.exists():
            dst_name = "openrank_architecture_reproduction.svg" if name.endswith(".cleaned.svg") else name
            shutil.copy2(src, OUT / dst_name)

    print(OUT)


if __name__ == "__main__":
    anyio.run(main)
