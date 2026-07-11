from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("local-python-figure-mcp")


def _default_allowed_roots() -> list[Path]:
    roots = [Path.home(), Path.cwd()]
    for drive in ("D:/", "E:/"):
        p = Path(drive)
        if p.exists():
            roots.append(p)
    return [p.resolve() for p in roots]


def _allowed_roots() -> list[Path]:
    raw = os.getenv("FIGURE_ALLOWED_ROOTS", "")
    if not raw.strip():
        return _default_allowed_roots()
    roots: list[Path] = []
    for item in raw.split(";"):
        item = item.strip()
        if item:
            roots.append(Path(item).expanduser().resolve())
    return roots or _default_allowed_roots()


def _within_allowed_roots(path: Path) -> bool:
    resolved = path.expanduser().resolve()
    for root in _allowed_roots():
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def _safe_path(raw_path: str, *, must_exist: bool = False) -> Path:
    path = Path(raw_path).expanduser()
    if must_exist and not path.exists():
        raise ValueError(f"Path does not exist: {raw_path}")
    resolved = path.resolve()
    if not _within_allowed_roots(resolved):
        roots = "; ".join(str(root) for root in _allowed_roots())
        raise ValueError(f"Path is outside FIGURE_ALLOWED_ROOTS: {resolved}. Allowed roots: {roots}")
    return resolved


def _slug(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", text.strip()).strip("-")
    return value[:80] or "figure"


def _as_list(value: str | list[str] | None, default: list[str]) -> list[str]:
    if value is None:
        return default
    if isinstance(value, str):
        return [item.strip().lower() for item in value.split(",") if item.strip()]
    return [str(item).strip().lower() for item in value if str(item).strip()]


def _read_table(path: Path, sheet_name: str | None = None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".tsv", ".txt"}:
        return pd.read_csv(path, sep="\t")
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=sheet_name or 0)
    raise ValueError("Supported table formats: .csv, .tsv, .txt, .xlsx, .xls")


def _write_caption(
    output_dir: Path,
    *,
    plot_type: str,
    table_path: Path,
    x: str | None,
    y: str | None,
    hue: str | None,
    title: str | None,
) -> None:
    caption = [
        "# Caption Draft",
        "",
        f"Plot type: `{plot_type}`",
        f"Data source: `{table_path}`",
        f"X: `{x or 'not specified'}`",
        f"Y: `{y or 'not specified'}`",
        f"Group/Hue: `{hue or 'not specified'}`",
        "",
        "统计说明待用户补充：样本量、误差线定义、统计检验、显著性阈值、重复类型。",
    ]
    if title:
        caption.insert(2, f"Title: {title}")
    (output_dir / "caption.md").write_text("\n".join(caption) + "\n", encoding="utf-8")


@mcp.tool()
def inspect_table(table_path: str, sheet_name: str | None = None, max_rows: int = 8) -> dict[str, Any]:
    """Inspect a local CSV/TSV/XLSX table before plotting.

    The tool returns columns, dtypes, row/column counts, missing values, and a small preview.
    It does not infer sample size, p values, or statistical significance.
    """
    path = _safe_path(table_path, must_exist=True)
    df = _read_table(path, sheet_name=sheet_name)
    preview_rows = max(1, min(int(max_rows), 20))
    return {
        "path": str(path),
        "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "columns": list(map(str, df.columns)),
        "dtypes": {str(k): str(v) for k, v in df.dtypes.items()},
        "missing_values": {str(k): int(v) for k, v in df.isna().sum().items()},
        "preview": df.head(preview_rows).to_dict(orient="records"),
        "scientific_boundary": "This inspection does not create or validate statistics. Provide n, error bars, tests, and p values explicitly if they must appear in a paper figure.",
    }


