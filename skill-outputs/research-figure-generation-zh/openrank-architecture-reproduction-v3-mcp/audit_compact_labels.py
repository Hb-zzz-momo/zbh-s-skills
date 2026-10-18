from __future__ import annotations

from pathlib import Path


OUT = Path(__file__).resolve().parent
SOURCE = OUT / "render_openrank_architecture_v3.py"


REQUIRED_SNIPPETS = {
    "Reusable component Metric Line Chart is wrapped": '"Metric\\nLine Chart"',
    "Reusable component Radar Compare is wrapped": '"Radar\\nCompare"',
    "Reusable component Contributor Bar Chart is wrapped": '"Contributor\\nBar Chart"',
    "Middleware JWT Authentication is wrapped": '"JWT\\nAuthentication"',
    "Middleware API Rate Limiting is wrapped": '"API Rate\\nLimiting"',
    "MetricSeries uses a real icon alias": '"M": "line-chart"',
}


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    missing = [name for name, snippet in REQUIRED_SNIPPETS.items() if snippet not in text]
    report = {
        "ok": not missing,
        "checked": list(REQUIRED_SNIPPETS),
        "missing": missing,
    }
    (OUT / "compact_label_audit.json").write_text(
        __import__("json").dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if missing:
        raise SystemExit(f"compact label audit failed: {missing}")
    print("compact label audit ok")


if __name__ == "__main__":
    main()
