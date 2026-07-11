from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape


OUT = Path(__file__).resolve().parent
W, H = 1690, 939

NAVY = "#0d1b2f"
BLUE = "#1558ad"
BLUE_DARK = "#0d3f87"
GREEN = "#16763a"
ORANGE = "#ef6a1a"
PURPLE = "#5b2a97"
TEXT = "#101828"


class Drawio:
    def __init__(self) -> None:
        self.parts: list[str] = [
            f'<mxGraphModel dx="1690" dy="939" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{W}" pageHeight="{H}" math="0" shadow="0">',
            "<root>",
            '<mxCell id="0"/>',
            '<mxCell id="1" parent="0"/>',
        ]
        self.n = 2

    def new_id(self, prefix: str) -> str:
        self.n += 1
        return f"{prefix}{self.n}"

    def vertex(self, value: str, x: float, y: float, w: float, h: float, style: str, prefix: str = "v") -> str:
        cid = self.new_id(prefix)
        self.parts.append(
            f'<mxCell id="{cid}" value="{escape(value)}" style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>'
            "</mxCell>"
        )
        return cid

    def edge(self, source: str, target: str, value: str = "", color: str = "#111827", dashed: bool = False) -> str:
        cid = self.new_id("e")
        dash = "dashed=1;dashPattern=5 4;" if dashed else ""
        style = (
            "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=classic;"
            f"strokeColor={color};strokeWidth=2;{dash}"
        )
        self.parts.append(
            f'<mxCell id="{cid}" value="{escape(value)}" style="{style}" edge="1" parent="1" source="{source}" target="{target}">'
            '<mxGeometry relative="1" as="geometry"/>'
            "</mxCell>"
        )
        return cid

    def finish(self) -> str:
        return "\n".join([*self.parts, "</root>", "</mxGraphModel>"])


def panel(d: Drawio, x: int, y: int, w: int, h: int, color: str, no: str, title: str) -> str:
    box = d.vertex(
        "",
        x,
        y,
        w,
        h,
        f"rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor={color};strokeWidth=2;dashed=1;dashPattern=5 3;",
        "panel",
    )
    d.vertex(no, x + 21, y + 14, 34, 34, f"ellipse;whiteSpace=wrap;html=1;fillColor={color};strokeColor={color};fontColor=#ffffff;fontStyle=1;fontSize=18;", "num")
    d.vertex(title, x + 66, y + 15, w - 75, 30, f"text;html=1;strokeColor=none;fillColor=none;fontColor={color};fontStyle=1;fontSize=20;align=left;verticalAlign=middle;", "title")
    return box


def item(d: Drawio, x: int, y: int, w: int, h: int, label: str, color: str) -> str:
    return d.vertex(
        label.replace("\n", "&#xa;"),
        x,
        y,
        w,
        h,
        f"rounded=1;whiteSpace=wrap;html=1;fillColor=#fbfdff;strokeColor={color};strokeWidth=1.3;fontColor={TEXT};fontSize=12;spacingLeft=12;align=left;verticalAlign=middle;",
        "item",
    )


def small_text(d: Drawio, x: int, y: int, w: int, h: int, text: str, color: str = TEXT, size: int = 12, bold: bool = False) -> str:
    return d.vertex(
        text.replace("\n", "&#xa;"),
        x,
        y,
        w,
        h,
        f"text;html=1;strokeColor=none;fillColor=none;fontColor={color};fontSize={size};fontStyle={1 if bold else 0};align=center;verticalAlign=middle;",
        "txt",
    )


