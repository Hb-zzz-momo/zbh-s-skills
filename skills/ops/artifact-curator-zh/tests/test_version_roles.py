"""Version roles and recovery copies must survive inventory heuristics."""
import csv
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/curate_artifacts.py"
spec = importlib.util.spec_from_file_location("version_curation", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_default_inventory_discovers_topic_roles_and_keeps_frozen_history(tmp_path):
    files = ["活动宣传/编辑稿/推文.md", "活动宣传/发布快照/推文_v1.0.md", "活动宣传/历史版本/推文_v0.9.log", "主持稿/并列用途/上午场/发布快照/主持稿_v1.0.md", "主持稿/并列用途/下午场/编辑稿/主持稿.md"]
    for relative in files:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("isolated example", encoding="utf-8")
        os.utime(path, (time.time() - 86400 * 100, time.time() - 86400 * 100))
    output = tmp_path / "制作与核对记录/文件整理"
    result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp_path), "--output", str(output)], capture_output=True)
    assert result.returncode == 0, result.stderr
    with (output / "artifact_inventory.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = {r["path"]: r for r in csv.DictReader(stream)}
    assert set(files) <= rows.keys()
    assert rows[files[0]]["version_role"] == "编辑稿"
    assert rows[files[1]]["version_role"] == "发布快照"
    assert rows[files[2]]["version_role"] == "历史版本"
    assert rows[files[3]]["parallel_use"] == "上午场"
    assert rows[files[4]]["parallel_use"] == "下午场"
    assert all(rows[p]["stale_action"] != "archive_candidate" for p in files)
    assert not (tmp_path / "skill-outputs").exists()


def test_recovery_backup_with_old_log_name_is_not_a_stale_candidate():
    records = [dict(path="独立备份/2026-01-01/old.log", name="old.log", topic_key="old", mtime_ts=0,
                    artifact_type="log", referenced=False, text_head="", version_role="独立备份", parallel_use="")]
    module.classify(records, stale_days=45)
    assert records[0]["stale_action"] == "keep_recovery_copy"


def test_scoped_daily_inventory_does_not_scan_other_topics(tmp_path):
    for topic in ("活动宣传", "费用核算"):
        path = tmp_path / topic / "编辑稿/当前.md"
        path.parent.mkdir(parents=True)
        path.write_text(topic, encoding="utf-8")
    output = tmp_path / "制作与核对记录/本次"
    result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp_path), "--dirs", "活动宣传", "--output", str(output)], capture_output=True)
    assert result.returncode == 0
    with (output / "artifact_inventory.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert [r["path"] for r in rows] == ["活动宣传/编辑稿/当前.md"]


def test_production_log_can_be_reviewed_without_reclassifying_snapshot():
    records = [dict(path=f"宣传/{role}/log.txt", name="log.txt", topic_key=role, mtime_ts=0,
                    artifact_type="log", referenced=False, text_head="", version_role=role, parallel_use="")
               for role in ("制作与核对记录", "发布快照")]
    module.classify(records, 45)
    assert records[0]["stale_action"] == "archive_candidate"
    assert records[1]["stale_action"] == "keep_in_place"
