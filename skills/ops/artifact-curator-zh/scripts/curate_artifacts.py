#!/usr/bin/env python
"""Build a read-only artifact index and stale-candidate report.

The script never moves or deletes files. It only writes CSV/Markdown reports.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


TEXT_EXTS = {".md", ".txt", ".log", ".m", ".py", ".ps1", ".yaml", ".yml", ".json", ".csv"}
RESULT_EXTS = {".csv", ".mat", ".xlsx", ".xls"}
LOG_NAME_HINTS = ("log", "stderr", "stdout", "ping", "watchdog", "tmp", "temp")
FAIL_HINTS = ("失败", "红灯", "证伪", "放弃", "不再", "hard stop", "stop", "failed", "failure", "stale")
SKILL_PREFIX_RE = re.compile(
    r"^(?:research-coach-zh|research-iteration-audit-zh|project-dev-zh|workflow-forge-zh|knowledge-digest-zh|paper-writing-zh|[a-z-]+-zh)_",
    re.IGNORECASE,
)
LEGACY_FLAT_FIRST = re.compile(r"^\d{8}_\d{6}_")
DATE_PREFIX_RE = re.compile(r"^\d{8}_\d{6}_")
DATE_SUFFIX_RE = re.compile(r"[_-]\d{8}_\d{6}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan project artifacts and report stale candidates.")
    parser.add_argument("--root", default=".", help="Project root to scan.")
    parser.add_argument("--dirs", nargs="*", default=None, help="Relative directories to scan.")
    parser.add_argument("--output", default=None, help="Output directory. Defaults to skill-outputs/_curation/<timestamp>.")
    parser.add_argument("--stale-days", type=int, default=45, help="Age threshold for log/temp stale candidates.")
    parser.add_argument("--include-logs", action="store_true", help="Include common root-level logs.")
    parser.add_argument("--include-data-step", action="store_true", help="Include PlatEMO Data_step* directories in inventory.")
    parser.add_argument("--max-text-bytes", type=int, default=12000, help="Bytes to read from text files for hints.")
    return parser.parse_args()


def relpath(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def default_scan_dirs(root: Path, include_logs: bool, include_data_step: bool) -> list[Path]:
    candidates = [
        root / "skill-outputs",
        root / "资料" / "exp_start" / "steps",
        root / "资料" / "exp_start" / "results",
        root / "资料" / "exp_start" / "Tracing",
    ]
    if include_data_step:
        platemo = root / "PlatEMO-master" / "PlatEMO"
        if platemo.exists():
            candidates.extend(p for p in platemo.glob("Data_step*") if p.is_dir())
    if include_logs:
        candidates.append(root)
    return [p for p in candidates if p.exists()]


def reference_files(root: Path) -> list[Path]:
    files = [
        root / "AGENTS.md",
        root / "资料" / "exp_start" / "AI接班手册.md",
        root / "资料" / "exp_start" / "项目统一认知.md",
        root / "资料" / "exp_start" / "PlatEMO工作流细化.md",
        root / "资料" / "exp_start" / "Tracing" / "机制注册表.md",
        root / "资料" / "exp_start" / "Tracing" / "结论记录.md",
        root / "资料" / "exp_start" / "Tracing" / "问题记录.md",
        root / "资料" / "exp_start" / "Tracing" / "上下文压缩记录.md",
    ]
    return [p for p in files if p.exists()]


def load_reference_text(root: Path) -> str:
    chunks: list[str] = []
    for path in reference_files(root):
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    return "\n".join(chunks)


def read_head(path: Path, max_bytes: int) -> str:
    if path.suffix.lower() not in TEXT_EXTS:
        return ""
    try:
        data = path.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="ignore").lower()
    except OSError:
        return ""


def detect_step(text: str) -> str:
    match = re.search(r"step\s*[-_ ]?(\d+)", text, flags=re.IGNORECASE)
    return match.group(1) if match else ""


def detect_version(text: str) -> str:
    patterns = [r"\bG(\d+)\b", r"\bv(\d+[a-z]?)\b", r"\bround\s*([A-Za-z0-9]+)\b"]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)
    return ""


def topic_key(path: Path) -> str:
    stem = path.stem
    stem = DATE_PREFIX_RE.sub("", stem)
    stem = DATE_SUFFIX_RE.sub("", stem)
    stem = SKILL_PREFIX_RE.sub("", stem)
    stem = re.sub(r"[_-]run\d+$", "", stem, flags=re.IGNORECASE)
    stem = re.sub(r"[_-]seed\d+$", "", stem, flags=re.IGNORECASE)
    stem = re.sub(r"[_-]\d{8,}$", "", stem)
    return stem.lower() or path.stem.lower()


def skill_outputs_bucket(rel: str) -> str:
    """skill-outputs 第一层：legacy-flat（时间戳开头）、保留目录、或 skill 名分桶。"""
    rel_posix = rel.replace("\\", "/")
    parts = rel_posix.split("/")
    if len(parts) < 2 or parts[0] != "skill-outputs":
        return ""
    seg = parts[1]
    if seg in ("_curation", "_archive"):
        return seg
    if LEGACY_FLAT_FIRST.match(seg):
        return "legacy-flat"
    return seg


def delivery_topic_key(path: Path, rel: str) -> str:
    """同一次 skill 交付（子目录）内多文件共享 topic，便于 stale 判定。"""
    rel_posix = rel.replace("\\", "/")
    bucket = skill_outputs_bucket(rel_posix)
    parts = rel_posix.split("/")
    if bucket in ("_curation", "_archive", ""):
        return topic_key(path)
    if bucket == "legacy-flat":
        return topic_key(path)
    if len(parts) >= 4:
        run = DATE_PREFIX_RE.sub("", parts[2])
        run = DATE_SUFFIX_RE.sub("", run)
        return f"{bucket}/{run.lower()}"
    if len(parts) == 3:
        return f"{bucket}/{topic_key(path)}"
    return topic_key(path)


def detect_domain(rel: str, name: str) -> str:
    hay = f"{rel} {name}".lower()
    if "research" in hay or "step" in hay or "实验" in hay or "算法" in hay:
        return "research"
    if "paper" in hay or "论文" in hay:
        return "paper"
    if "handoff" in hay or "接班" in hay or "统一认知" in hay:
        return "handoff"
    if "workflow" in hay or "工作流" in hay:
        return "workflow"
    if "knowledge" in hay or "知识" in hay:
        return "knowledge"
    if "log" in hay or "stderr" in hay or "watchdog" in hay:
        return "ops-log"
    return "general"


def detect_type(path: Path, rel: str) -> str:
    ext = path.suffix.lower()
    name = path.name.lower()
    if any(h in name for h in LOG_NAME_HINTS) or ext == ".log":
        return "log"
    if ext in RESULT_EXTS:
        if "summary" in name or "table" in name or "delta" in name:
            return "result-table"
        return "result-artifact"
    if ext == ".md":
        return "report"
    if ext in {".m", ".py", ".ps1"}:
        return "script"
    return "artifact"


def is_referenced(rel: str, path: Path, ref_text: str) -> bool:
    rel_posix = rel.replace("\\", "/")
    return rel_posix in ref_text or path.name in ref_text


def collect_files(root: Path, scan_dirs: list[Path], include_logs: bool) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for base in scan_dirs:
        if not base.exists():
            continue
        if include_logs and base == root:
            iterator = (p for p in root.iterdir() if p.is_file())
        else:
            iterator = (p for p in base.rglob("*") if p.is_file())
        for path in iterator:
            if any(part in {".git", "__pycache__", ".venv", "node_modules", "_curation", "_archive"} for part in path.parts):
                continue
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(path)
    return sorted(files, key=lambda p: str(p).lower())


def classify(records: list[dict], stale_days: int) -> None:
    by_topic: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_topic[record["topic_key"]].append(record)

    latest_by_topic: dict[str, dict] = {}
    for key, rows in by_topic.items():
        latest_by_topic[key] = max(rows, key=lambda r: r["mtime_ts"])

    now_ts = datetime.now(timezone.utc).timestamp()
    stale_seconds = stale_days * 86400

    for record in records:
        reasons: list[str] = []
        latest = latest_by_topic[record["topic_key"]]
        name = record["name"].lower()
        head = record.get("text_head", "")

        if record["referenced"]:
            curation_class = "active-reference"
            action = "keep"
            reasons.append("referenced_by_key_docs")
        elif record["artifact_type"].startswith("result"):
            curation_class = "result-artifact"
            action = "keep_in_place"
            reasons.append("result_file")
        elif any(h in name or h in head for h in FAIL_HINTS):
            curation_class = "historical-evidence"
            action = "keep_or_archive_with_context"
            reasons.append("failure_or_boundary_evidence")
        elif latest is not record and record["path"].startswith("skill-outputs/"):
            curation_class = "stale-superseded-candidate"
            action = "archive_candidate"
            reasons.append(f"newer_same_topic:{latest['name']}")
        elif record["artifact_type"] == "log" and now_ts - record["mtime_ts"] > stale_seconds:
            curation_class = "temporary-or-log"
            action = "archive_candidate"
            reasons.append(f"log_older_than_{stale_days}_days")
        elif latest is record and record["path"].startswith("skill-outputs/"):
            curation_class = "latest-topic-output"
            action = "keep_index"
            reasons.append("latest_in_topic")
        else:
            curation_class = "unknown-review"
            action = "manual_review"
            reasons.append("insufficient_signal")

        record["curation_class"] = curation_class
        record["stale_action"] = action
        record["stale_reason"] = "; ".join(reasons)
        record.pop("text_head", None)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, records: list[dict], root: Path) -> None:
    class_counts = Counter(r["curation_class"] for r in records)
    domain_counts = Counter(r["domain"] for r in records)
    stale = [r for r in records if r["stale_action"] == "archive_candidate"]
    stale = sorted(stale, key=lambda r: (r["curation_class"], -int(r["size_bytes"])))[:50]

    lines = [
        "# Artifact Curation Summary",
        "",
        f"- Root: `{root}`",
        f"- Total files scanned: `{len(records)}`",
        f"- Archive candidates: `{sum(1 for r in records if r['stale_action'] == 'archive_candidate')}`",
        "",
        "## Class Counts",
        "",
    ]
    for key, value in class_counts.most_common():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Domain Counts", ""])
    for key, value in domain_counts.most_common():
        lines.append(f"- `{key}`: {value}")
    bucket_counts = Counter((r.get("skill_outputs_bucket") or "") for r in records)
    if any(bucket_counts.values()):
        lines.extend(["", "## skill_outputs_bucket (under skill-outputs/)", ""])
        for key, value in sorted(bucket_counts.items(), key=lambda kv: (-kv[1], kv[0])):
            label = key if key else "(non-skill-outputs)"
            lines.append(f"- `{label}`: {value}")
    lines.extend(["", "## Top Archive Candidates", ""])
    if stale:
        for record in stale:
            lines.append(f"- `{record['path']}` | {record['stale_reason']}")
    else:
        lines.append("- No archive candidates detected.")
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "Review `stale_candidates.csv`. Do not move or delete files until the user confirms the plan.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output:
        out_dir = Path(args.output).resolve()
    elif (root / "skill-outputs").exists():
        out_dir = root / "skill-outputs" / "_curation" / timestamp
    else:
        out_dir = root / "_artifact_curation" / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    scan_dirs = [root / d for d in args.dirs] if args.dirs else default_scan_dirs(root, args.include_logs, args.include_data_step)
    ref_text = load_reference_text(root)
    files = collect_files(root, scan_dirs, args.include_logs)

    records: list[dict] = []
    for path in files:
        try:
            stat = path.stat()
        except OSError:
            continue
        rel = relpath(path, root)
        head = read_head(path, args.max_text_bytes)
        record = {
            "path": rel,
            "name": path.name,
            "domain": detect_domain(rel, path.name),
            "artifact_type": detect_type(path, rel),
            "extension": path.suffix.lower(),
            "size_bytes": stat.st_size,
            "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "mtime_ts": stat.st_mtime,
            "step": detect_step(rel),
            "version": detect_version(rel),
            "skill_outputs_bucket": skill_outputs_bucket(rel),
            "topic_key": delivery_topic_key(path, rel),
            "referenced": is_referenced(rel, path, ref_text),
            "text_head": head,
        }
        records.append(record)

    classify(records, args.stale_days)
    records = sorted(records, key=lambda r: (r["domain"], r["step"], r["topic_key"], r["path"]))

    fields = [
        "path",
        "name",
        "domain",
        "artifact_type",
        "curation_class",
        "stale_action",
        "stale_reason",
        "extension",
        "size_bytes",
        "mtime",
        "step",
        "version",
        "skill_outputs_bucket",
        "topic_key",
        "referenced",
    ]
    write_csv(out_dir / "artifact_inventory.csv", records, fields)
    write_csv(out_dir / "classification_plan.csv", records, fields)
    write_csv(out_dir / "stale_candidates.csv", [r for r in records if r["stale_action"] == "archive_candidate"], fields)
    write_summary(out_dir / "artifact_summary.md", records, root)

    print(f"[artifact-curator] scanned={len(records)} archive_candidates={sum(1 for r in records if r['stale_action'] == 'archive_candidate')}")
    print(f"[artifact-curator] output={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
