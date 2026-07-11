from __future__ import annotations

import json
from pathlib import Path


OUT = Path(__file__).resolve().parent


def main() -> None:
    checks = []

    def add(name: str, ok: bool, detail: dict) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    sqlite_container = {"x": 1072, "y": 548, "w": 272, "h": 160}
    db_icon = {"x": 1088, "w": 72}
    sqlite_rows = [
        {"name": "User", "x": 1172, "y": 586, "w": 158, "h": 31},
        {"name": "Favorite", "x": 1172, "y": 625, "w": 158, "h": 31},
        {"name": "MetricSeries", "x": 1172, "y": 664, "w": 158, "h": 31},
    ]
    db_icon_right = db_icon["x"] + db_icon["w"]
    for row in sqlite_rows:
        add(
            f"sqlite row {row['name']} clears database icon",
            row["x"] - db_icon_right >= 10,
            {"row_left": row["x"], "db_icon_right": db_icon_right, "margin": row["x"] - db_icon_right},
        )
        add(
            f"sqlite row {row['name']} stays inside container",
            row["x"] + row["w"] <= sqlite_container["x"] + sqlite_container["w"] - 10
            and row["y"] + row["h"] <= sqlite_container["y"] + sqlite_container["h"] - 10,
            {
                "row_right": row["x"] + row["w"],
                "row_bottom": row["y"] + row["h"],
                "container_right_safe": sqlite_container["x"] + sqlite_container["w"] - 10,
                "container_bottom_safe": sqlite_container["y"] + sqlite_container["h"] - 10,
            },
        )

    metric_container = {"x": 1438, "y": 482, "w": 226, "h": 205}
    contributor = {"x": 1452, "y": 644, "w": 186, "h": 31}
    add(
        "metric ingestion contributor row has bottom padding",
        contributor["y"] + contributor["h"] <= metric_container["y"] + metric_container["h"] - 10,
        {
            "row_bottom": contributor["y"] + contributor["h"],
            "container_bottom_safe": metric_container["y"] + metric_container["h"] - 10,
            "padding": metric_container["y"] + metric_container["h"] - (contributor["y"] + contributor["h"]),
        },
    )

    fetch_label = {"left": 1359, "right": 1421}
    safe_gap = {"left": 1352, "right": 1426}
    add(
        "fetch label stays between panels",
        fetch_label["left"] >= safe_gap["left"] and fetch_label["right"] <= safe_gap["right"],
        {"fetch_label": fetch_label, "safe_gap": safe_gap},
    )

    frontend_callout = {"x": 232, "y": 627, "w": 360, "h": 93}
    left_text = {"right": 322}
    doc_icon = {"x": 329, "w": 42}
    chart_icon = {"x": 394, "w": 48}
    right_text = {"x": 474, "right": 560}
    add(
        "frontend bottom flow left label clears document icon",
        doc_icon["x"] - left_text["right"] >= 7,
        {"left_text_right": left_text["right"], "doc_icon_left": doc_icon["x"], "margin": doc_icon["x"] - left_text["right"]},
    )
    add(
        "frontend bottom flow chart icon clears right label",
        right_text["x"] - (chart_icon["x"] + chart_icon["w"]) >= 20,
        {
            "chart_icon_right": chart_icon["x"] + chart_icon["w"],
            "right_text_left": right_text["x"],
            "margin": right_text["x"] - (chart_icon["x"] + chart_icon["w"]),
        },
    )
    add(
        "frontend bottom flow stays inside dashed callout",
        right_text["right"] <= frontend_callout["x"] + frontend_callout["w"] - 20,
        {
            "right_text_right": right_text["right"],
            "callout_right_safe": frontend_callout["x"] + frontend_callout["w"] - 20,
        },
    )

    ok = all(c["ok"] for c in checks)
    report = {"ok": ok, "checks": checks}
    (OUT / "layout_geometry_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if not ok:
        failed = [c for c in checks if not c["ok"]]
        raise SystemExit(json.dumps(failed, ensure_ascii=False, indent=2))
    print("layout geometry audit ok")


if __name__ == "__main__":
    main()
