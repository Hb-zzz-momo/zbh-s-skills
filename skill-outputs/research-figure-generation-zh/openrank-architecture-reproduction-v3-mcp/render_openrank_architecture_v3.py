from __future__ import annotations

import re
from pathlib import Path


OUT = Path(__file__).resolve().parent
ICON_DIR = OUT / "node_modules" / "lucide-static" / "icons"
W, H = 1690, 939

NAVY = "#0d1b2f"
BLUE = "#1558ad"
BLUE_DARK = "#0d3f87"
GREEN = "#16763a"
GREEN_DARK = "#0b6b32"
ORANGE = "#ef6a1a"
PURPLE = "#5b2a97"
TEXT = "#101828"
ICON_BLACK = "#0f172a"
MUTED = "#344054"
SOFT = "#f8fbff"

ICON_ALIASES = {
    "APP": "file-code-2",
    "API": "globe-2",
    "BAR": "bar-chart-3",
    "C": "globe",
    "CFG": "settings",
    "CH": "bar-chart-3",
    "DB": "database",
    "DC": "server",
    "DF": "cloud-download",
    "DOC": "file-text",
    "DV": "users",
    "EC": "pie-chart",
    "GH": "git-branch",
    "HS": "heart-pulse",
    "IMG": "image",
    "JWT": "shield-check",
    "L": "flask-conical",
    "LN": "line-chart",
    "M": "line-chart",
    "MU": "wrench",
    "OD": "search",
    "OR": "badge-check",
    "P": "store",
    "PA": "activity",
    "PDF": "file-output",
    "PIE": "pie-chart",
    "RD": "radar",
    "RL": "gauge",
    "RT": "route",
    "S": "bar-chart-3",
    "SH": "shield-alert",
    "TS": "trending-up",
    "U": "user",
    "USR": "users",
    "V": "zap",
    "WEB": "globe",
    "+": "user-plus",
    "*": "star",
    "123": "trophy",
    "AI": "brain",
}


