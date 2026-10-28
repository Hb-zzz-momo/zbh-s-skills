import csv
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/curate_artifacts.py"
MIGRATE = SCRIPT.with_name("auto_migrate_skill_outputs.py")


def test_curation_reads_project_documents_and_writes_outside_legacy_bucket(tmp_path):
    documents = ["docs/guides/入门.md", "reports/结果.md", "比赛资料/官方说明.md", "skill-outputs/project-dev-zh/旧文档.md"]
    for relative in documents:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative, encoding="utf-8")
    # The existing reports boundary is reused; prior inventories must not index themselves.
    old_inventory = tmp_path / "reports/artifact-curation/old/artifact_summary.md"
    old_inventory.parent.mkdir(parents=True)
    old_inventory.write_text("old inventory", encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp_path)], capture_output=True, check=False)
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    inventories = list((tmp_path / "reports/artifact-curation").glob("*/artifact_inventory.csv"))
    assert len(inventories) == 1
    with inventories[0].open(encoding="utf-8-sig", newline="") as handle:
        paths = {row["path"] for row in csv.DictReader(handle)}
    assert set(documents) <= paths
    assert old_inventory.relative_to(tmp_path).as_posix() not in paths
    assert not (tmp_path / "skill-outputs/_curation").exists()
    for relative in documents:
        assert (tmp_path / relative).read_text(encoding="utf-8") == relative


def test_curation_without_existing_document_directory_uses_project_reviews(tmp_path):
    result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp_path)], capture_output=True, check=False)
    assert result.returncode == 0
    assert list((tmp_path / "docs/reviews/artifact-curation").glob("*/artifact_inventory.csv"))
    assert not (tmp_path / "skill-outputs").exists()


def test_legacy_migration_can_use_an_explicit_existing_review_location(tmp_path):
    original = tmp_path / "skill-outputs/20261029_000001_project-dev-zh_guide.md"
    original.parent.mkdir()
    original.write_text("historical guide", encoding="utf-8")
    output = tmp_path / "文档/评审/迁移记录"
    result = subprocess.run(
        [sys.executable, str(MIGRATE), "--root", str(tmp_path), "--apply", "--no-rewrite-md", "--output", str(output)],
        capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert list(output.glob("*.csv"))
    assert not (tmp_path / "docs").exists()
    assert (original.parent / "project-dev-zh" / original.name).read_text(encoding="utf-8") == "historical guide"


def test_legacy_migration_dryrun_and_default_chinese_review_owner(tmp_path):
    original = tmp_path / "skill-outputs/20261029_000001_project-dev-zh_guide.md"
    original.parent.mkdir()
    original.write_text("historical guide", encoding="utf-8")
    review = tmp_path / "文档/评审"
    review.mkdir(parents=True)
    command = [sys.executable, str(MIGRATE), "--root", str(tmp_path)]
    before = {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    dry = subprocess.run(command, capture_output=True, check=False)
    assert dry.returncode == 0
    assert before == {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    applied = subprocess.run(command + ["--apply", "--no-rewrite-md"], capture_output=True, check=False)
    assert applied.returncode == 0
    assert list((review / "artifact-migration").glob("*.csv"))
    assert not (tmp_path / "docs").exists()