@mcp.tool()
def plot_table(
    table_path: str,
    plot_type: str,
    x: str | None = None,
    y: str | None = None,
    hue: str | None = None,
    value: str | None = None,
    title: str | None = None,
    output_dir: str | None = None,
    formats: str | list[str] | None = None,
    sheet_name: str | None = None,
    width_in: float = 6.0,
    height_in: float = 4.0,
    dpi: int = 300,
    palette: str = "colorblind",
    show_points: bool = False,
) -> dict[str, Any]:
    """Create a reproducible figure from a local table.

    Supported plot_type values: line, scatter, bar, box, violin, heatmap, correlation_heatmap.
    Outputs PNG/SVG/PDF files plus plot_spec.json and caption.md. The tool plots provided data only
    and never fabricates p values, sample sizes, or statistical significance labels.
    """
    path = _safe_path(table_path, must_exist=True)
    df = _read_table(path, sheet_name=sheet_name)
    kind = plot_type.strip().lower().replace("-", "_")
    out_formats = _as_list(formats, ["png", "svg", "pdf"])
    allowed_formats = {"png", "svg", "pdf"}
    bad_formats = sorted(set(out_formats) - allowed_formats)
    if bad_formats:
        raise ValueError(f"Unsupported formats: {bad_formats}. Allowed: png, svg, pdf")

    if output_dir:
        out_dir = _safe_path(output_dir)
    else:
        out_dir = path.parent / "figures" / f"{_slug(kind)}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        if not _within_allowed_roots(out_dir):
            out_dir = Path.cwd() / "figures" / f"{_slug(kind)}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)

    sns.set_theme(context="paper", style="whitegrid", palette=palette, font="Arial")
    fig, ax = plt.subplots(figsize=(float(width_in), float(height_in)), constrained_layout=True)

    if kind == "line":
        if not x or not y:
            raise ValueError("line plot requires x and y")
        sns.lineplot(data=df, x=x, y=y, hue=hue, marker="o", ax=ax)
    elif kind == "scatter":
        if not x or not y:
            raise ValueError("scatter plot requires x and y")
        sns.scatterplot(data=df, x=x, y=y, hue=hue, ax=ax)
    elif kind == "bar":
        if not x or not y:
            raise ValueError("bar plot requires x and y")
        sns.barplot(data=df, x=x, y=y, hue=hue, errorbar=None, ax=ax)
        if show_points:
            sns.stripplot(data=df, x=x, y=y, hue=hue, dodge=bool(hue), color="black", alpha=0.55, ax=ax, legend=False)
    elif kind == "box":
        if not x or not y:
            raise ValueError("box plot requires x and y")
        sns.boxplot(data=df, x=x, y=y, hue=hue, ax=ax)
        if show_points:
            sns.stripplot(data=df, x=x, y=y, hue=hue, dodge=bool(hue), color="black", alpha=0.5, ax=ax, legend=False)
    elif kind == "violin":
        if not x or not y:
            raise ValueError("violin plot requires x and y")
        sns.violinplot(data=df, x=x, y=y, hue=hue, inner="quartile", cut=0, ax=ax)
    elif kind == "heatmap":
        if x and y and value:
            matrix = df.pivot_table(index=y, columns=x, values=value, aggfunc="mean")
        else:
            numeric = df.select_dtypes(include="number")
            if numeric.empty:
                raise ValueError("heatmap without x/y/value requires numeric columns")
            matrix = numeric
        sns.heatmap(matrix, cmap="viridis", ax=ax)
    elif kind == "correlation_heatmap":
        numeric = df.select_dtypes(include="number")
        if numeric.empty:
            raise ValueError("correlation_heatmap requires numeric columns")
        sns.heatmap(numeric.corr(), cmap="vlag", center=0, annot=True, fmt=".2f", ax=ax)
    else:
        raise ValueError("Supported plot_type values: line, scatter, bar, box, violin, heatmap, correlation_heatmap")

    if title:
        ax.set_title(title)
    if x:
        ax.set_xlabel(x)
    if y:
        ax.set_ylabel(y)
    ax.tick_params(axis="x", labelrotation=30)
    sns.despine(fig=fig)

    saved_files: list[str] = []
    base = out_dir / _slug(title or kind)
    for fmt in out_formats:
        target = base.with_suffix(f".{fmt}")
        fig.savefig(target, dpi=int(dpi), bbox_inches="tight")
        saved_files.append(str(target))
    plt.close(fig)

    spec = {
        "table_path": str(path),
        "plot_type": kind,
        "x": x,
        "y": y,
        "hue": hue,
        "value": value,
        "title": title,
        "formats": out_formats,
        "width_in": width_in,
        "height_in": height_in,
        "dpi": dpi,
        "palette": palette,
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "scientific_boundary": "No p values, sample sizes, significance labels, or statistical tests were inferred or fabricated.",
    }
    (out_dir / "plot_spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_caption(out_dir, plot_type=kind, table_path=path, x=x, y=y, hue=hue, title=title)

    return {
        "output_dir": str(out_dir),
        "files": saved_files,
        "spec": str(out_dir / "plot_spec.json"),
        "caption": str(out_dir / "caption.md"),
        "scientific_boundary": spec["scientific_boundary"],
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