def icon_inner(name: str) -> str | None:
    path = ICON_DIR / f"{name}.svg"
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    match = re.search(r"<svg\b[^>]*>\s*(.*?)\s*</svg>", raw, flags=re.S)
    return match.group(1) if match else None


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

    def icon(self, name: str, x: float, y: float, size: float, *, color: str = TEXT, sw: float = 2.0) -> None:
        inner = icon_inner(name)
        if not inner:
            self.text(x + size / 2, y + size * 0.72, name[:2].upper(), size=max(8, int(size * 0.38)), fill=color, anchor="middle", weight=700)
            return
        scale = size / 24
        self.add(
            f'<g transform="translate({x} {y}) scale({scale})" fill="none" '
            f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">'
            f"{inner}</g>"
        )


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
'''
)


def panel(x: int, y: int, w: int, h: int, color: str, no: str, title: str) -> None:
    svg.rect(x, y, w, h, r=9, fill="#ffffff", stroke=color, sw=1.7, dash="5 3")
    svg.add(f'<circle cx="{x+38}" cy="{y+31}" r="17" fill="{color}"/>')
    svg.text(x + 38, y + 37, no, size=18, weight=700, fill="white", anchor="middle")
    title_size = 17 if len(title) >= 21 else 20
    svg.text(x + 68, y + 38, title, size=title_size, weight=700, fill=color)


def item(x: int, y: int, w: int, h: int, label: str, color: str, icon: str = "", font_size: int | None = None) -> None:
    svg.rect(x, y, w, h, r=6, fill="#fbfdff", stroke=color, sw=1.2)
    if icon:
        icon_name = ICON_ALIASES.get(icon, icon.lower())
        if not label and w <= 60:
            box = min(31, h - 10)
            bx = x + (w - box) / 2
            by = y + (h - box) / 2
            svg.rect(bx, by, box, box, r=5, fill="#ffffff", stroke=color, sw=1)
            svg.icon(icon_name, bx + 6, by + 6, box - 12, color=color, sw=2.2)
            tx = x + w + 6
        else:
            size_icon = min(27, h - 13)
            bx = x + 12
            by = y + (h - size_icon) / 2
            svg.icon(icon_name, bx, by, size_icon, color=ICON_BLACK, sw=2.2)
            tx = x + 48
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
    svg.rect(x, y, 104, 98, r=8, fill="#f8fafc", stroke=NAVY, sw=4)
    svg.icon("monitor", x + 20, y + 14, 64, color=NAVY, sw=1.8)
    svg.icon("circle-user-round", x + 34, y + 33, 36, color=NAVY, sw=2.1)


def db_icon(x: int, y: int, color: str) -> None:
    svg.add(f'<ellipse cx="{x+36}" cy="{y+15}" rx="36" ry="15" fill="{color}"/>')
    svg.add(f'<path d="M{x},{y+15} v70 c0,8 17,15 36,15 s36,-7 36,-15 v-70" fill="{color}" opacity="0.95"/>')
    for dy in (38, 62):
        svg.add(f'<path d="M{x},{y+dy} c0,8 17,15 36,15 s36,-7 36,-15" fill="none" stroke="white" stroke-width="3"/>')


title_bar()

# Panels
panel(12, 96, 212, 620, BLUE, "1", "User & Client")
panel(278, 96, 282, 520, GREEN, "2", "Vue 3 Frontend")
panel(626, 96, 355, 620, BLUE_DARK, "3", "Flask Backend Service")
panel(1055, 96, 295, 620, GREEN, "4", "Data Processing & Storage")
panel(1428, 96, 258, 620, ORANGE, "5", "External Data Sources")

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
    (430, "house", "Home Dashboard"),
    (464, "bar-chart-3", "LLM Ecosystem Summary"),
    (498, "flask-conical", "Visual Lab"),
    (532, "star", "Favorites"),
    (566, "user-plus", "Login / Register"),
]:
    svg.icon(ic, 301, y - 16, 20, color=GREEN, sw=2.3)
    if lab == "LLM Ecosystem Summary":
        svg.text(328, y - 5, "LLM Ecosystem", size=10, fill=TEXT)
        svg.text(328, y + 8, "Summary", size=10, fill=TEXT)
    else:
        svg.text(328, y, lab, size=11, fill=TEXT)

svg.rect(426, 384, 122, 216, r=8, fill="#fbfffb", stroke=GREEN, sw=1.4)
svg.text(487, 402, "Reusable", size=11, weight=700, fill=GREEN, anchor="middle")
svg.text(487, 416, "Components", size=11, weight=700, fill=GREEN, anchor="middle")
for y, ic, lab in [
    (450, "LN", "Metric Line Chart"),
    (508, "RD", "Radar Compare"),
    (566, "DB", "Contributor Bar Chart"),
]:
    wrapped = {
        "Metric Line Chart": "Metric\nLine Chart",
        "Radar Compare": "Radar\nCompare",
        "Contributor Bar Chart": "Contributor\nBar Chart",
    }[lab]
    item(434, y - 22, 104, 48, wrapped, GREEN, ic, font_size=10)

svg.rect(232, 627, 360, 93, r=8, fill="#fbfff9", stroke=GREEN, sw=1.4, dash="5 3")
svg.multiline(247, 656, ["Receives", "JSON Data", "from Backend"], size=11, fill=GREEN_DARK, weight=600, leading=15)
item(329, 642, 42, 50, "", GREEN, "DOC")
svg.line(376, 667, 390, 667, stroke=GREEN, sw=2, marker="arrowGreen")
item(394, 642, 48, 50, "", GREEN, "CH")
svg.line(448, 667, 466, 667, stroke=GREEN, sw=2, marker="arrowGreen")
svg.multiline(474, 656, ["Renders Charts", "Dashboard", "Views"], size=11, fill=GREEN_DARK, weight=600, leading=15)

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
    svg.text(838, ay + 22, path, size=9 if len(path) > 22 else 11, fill=TEXT)
    ay += 38

svg.rect(640, 537, 323, 140, r=8, fill="#fbfdff", stroke=BLUE_DARK, sw=1.4)
svg.text(801, 558, "Middleware / Services", size=14, weight=800, fill=BLUE_DARK, anchor="middle")
for x, y, lab, ic, fs in [
    (651, 577, "JWT\nAuthentication", "JWT", 11),
    (801, 577, "API Rate\nLimiting", "RL", 11),
    (651, 629, "CORS", "C", 12),
    (801, 629, "Request Cache", "DB", 11),
]:
    item(x, y, 142, 43, lab, BLUE_DARK, ic, font_size=fs)

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

svg.rect(1072, 548, 272, 160, r=8, fill="#fbfffb", stroke=GREEN, sw=1.4)
svg.text(1234, 574, "SQLite Database", size=16, weight=800, fill=GREEN, anchor="middle")
db_icon(1088, 584, GREEN)
for y, ic, lab in [
    (586, "U", "User"),
    (625, "*", "Favorite"),
    (664, "M", "MetricSeries"),
]:
    item(1172, y, 158, 31, lab, GREEN, ic, font_size=11)
    svg.rect(1305, y + 7, 20, 17, r=2, fill="#ffffff", stroke=GREEN, sw=0.9)
    svg.line(1305, y + 13, 1325, y + 13, stroke=GREEN, sw=0.8)
    svg.line(1312, y + 7, 1312, y + 24, stroke=GREEN, sw=0.8)

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

svg.rect(1438, 482, 226, 205, r=8, fill="#fffaf5", stroke=ORANGE, sw=1.5, dash="5 3")
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
svg.rect(226, 247, 49, 38, r=3, fill="#ffffff", stroke="#ffffff", sw=0)
svg.multiline(250, 260, ["HTTPS", "Request"], size=11, fill=TEXT, weight=600, leading=14, anchor="middle")
svg.line(560, 318, 622, 318, stroke="#111827", sw=2, marker="arrowBlack")
svg.rect(563, 266, 60, 52, r=3, fill="#ffffff", stroke="#ffffff", sw=0)
svg.multiline(593, 280, ["REST API", "Requests", "(JSON)"], size=10, fill=TEXT, weight=600, leading=13, anchor="middle")
svg.line(981, 300, 1053, 300, stroke="#111827", sw=2, marker="arrowBlack")
svg.rect(990, 262, 58, 39, r=3, fill="#ffffff", stroke="#ffffff", sw=0)
svg.multiline(1019, 276, ["Process", "Requests"], size=10, fill=TEXT, weight=600, leading=13, anchor="middle")
svg.line(1428, 202, 1352, 202, stroke="#111827", sw=2, marker="arrowBlack")
svg.rect(1355, 292, 70, 40, r=4, fill="#ffffff", stroke="#ffffff", sw=0)
svg.multiline(1390, 305, ["Fetch Data", "(API/Scrape)"], size=11, fill=ORANGE, weight=700, leading=14, anchor="middle")

svg.line(1047, 379, 982, 379, stroke=BLUE, sw=1.8, dash="5 4", marker="arrowBlue")
svg.rect(986, 393, 65, 43, r=3, fill="#ffffff", stroke="#ffffff", sw=0)
svg.multiline(1018, 407, ["Cached Data", "DB Results"], size=10, fill=BLUE, weight=700, leading=13, anchor="middle")
svg.line(1047, 595, 982, 595, stroke=BLUE, sw=1.8, dash="5 4", marker="arrowBlue")
svg.rect(986, 611, 65, 43, r=3, fill="#ffffff", stroke="#ffffff", sw=0)
svg.multiline(1018, 625, ["Query / Read", "(Results)"], size=10, fill=BLUE, weight=700, leading=13, anchor="middle")
svg.line(626, 467, 562, 467, stroke=BLUE, sw=1.8, dash="5 4", marker="arrowBlue")
svg.rect(563, 480, 61, 89, r=3, fill="#ffffff", stroke="#ffffff", sw=0)
svg.multiline(594, 493, ["JSON", "Responses", "Data", "Reports", "AI Insights", "Favorites"], size=9, fill=BLUE, weight=700, leading=12, anchor="middle")
svg.line(278, 516, 228, 516, stroke="#111827", sw=2, marker="arrowBlack")
svg.rect(226, 523, 50, 39, r=3, fill="#ffffff", stroke="#ffffff", sw=0)
svg.multiline(251, 537, ["Rendered", "Views"], size=10, fill=TEXT, weight=600, leading=13, anchor="middle")

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
    svg.icon(ICON_ALIASES.get(ic, ic.lower()), cx + 14, 791, 24, color=PURPLE, sw=2.2)
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
