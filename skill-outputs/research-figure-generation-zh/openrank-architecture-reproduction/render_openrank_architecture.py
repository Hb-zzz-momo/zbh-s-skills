from __future__ import annotations

from pathlib import Path


OUT = Path(__file__).resolve().parent
W, H = 1708, 973

NAVY = "#0d1b2f"
BLUE = "#1558ad"
BLUE_DARK = "#0d3f87"
GREEN = "#16763a"
GREEN_DARK = "#0b6b32"
ORANGE = "#ef6a1a"
PURPLE = "#5b2a97"
TEXT = "#101828"
MUTED = "#344054"
SOFT = "#f8fbff"


def esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


class SVG:
    def __init__(self) -> None:
        self.parts: list[str] = []

    def add(self, s: str) -> None:
        self.parts.append(s)

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        *,
        r: float = 8,
        fill: str = "white",
        stroke: str = "#98a2b3",
        sw: float = 1.4,
        dash: str | None = None,
        cls: str | None = None,
    ) -> None:
        attrs = [
            f'x="{x}"',
            f'y="{y}"',
            f'width="{w}"',
            f'height="{h}"',
            f'rx="{r}"',
            f'fill="{fill}"',
            f'stroke="{stroke}"',
            f'stroke-width="{sw}"',
        ]
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if cls:
            attrs.append(f'class="{cls}"')
        self.add(f"<rect {' '.join(attrs)}/>")

    def text(
        self,
        x: float,
        y: float,
        body: str,
        *,
        size: int = 16,
        weight: int | str = 400,
        fill: str = TEXT,
        anchor: str = "start",
        style: str = "",
    ) -> None:
        self.add(
            f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" {style}>{esc(body)}</text>'
        )

    def multiline(
        self,
        x: float,
        y: float,
        lines: list[str],
        *,
        size: int = 14,
        fill: str = TEXT,
        weight: int | str = 400,
        anchor: str = "start",
        leading: int = 18,
    ) -> None:
        for i, line in enumerate(lines):
            self.text(x, y + i * leading, line, size=size, fill=fill, weight=weight, anchor=anchor)

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        stroke: str = "#111827",
        sw: float = 1.8,
        dash: str | None = None,
        marker: str | None = None,
    ) -> None:
        attrs = [
            f'x1="{x1}"',
            f'y1="{y1}"',
            f'x2="{x2}"',
            f'y2="{y2}"',
            f'stroke="{stroke}"',
            f'stroke-width="{sw}"',
            'fill="none"',
        ]
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if marker:
            attrs.append(f'marker-end="url(#{marker})"')
        self.add(f"<line {' '.join(attrs)}/>")


svg = SVG()