def main() -> None:
    d = Drawio()
    small_text(d, 250, 9, 1190, 42, "OpenRank Visualization Platform: System Architecture", NAVY, 34, True)
    small_text(d, 350, 52, 990, 26, "LLM Open-Source Ecosystem Health Analytics Based on OpenDigger Metrics", "#28384d", 18, False)

    panel(d, 12, 96, 212, 620, BLUE, "1", "User & Client")
    panel(d, 278, 96, 282, 520, GREEN, "2", "Vue 3 Frontend")
    panel(d, 626, 96, 355, 620, BLUE_DARK, "3", "Flask Backend Service")
    panel(d, 1055, 96, 307, 620, GREEN, "4", "Data Processing & Storage")
    panel(d, 1420, 96, 266, 620, ORANGE, "5", "External Data Sources")

    user = d.vertex("User&#xa;Client", 64, 210, 104, 98, f"rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor={NAVY};strokeWidth=4;fontColor={NAVY};fontStyle=1;fontSize=14;", "user")
    web = item(d, 28, 352, 180, 64, "Web Browser", BLUE)
    item(d, 28, 440, 180, 64, "Student / Analyst /\nResearcher", BLUE)
    views = item(d, 28, 528, 180, 64, "Interactive Dashboard\nAccess", BLUE)

    frontend_items = []
    fy = 158
    for label in ["Vite Build System", "Vue Router", "Pinia State Management", "API Service Layer", "ECharts Visualization Engine"]:
        frontend_items.append(item(d, 291, fy, 252, 36, label, GREEN))
        fy += 43
    d.vertex("Main Views&#xa;&#xa;Home Dashboard&#xa;LLM Ecosystem Summary&#xa;Visual Lab&#xa;Favorites&#xa;Login / Register", 291, 384, 127, 216, f"rounded=1;whiteSpace=wrap;html=1;fillColor=#fbfffb;strokeColor={GREEN};strokeWidth=1.4;fontColor={TEXT};fontSize=10;align=center;", "views")
    d.vertex("Reusable Components&#xa;&#xa;Metric Line Chart&#xa;&#xa;Radar Compare&#xa;&#xa;Contributor Bar Chart", 426, 384, 122, 216, f"rounded=1;whiteSpace=wrap;html=1;fillColor=#fbfffb;strokeColor={GREEN};strokeWidth=1.4;fontColor={TEXT};fontSize=10;align=center;", "comp")
    item(d, 232, 627, 360, 93, "Receives JSON Data from Backend      Renders Charts & Dashboard Views", GREEN)

    app = item(d, 639, 158, 326, 44, "Application Entry: main.py", BLUE_DARK)
    small_text(d, 704, 220, 200, 28, "REST APIs", BLUE_DARK, 16, True)
    api_targets = []
    api_rows = [
        ("OpenDigger API Module", "/api/llm/summary"),
        ("LLM Summary / Report API", "/api/llm/rank/metrics"),
        ("Contributor Risk API", "/api/llm/report"),
        ("Auth API", "/api/auth/login"),
        ("Auth API (Register)", "/api/auth/register"),
        ("Favorites API", "/api/favorites"),
        ("Contributor Risk API", "/api/health/contributors/risk"),
    ]
    ay = 246
    for label, path in api_rows:
        api_targets.append(item(d, 642, ay, 180, 34, label, BLUE_DARK))
        item(d, 828, ay, 128, 34, path, BLUE_DARK)
        ay += 38
    mid = d.vertex("Middleware / Services&#xa;&#xa;JWT Authentication        API Rate Limiting&#xa;&#xa;CORS                         Request Cache", 640, 537, 323, 127, f"rounded=1;whiteSpace=wrap;html=1;fillColor=#fbfdff;strokeColor={BLUE_DARK};strokeWidth=1.4;fontColor={TEXT};fontSize=12;align=center;", "mid")

    pipe = d.vertex("Data Processing Pipeline&#xa;&#xa;Data Fetcher&#xa;Metric Utilities&#xa;Config Loader&#xa;Health Score Calculation&#xa;Time-Series Aggregation&#xa;Data Cache", 1072, 158, 272, 272, f"rounded=1;whiteSpace=wrap;html=1;fillColor=#fbfffb;strokeColor={GREEN};strokeWidth=1.4;fontColor={TEXT};fontSize=12;align=center;", "pipe")
    health = d.vertex("Health Score =&#xa;0.5 x OpenRank + 0.3 x Activity + 0.2 x Stability", 1072, 449, 272, 57, f"rounded=1;whiteSpace=wrap;html=1;fillColor=#fbfff9;strokeColor={GREEN};strokeWidth=1.4;dashed=1;dashPattern=5 3;fontColor={GREEN};fontSize=12;fontStyle=1;align=center;", "health")
    db = d.vertex("SQLite Database&#xa;&#xa;User&#xa;Favorite&#xa;MetricSeries", 1072, 548, 272, 145, f"rounded=1;whiteSpace=wrap;html=1;fillColor=#fbfffb;strokeColor={GREEN};strokeWidth=1.4;fontColor={TEXT};fontSize=12;align=center;", "db")

    external = []
    ey = 158
    for label in ["OpenDigger", "OpenRank Metrics", "GitHub Repository Metadata", "Project Activity Metrics", "Developer / Contributor Metrics"]:
        external.append(item(d, 1438, ey, 226, 47, label, ORANGE))
        ey += 57
    ingestion = d.vertex("Metric Ingestion&#xa;&#xa;OpenRank       Activity&#xa;Stars          Forks&#xa;Issues         Pull Requests&#xa;Contributors", 1438, 482, 226, 190, f"rounded=1;whiteSpace=wrap;html=1;fillColor=#fffaf5;strokeColor={ORANGE};strokeWidth=1.5;dashed=1;dashPattern=5 3;fontColor={TEXT};fontSize=12;align=center;", "ingest")

    d.edge(user, frontend_items[0], "HTTPS Request")
    d.edge(frontend_items[3], app, "REST API Requests (JSON)")
    d.edge(api_targets[0], pipe, "Process Requests")
    d.edge(external[0], pipe, "Fetch Data (API / Scrape)")
    d.edge(pipe, health, "")
    d.edge(health, db, "Processed Metrics")
    d.edge(db, api_targets[0], "Query / Read (Results)", BLUE, True)
    d.edge(pipe, api_targets[1], "Cached Data / DB Results", BLUE, True)
    d.edge(mid, frontend_items[-1], "JSON Responses", BLUE, True)
    d.edge(frontend_items[-1], views, "Rendered Views")

    d.vertex("Platform Capabilities&#xa;&#xa;Interactive Visualization    AI Interpretation    PNG Export    Report Export    Favorites Management    Risk Analysis    Health Ranking    Multi-chart Visual Analytics", 12, 740, 1675, 103, f"rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor={PURPLE};strokeWidth=1.5;dashed=1;dashPattern=5 3;fontColor={TEXT};fontSize=12;align=center;", "cap")
    d.vertex("Legend:  Infrastructure / Backend      Data Processing      Analytics / AI Interpretation      Visualization / Capabilities", 28, 871, 862, 50, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#667085;strokeWidth=1.2;fontColor=#101828;fontSize=12;align=center;", "legend")
    small_text(d, 960, 872, 680, 50, "Primary Data Flow          Response / Return Flow          Bidirectional / Data Access", TEXT, 12)

    model = d.finish()
    graph_path = OUT / "openrank_architecture_reproduction.drawio.xml"
    graph_path.write_text(model, encoding="utf-8")
    mxfile = (
        '<mxfile host="app.diagrams.net" modified="2026-06-26T00:00:00.000Z" agent="Codex" version="24.7.0">'
        f'<diagram id="openrank-architecture" name="OpenRank Architecture">{model}</diagram>'
        "</mxfile>"
    )
    (OUT / "openrank_architecture_reproduction.drawio").write_text(mxfile, encoding="utf-8")
    print(graph_path)


if __name__ == "__main__":
    main()