svg.add(
    f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <filter id="softShadow" x="-10%" y="-10%" width="120%" height="120%">
    <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#0f172a" flood-opacity="0.10"/>
  </filter>
  <marker id="arrowBlack" markerWidth="11" markerHeight="8" refX="10" refY="4" orient="auto">
    <path d="M0,0 L10,4 L0,8 Z" fill="#111827"/>
  </marker>
  <marker id="arrowBlue" markerWidth="11" markerHeight="8" refX="10" refY="4" orient="auto">
    <path d="M0,0 L10,4 L0,8 Z" fill="{BLUE}"/>
  </marker>
  <marker id="arrowGreen" markerWidth="11" markerHeight="8" refX="10" refY="4" orient="auto">
    <path d="M0,0 L10,4 L0,8 Z" fill="{GREEN}"/>
  </marker>
  <style>
    text {{ font-family: Arial, Helvetica, sans-serif; }}
    .small {{ letter-spacing: 0; }}
  </style>
</defs>
<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>
<rect x="0" y="0" width="{W}" height="{H}" fill="url(#paper)"/>
'''
)


def panel(x: int, y: int, w: int, h: int, color: str, no: str, title: str) -> None:
    svg.rect(x, y, w, h, r=9, fill="#ffffff", stroke=color, sw=1.7, dash="5 3")
    svg.add(f'<circle cx="{x+38}" cy="{y+31}" r="17" fill="{color}"/>')
    svg.text(x + 38, y + 37, no, size=18, weight=700, fill="white", anchor="middle")
    title_size = 18 if len(title) > 22 else 20
    svg.text(x + 68, y + 38, title, size=title_size, weight=700, fill=color)


def item(x: int, y: int, w: int, h: int, label: str, color: str, icon: str = "", font_size: int | None = None) -> None:
    svg.rect(x, y, w, h, r=6, fill="#fbfdff", stroke=color, sw=1.2)
    if icon:
        svg.rect(x + 10, y + 7, 24, h - 14, r=4, fill="#ffffff", stroke=color, sw=1)
        svg.text(x + 22, y + h / 2 + 5, icon, size=12, weight=700, fill=color, anchor="middle")
        tx = x + 47
    else:
        tx = x + 16
    size = font_size if font_size is not None else (11 if len(label) > 28 else 13)
    lines = label.split("\n")
    if len(lines) == 1:
        svg.text(tx, y + h / 2 + 5, label, size=size, weight=500, fill=TEXT)
    else:
        start = y + h / 2 - (len(lines) - 1) * (size * 0.65) + 4
        for i, line in enumerate(lines):
            svg.text(tx, start + i * (size + 2), line, size=size, weight=500, fill=TEXT)


def title_bar() -> None:
    svg.text(W / 2, 41, "OpenRank Visualization Platform: System Architecture", size=38, weight=800, fill=NAVY, anchor="middle")
    svg.text(W / 2, 75, "LLM Open-Source Ecosystem Health Analytics Based on OpenDigger Metrics", size=20, weight=500, fill="#28384d", anchor="middle", style='font-style="italic"')


def monitor(x: int, y: int) -> None:
    svg.rect(x, y, 102, 90, r=7, fill="#f8fafc", stroke=NAVY, sw=4)
    svg.line(x + 6, y + 20, x + 96, y + 20, stroke=NAVY, sw=3)
    svg.add(f'<circle cx="{x+51}" cy="{y+46}" r="11" fill="none" stroke="{NAVY}" stroke-width="4"/>')
    svg.add(f'<path d="M{x+32},{y+73} Q{x+51},{y+52} {x+70},{y+73}" fill="none" stroke="{NAVY}" stroke-width="4"/>')
    svg.add(f'<path d="M{x+44},{y+91} L{x+38},{y+113} L{x+75},{y+113} L{x+69},{y+91}" fill="none" stroke="{NAVY}" stroke-width="4"/>')
    svg.line(x + 31, y + 113, x + 80, y + 113, stroke=NAVY, sw=4)


def db_icon(x: int, y: int, color: str) -> None:
    svg.add(f'<ellipse cx="{x+42}" cy="{y+15}" rx="42" ry="15" fill="{color}"/>')
    svg.add(f'<path d="M{x},{y+15} v70 c0,8 19,15 42,15 s42,-7 42,-15 v-70" fill="{color}" opacity="0.95"/>')
    for dy in (38, 62):
        svg.add(f'<path d="M{x},{y+dy} c0,8 19,15 42,15 s42,-7 42,-15" fill="none" stroke="white" stroke-width="3"/>')


title_bar()

# Panels
panel(12, 96, 212, 620, BLUE, "1", "User & Client")
panel(278, 96, 282, 520, GREEN, "2", "Vue 3 Frontend")
panel(626, 96, 355, 620, BLUE_DARK, "3", "Flask Backend Service")
panel(1055, 96, 307, 620, GREEN, "4", "Data Processing & Storage")
panel(1420, 96, 266, 620, ORANGE, "5", "External Data Sources")

# User/client
monitor(64, 210)
item(28, 352, 180, 64, "Web Browser", BLUE, "WEB")
item(28, 440, 180, 64, "Student / Analyst /\nResearcher", BLUE, "USR", font_size=12)
item(28, 528, 180, 64, "Interactive Dashboard\nAccess", BLUE, "BAR", font_size=12)

# Frontend
fy = 158
for icon, label in [
    ("V", "Vite Build System"),
    ("RT", "Vue Router"),
    ("P", "Pinia State Management"),
    ("API", "API Service Layer"),
    ("EC", "ECharts Visualization Engine"),
]:
    item(291, fy, 252, 36, label, GREEN, icon)
    fy += 43

svg.rect(291, 384, 127, 216, r=8, fill="#fbfffb", stroke=GREEN, sw=1.4)
svg.text(354, 409, "Main Views", size=14, weight=700, fill=GREEN, anchor="middle")
for y, ic, lab in [
    (430, "H", "Home Dashboard"),
    (464, "S", "LLM Ecosystem Summary"),
    (498, "L", "Visual Lab"),
    (532, "*", "Favorites"),
    (566, "+", "Login / Register"),
]:
    svg.text(307, y, ic, size=15, weight=700, fill=GREEN)
    if lab == "LLM Ecosystem Summary":
        svg.text(328, y - 5, "LLM Ecosystem", size=10, fill=TEXT)
        svg.text(328, y + 8, "Summary", size=10, fill=TEXT)
    else:
        svg.text(328, y, lab, size=11, fill=TEXT)

svg.rect(426, 384, 122, 216, r=8, fill="#fbfffb", stroke=GREEN, sw=1.4)
svg.text(487, 409, "Reusable Components", size=13, weight=700, fill=GREEN, anchor="middle")
for y, ic, lab in [
    (434, "LN", "Metric Line Chart"),
    (498, "RD", "Radar Compare"),
    (562, "DB", "Contributor Bar Chart"),
]:
    item(434, y - 22, 104, 48, lab.replace(" ", "\n", 1) if len(lab) > 13 else lab, GREEN, ic, font_size=11)

svg.rect(232, 627, 360, 93, r=8, fill="#fbfff9", stroke=GREEN, sw=1.4, dash="5 3")
svg.multiline(248, 660, ["Receives", "JSON Data", "from Backend"], size=12, fill=GREEN_DARK, weight=600, leading=18)
item(309, 642, 42, 50, "", GREEN, "DOC")
svg.line(356, 667, 379, 667, stroke=GREEN, sw=2, marker="arrowGreen")
item(383, 642, 48, 50, "", GREEN, "CH")
svg.line(437, 667, 462, 667, stroke=GREEN, sw=2, marker="arrowGreen")
svg.multiline(470, 655, ["Renders Charts", "& Dashboard", "Views"], size=12, fill=GREEN_DARK, weight=600, leading=18)

# Backend
item(639, 158, 326, 44, "Application Entry: main.py", BLUE_DARK, "APP")
svg.text(804, 237, "REST APIs", size=16, weight=800, fill=BLUE_DARK, anchor="middle")
api_rows = [
    ("OpenDigger\nAPI Module", "/api/llm/summary"),
    ("LLM Summary /\nReport API", "/api/llm/rank/metrics"),
    ("Contributor Risk API", "/api/llm/report"),
    ("Auth API", "/api/auth/login"),
    ("Auth API (Register)", "/api/auth/register"),
    ("Favorites API", "/api/favorites"),
    ("Contributor Risk API", "/api/health/contributors/risk"),
]
ay = 246
for label, path in api_rows:
    item(642, ay, 180, 34, label, BLUE_DARK, "API", font_size=10 if "\n" in label else 12)
    svg.rect(828, ay, 128, 34, r=5, fill="#f8fbff", stroke=BLUE_DARK, sw=1)
    svg.text(838, ay + 22, path, size=11, fill=TEXT)
    ay += 38

svg.rect(640, 537, 323, 127, r=8, fill="#fbfdff", stroke=BLUE_DARK, sw=1.4)
svg.text(801, 558, "Middleware / Services", size=14, weight=800, fill=BLUE_DARK, anchor="middle")
for x, y, lab, ic in [
    (651, 577, "JWT Authentication", "JWT"),
    (801, 577, "API Rate Limiting", "RL"),
    (651, 629, "CORS", "C"),
    (801, 629, "Request Cache", "DB"),
]:
    item(x, y, 140, 43, lab, BLUE_DARK, ic)

# Data processing
svg.rect(1072, 158, 272, 272, r=8, fill="#fbfffb", stroke=GREEN, sw=1.4)
svg.text(1208, 181, "Data Processing Pipeline", size=15, weight=800, fill=GREEN, anchor="middle")
py = 190
for icon, label in [
    ("DF", "Data Fetcher"),
    ("MU", "Metric Utilities"),
    ("CFG", "Config Loader"),
    ("HS", "Health Score Calculation"),
    ("TS", "Time-Series Aggregation"),
    ("DC", "Data Cache"),
]:
    item(1085, py, 246, 36, label, GREEN, icon)
    py += 39
svg.line(1208, 430, 1208, 450, stroke="#111827", sw=1.8, marker="arrowBlack")
svg.rect(1072, 449, 272, 57, r=7, fill="#fbfff9", stroke=GREEN, sw=1.4, dash="5 3")
svg.text(1208, 474, "Health Score =", size=14, weight=800, fill=GREEN, anchor="middle")
svg.text(1208, 494, "0.5 x OpenRank + 0.3 x Activity + 0.2 x Stability", size=12, fill=GREEN_DARK, anchor="middle")
svg.line(1208, 506, 1208, 542, stroke="#111827", sw=1.8, marker="arrowBlack")
svg.text(1248, 528, "Processed Metrics", size=12, fill=GREEN_DARK, anchor="middle")
svg.text(1248, 545, "(Parsed)", size=12, fill=GREEN_DARK, anchor="middle")

svg.rect(1072, 548, 272, 145, r=8, fill="#fbfffb", stroke=GREEN, sw=1.4)
svg.text(1234, 574, "SQLite Database", size=16, weight=800, fill=GREEN, anchor="middle")
db_icon(1089, 579, GREEN)
for y, ic, lab in [
    (586, "U", "User"),
    (625, "*", "Favorite"),
    (664, "M", "MetricSeries"),
]:
    item(1160, y, 170, 31, lab, GREEN, ic)
    svg.rect(1294, y + 6, 25, 18, r=2, fill="#ffffff", stroke=GREEN, sw=1)
    svg.line(1294, y + 12, 1319, y + 12, stroke=GREEN, sw=0.9)
    svg.line(1303, y + 6, 1303, y + 24, stroke=GREEN, sw=0.9)

# External data
ey = 158
for ic, label in [
    ("OD", "OpenDigger"),
    ("OR", "OpenRank Metrics"),
    ("GH", "GitHub Repository Metadata"),
    ("PA", "Project Activity Metrics"),
    ("DV", "Developer / Contributor Metrics"),
]:
    item(1438, ey, 226, 47, label.replace(" Repository ", " Repository\n") if "Repository" in label else label, ORANGE, ic, font_size=12)
    ey += 57

svg.rect(1438, 482, 226, 190, r=8, fill="#fffaf5", stroke=ORANGE, sw=1.5, dash="5 3")
svg.text(1551, 509, "Metric Ingestion", size=16, weight=800, fill=ORANGE, anchor="middle")
metric_boxes = [
    (1452, 524, 89, "OpenRank"),
    (1548, 524, 90, "Activity"),
    (1452, 564, 89, "Stars"),
    (1548, 564, 90, "Forks"),
    (1452, 604, 89, "Issues"),
    (1548, 604, 90, "Pull Requests"),
    (1452, 644, 186, "Contributors"),
]
for x, y, w, lab in metric_boxes:
    svg.rect(x, y, w, 31, r=5, fill="#fffdf9", stroke=ORANGE, sw=1.2)
    svg.text(x + w / 2, y + 20, lab, size=12, fill=TEXT, anchor="middle")

# Arrows and labels
svg.line(224, 292, 276, 292, stroke="#111827", sw=2, marker="arrowBlack")
svg.multiline(232, 255, ["HTTPS", "Request"], size=12, fill=TEXT, weight=600, leading=18)
svg.line(560, 318, 622, 318, stroke="#111827", sw=2, marker="arrowBlack")
svg.multiline(568, 274, ["REST API", "Requests", "(JSON)"], size=12, fill=TEXT, weight=600, leading=18)
svg.line(981, 300, 1053, 300, stroke="#111827", sw=2, marker="arrowBlack")
svg.multiline(996, 270, ["Process", "Requests"], size=12, fill=TEXT, weight=600, leading=18)
svg.line(1420, 202, 1363, 202, stroke="#111827", sw=2, marker="arrowBlack")
svg.multiline(1367, 319, ["Fetch Data", "(API / Scrape)"], size=12, fill=ORANGE, weight=700, leading=18)

svg.line(1047, 379, 982, 379, stroke=BLUE, sw=1.8, dash="5 4", marker="arrowBlue")
svg.multiline(986, 405, ["Cached Data", "/ DB Results"], size=12, fill=BLUE, weight=700, leading=18)
svg.line(1047, 595, 982, 595, stroke=BLUE, sw=1.8, dash="5 4", marker="arrowBlue")
svg.multiline(986, 623, ["Query / Read", "(Results)"], size=12, fill=BLUE, weight=700, leading=18)
svg.line(626, 467, 562, 467, stroke=BLUE, sw=1.8, dash="5 4", marker="arrowBlue")
svg.multiline(566, 492, ["JSON", "Responses", "(Data, Reports,", "AI Insights,", "Favorites)"], size=12, fill=BLUE, weight=700, leading=17)
svg.line(278, 516, 228, 516, stroke="#111827", sw=2, marker="arrowBlack")
svg.multiline(229, 536, ["Rendered", "Views"], size=12, fill=TEXT, weight=600, leading=18)

# Platform capabilities
svg.rect(12, 740, 1675, 103, r=9, fill="#ffffff", stroke=PURPLE, sw=1.5, dash="5 3")
svg.text(W / 2, 769, "Platform Capabilities", size=20, weight=800, fill=PURPLE, anchor="middle")
caps = [
    ("BAR", "Interactive Visualization"),
    ("AI", "AI Interpretation"),
    ("IMG", "PNG Export"),
    ("PDF", "Report Export"),
    ("*", "Favorites Management"),
    ("SH", "Risk Analysis"),
    ("123", "Health Ranking"),
    ("PIE", "Multi-chart Visual Analytics"),
]
cx = 32
for ic, lab in caps:
    bw = 210 if len(lab) >= 19 else 176
    svg.rect(cx, 777, bw, 50, r=6, fill="#fffefd", stroke=PURPLE, sw=1.2)
    svg.text(cx + 22, 809, ic, size=15, weight=800, fill=PURPLE, anchor="middle")
    svg.text(cx + 52, 807, lab, size=12 if len(lab) >= 19 else 13, weight=600, fill=TEXT)
    cx += bw + 17

# Legend
svg.rect(28, 871, 862, 50, r=6, fill="#ffffff", stroke="#667085", sw=1.2)
svg.text(46, 903, "Legend:", size=13, weight=800, fill=TEXT)
legend_items = [
    (116, BLUE, "Infrastructure / Backend"),
    (316, GREEN, "Data Processing"),
    (486, ORANGE, "Analytics / AI Interpretation"),
    (686, PURPLE, "Visualization / Capabilities"),
]
for lx, color, lab in legend_items:
    svg.rect(lx, 884, 36, 22, r=4, fill="#ffffff", stroke=color, sw=1.4, dash="5 3")
    svg.text(lx + 50, 901, lab, size=12, fill=TEXT)

svg.line(960, 894, 1010, 894, stroke="#111827", sw=2, marker="arrowBlack")
svg.text(1025, 900, "Primary Data Flow", size=12, fill=TEXT)
svg.line(1190, 894, 1240, 894, stroke=BLUE, sw=2, dash="5 4", marker="arrowBlue")
svg.text(1260, 900, "Response / Return Flow", size=12, fill=BLUE, weight=700)
svg.line(1432, 894, 1484, 894, stroke=BLUE, sw=2, dash="5 4", marker="arrowBlue")
svg.line(1484, 894, 1432, 894, stroke=BLUE, sw=2, dash="5 4", marker="arrowBlue")
svg.text(1505, 900, "Bidirectional / Data Access", size=12, fill=TEXT)

svg.add("</svg>\n")

svg_path = OUT / "openrank_architecture_reproduction.svg"
svg_path.write_text("\n".join(svg.parts), encoding="utf-8")

(OUT / "brief.md").write_text(
    """# Brief

图型：系统架构图复现
用途：根据用户提供截图复现 OpenRank Visualization Platform 架构图
核心信息：用户端、Vue 前端、Flask 后端、数据处理与存储、外部数据源之间的数据流
必须包含：五个主模块、REST API 表、数据处理管线、SQLite 数据库、平台能力条、图例
不得包含：未在截图中出现的新数据、新接口、新结论
布局：横向五栏，底部能力条和图例
风格：白底、蓝/绿/橙/紫分区、虚线边框、箭头数据流
输出规格：SVG 源图，PNG/PDF 导出
验收标准：结构完整、文字可读、箭头方向和模块分组与原图一致
""",
    encoding="utf-8",
)

print(svg_path)
