"""Behavioral regression tests for portable project memory, using isolated stores."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("memory", Path(__file__).parents[1] / "scripts/three_layer_memory.py")
memory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(memory)


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="memory-test-")
        self.root = Path(self.temp.name).resolve()
        self.root.relative_to(Path(tempfile.gettempdir()).resolve())
        memory.initialize(self.root, "demo", "示例项目")
        (self.root / "proof.md").write_text("用户规则与执行结果", encoding="utf-8")
        (memory.entry(self.root) / "项目记忆总览.md").write_text("\n\n".join("## " + h + "\n当前规则与证据参见 records。" for h in memory.HEADINGS), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def record(self, **kw):
        r = dict(id="rule-1", key="display-policy", kind="decision", scope="project", project_id="demo",
                 summary="实验6允许 head 展示已有结果", status="confirmed", authority="user",
                 valid_from="2026-10-13T00:00:00+08:00", verified_at="2026-10-13T00:00:00+08:00",
                 sources=[dict(path="proof.md", sha256=memory.digest(self.root / "proof.md"))],
                 aliases=["实验六", "车辆价格预测"], related_ids=[])
        r.update(kw)
        return r

    def put(self, **kw):
        return memory.put_record(self.root, self.record(**kw))

    def test_empty_scaffold_not_ready(self):
        r = memory.audit(self.root)
        self.assertEqual(r["dimensions"]["structure"]["status"], "PASS")
        self.assertNotEqual(r["dimensions"]["content"]["status"], "PASS")
        self.assertFalse(r["can_handoff"])

    def test_confirmed_record_needs_real_evidence(self):
        with self.assertRaises(ValueError):
            self.put(sources=[{"path": "missing.md", "sha256": "0" * 64}])

    def test_path_escape_rejected(self):
        for path in ("../secret.md", "C:/secret.md", "/etc/passwd"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.put(sources=[{"path": path, "sha256": "0" * 64}])

    def test_source_change_is_not_verified(self):
        self.put()
        (self.root / "proof.md").write_text("changed", encoding="utf-8")
        self.assertEqual(memory.audit(self.root)["dimensions"]["evidence"]["status"], "BLOCK")

    def test_duplicate_active_fact_rejected(self):
        self.put()
        with self.assertRaises(ValueError):
            self.put(id="rule-2", summary="冲突版本")

    def test_supersede_preserves_history(self):
        self.put()
        self.put(id="rule-2", summary="仅允许纯展示", supersedes=["rule-1"])
        data = memory.load_records(self.root)
        self.assertEqual(next(r for r in data if r["id"] == "rule-1")["status"], "superseded")
        self.assertEqual(memory.retrieve(self.root, "实验6")["records"][0]["id"], "rule-2")

    def test_lower_authority_cannot_replace_user_rule(self):
        self.put()
        with self.assertRaises(ValueError):
            self.put(id="rule-2", authority="assistant", supersedes=["rule-1"])

    def test_other_project_not_returned(self):
        self.put()
        with self.assertRaises(ValueError):
            self.put(id="foreign", project_id="other", key="other")

    def test_pending_not_default_truth(self):
        self.put(status="pending", sources=[])
        result = memory.retrieve(self.root, "实验6")
        self.assertEqual(result["records"], [])
        self.assertTrue(result["abstain"])

    def test_expired_not_returned(self):
        self.put(valid_until="2026-10-13T01:00:00+08:00")
        self.assertEqual(memory.retrieve(self.root, "实验6", at="2026-10-14T00:00:00+08:00")["records"], [])

    def test_agent_and_machine_isolation(self):
        self.put(scope="agent", agent_id="lab-worker")
        self.assertEqual(memory.retrieve(self.root, "实验6")["records"], [])
        self.assertEqual(len(memory.retrieve(self.root, "实验6", agent_id="lab-worker")["records"]), 1)
        self.put(id="machine-1", key="kernel", scope="machine", machine_id="pc-a")
        self.assertEqual(memory.retrieve(self.root, "kernel", machine_id="pc-b")["records"], [])

    def test_user_isolation(self):
        self.put(scope="user", user_id="u-a")
        self.assertEqual(memory.retrieve(self.root, "实验6", user_id="u-b")["records"], [])

    def test_alias_recall_and_budget(self):
        self.put()
        r = memory.retrieve(self.root, "车辆价格预测", max_chars=900)
        self.assertEqual(r["records"][0]["id"], "rule-1")
        self.assertLessEqual(r["content_chars"], 900)

    def test_unknown_query_abstains(self):
        self.put()
        self.assertTrue(memory.retrieve(self.root, "火星殖民计划")["abstain"])

    def test_immutable_id(self):
        self.put()
        with self.assertRaises(ValueError):
            self.put(summary="silently overwritten")

    def test_missing_related_id_blocks_content(self):
        self.put(related_ids=["missing"])
        self.assertEqual(memory.audit(self.root)["dimensions"]["content"]["status"], "BLOCK")

    def test_split_overview_supported(self):
        entry = memory.entry(self.root)
        manifest = memory.read_json(entry / "memory-manifest.json")
        manifest["overviews"] = []
        for i, heading in enumerate(memory.HEADINGS):
            path = f"docs/project-entry/overview-{i}.md"
            (self.root / path).write_text(f"## {heading}\n有来源的当前事实与路径", encoding="utf-8")
            manifest["overviews"].append(path)
        memory.atomic_json(entry / "memory-manifest.json", manifest)
        (entry / "项目记忆总览.md").unlink()
        self.assertEqual(memory.audit(self.root)["dimensions"]["structure"]["status"], "PASS")

    def test_root_claude_preserved(self):
        with tempfile.TemporaryDirectory(prefix="memory-claude-") as p:
            root = Path(p).resolve()
            root.relative_to(Path(tempfile.gettempdir()).resolve())
            (root / "CLAUDE.md").write_text("已有规则", encoding="utf-8")
            memory.initialize(root, "claude", "CLAUDE 项目")
            self.assertFalse((root / "AGENTS.md").exists())
            self.assertIn("已有规则", (root / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_lock_refuses_parallel_writer(self):
        with memory.writer_lock(self.root):
            with self.assertRaises(ValueError):
                self.put()

    def test_snapshot_detects_partial_sync(self):
        self.put()
        memory.seal(self.root)
        self.assertEqual(memory.verify_snapshot(self.root)["status"], "PASS")
        (memory.entry(self.root) / "项目记忆总览.md").write_text("半同步版本", encoding="utf-8")
        self.assertEqual(memory.verify_snapshot(self.root)["status"], "BLOCK")

    def test_write_invalidates_seal(self):
        self.put()
        memory.seal(self.root)
        self.put(id="r2", key="second")
        self.assertNotEqual(memory.verify_snapshot(self.root)["status"], "PASS")

    def test_seal_does_not_imply_handoff_test(self):
        self.put()
        memory.seal(self.root)
        self.assertFalse(memory.audit(self.root)["can_handoff"])

    def test_stale_source_not_retrieved_as_truth(self):
        self.put()
        (self.root / "proof.md").write_text("changed", encoding="utf-8")
        self.assertTrue(memory.retrieve(self.root, "实验6")["abstain"])

    def test_no_secret_ingestion(self):
        with self.assertRaises(ValueError):
            self.put(summary="password=abcdefghijklmnopqrstuvwxyz12345")

    def test_malformed_utf8_blocks(self):
        (memory.entry(self.root) / "项目记忆总览.md").write_bytes(b"\xff")
        self.assertEqual(memory.audit(self.root)["dimensions"]["structure"]["status"], "BLOCK")

    def test_cli_accepts_old_option_order(self):
        with contextlib.redirect_stdout(io.StringIO()):
            code = memory.main(["--project", str(self.root), "check", "--level", "structure"])
        self.assertEqual(code, 0)

    def test_archive_and_invalidate_are_retrievable_only_as_history(self):
        self.put()
        memory.set_status(self.root, "rule-1", "stale", "规则待重新核验")
        self.assertTrue(memory.retrieve(self.root, "实验6")["abstain"])
        self.assertEqual(len(memory.retrieve(self.root, "实验6", include_history=True)["records"]), 1)

    def test_handoff_result_tied_to_snapshot(self):
        self.put()
        memory.seal(self.root)
        with self.assertRaises(ValueError):
            memory.accept_handoff(self.root, {"snapshot_id": "wrong", "cases": []})

    def test_superseded_source_change_does_not_block_current_truth(self):
        self.put()
        (self.root / "proof2.md").write_text("新规则", encoding="utf-8")
        self.put(id="rule-2", sources=[dict(path="proof2.md", sha256=memory.digest(self.root / "proof2.md"))], supersedes=["rule-1"])
        (self.root / "proof.md").write_text("旧证据变更", encoding="utf-8")
        self.assertNotEqual(memory.audit(self.root)["dimensions"]["evidence"]["status"], "BLOCK")

    def test_pending_cannot_retire_current_rule(self):
        self.put()
        with self.assertRaises(ValueError):
            self.put(id="pending", status="pending", sources=[], verified_at="", supersedes=["rule-1"])
        self.assertEqual(memory.retrieve(self.root, "实验6")["records"][0]["id"], "rule-1")

    def test_future_replacement_and_historical_time(self):
        self.put(valid_from="2020-01-01T00:00:00+08:00")
        self.put(id="future", valid_from="2099-01-01T00:00:00+08:00", supersedes=["rule-1"])
        self.assertEqual(memory.retrieve(self.root, "实验6")["records"][0]["id"], "rule-1")
        self.assertEqual(memory.retrieve(self.root, "实验6", at="2021-01-01T00:00:00+08:00")["records"][0]["id"], "rule-1")

    def test_empty_time_rejected(self):
        with self.assertRaises(ValueError): self.put(valid_from="")

    def test_modified_record_without_source_not_retrieved(self):
        self.put()
        p = memory.entry(self.root) / "records/rule-1.json"
        r = memory.read_json(p); r["sources"] = []; memory.atomic_json(p, r)
        result = memory.retrieve(self.root, "实验6")
        self.assertEqual(result["status"], "BLOCK")
        self.assertTrue(result["abstain"])

    def test_missing_root_cannot_seal(self):
        self.put(); (self.root / "AGENTS.md").unlink()
        with self.assertRaises(ValueError): memory.seal(self.root)

    def test_seal_identifier_tampering_detected(self):
        self.put(); memory.seal(self.root)
        p = memory.entry(self.root) / "sync-snapshot.json"
        r = memory.read_json(p); r["snapshot_id"] = "forged"; memory.atomic_json(p, r)
        self.assertEqual(memory.verify_snapshot(self.root)["status"], "BLOCK")

    def test_root_evidence_included_in_snapshot(self):
        self.put(); memory.seal(self.root)
        (self.root / "proof.md").write_text("changed", encoding="utf-8")
        self.assertEqual(memory.verify_snapshot(self.root)["status"], "BLOCK")

    def test_malformed_record_returns_block(self):
        memory.atomic_json(memory.entry(self.root) / "records/broken.json", [])
        self.assertEqual(memory.audit(self.root)["status"], "BLOCK")
        self.assertEqual(memory.retrieve(self.root, "实验6")["status"], "BLOCK")

    def test_index_summary_corruption_detected(self):
        self.put(); p = memory.entry(self.root) / "memory-index.json"
        r = memory.read_json(p); r["records"][0]["summary"] = "错误索引"; memory.atomic_json(p, r)
        self.assertEqual(memory.audit(self.root)["dimensions"]["content"]["status"], "BLOCK")

    def test_budget_can_choose_later_small_record(self):
        self.put(summary="实验6 " * 2000)
        self.put(id="short", key="short", summary="实验6 简短可用记录")
        r = memory.retrieve(self.root, "实验6", limit=1, max_chars=1000)
        self.assertEqual(r["records"][0]["id"], "short")

    def test_cross_store_conflict_not_treated_as_two_truths(self):
        self.put()
        other = self.root / "other"
        memory.initialize(other, "demo", "另一个副本")
        (other / "proof.md").write_text("另一来源", encoding="utf-8")
        r = self.record(id="conflict", summary="实验6禁止展示", authority="assistant", sources=[dict(path="proof.md", sha256=memory.digest(other / "proof.md"))])
        memory.put_record(other, r)
        output = memory.retrieve(self.root, "实验6", stores=[other])
        self.assertEqual(output["status"], "BLOCK")
        self.assertTrue(output["abstain"])

    def test_external_employee_memory_is_reused_without_other_project(self):
        other = self.root / "employee"
        memory.initialize(other, "employees", "员工资料")
        (other / "proof.md").write_text("方法来源", encoding="utf-8")
        r = self.record(id="agent-method", key="review", scope="agent", agent_id="lab-worker", sources=[dict(path="proof.md", sha256=memory.digest(other / "proof.md"))])
        memory.put_record(other, r)
        self.assertTrue(memory.retrieve(self.root, "实验6", stores=[other])["abstain"])
        self.assertEqual(memory.retrieve(self.root, "实验6", stores=[other], agent_id="lab-worker")["records"][0]["id"], "agent-method")

    def test_same_instant_replacement_has_valid_empty_history(self):
        self.put(); self.put(id="new", supersedes=["rule-1"])
        self.assertEqual(memory.audit(self.root)["dimensions"]["content"]["status"], "PASS")
        memory.seal(self.root)

    def test_replacement_does_not_extend_expired_fact(self):
        self.put(valid_from="2020-01-01T00:00:00+08:00", valid_until="2022-01-01T00:00:00+08:00")
        self.put(id="new", supersedes=["rule-1"])
        self.assertTrue(memory.retrieve(self.root, "实验6", at="2024-01-01T00:00:00+08:00")["abstain"])

    def test_future_superseded_still_conflicts_while_valid(self):
        self.put(valid_from="2020-01-01T00:00:00+08:00")
        self.put(id="future", valid_from="2099-01-01T00:00:00+08:00", supersedes=["rule-1"])
        with self.assertRaises(ValueError):
            self.put(id="overlap", valid_from="2021-01-01T00:00:00+08:00", valid_until="2098-01-01T00:00:00+08:00")

    def test_changed_history_not_blocking_unsealed_current(self):
        self.put()
        (self.root / "proof2.md").write_text("new", encoding="utf-8")
        self.put(id="new", supersedes=["rule-1"], sources=[dict(path="proof2.md", sha256=memory.digest(self.root / "proof2.md"))])
        (self.root / "proof.md").write_text("old changed", encoding="utf-8")
        self.assertEqual(memory.retrieve(self.root, "实验6")["status"], "PASS")

    def test_manifest_nonobject_and_numeric_time_block(self):
        with self.assertRaises(ValueError): self.put(verified_at=17)
        memory.atomic_json(memory.entry(self.root) / "memory-manifest.json", [])
        self.assertEqual(memory.audit(self.root)["status"], "BLOCK")

    def test_snapshot_sources_include_future_without_clock_dependency(self):
        self.put()
        (self.root / "future.md").write_text("future evidence", encoding="utf-8")
        self.put(id="future", key="future", valid_from="2099-01-01T00:00:00+08:00", sources=[dict(path="future.md", sha256=memory.digest(self.root / "future.md"))])
        memory.seal(self.root)
        self.assertIn("future.md", memory.read_json(memory.entry(self.root) / "sync-snapshot.json")["files"])

    def test_incomplete_handoff_file_not_accepted_as_ready(self):
        self.put(); s=memory.seal(self.root)
        memory.atomic_json(memory.entry(self.root)/"handoff-validation.json", dict(snapshot_id=s["snapshot_id"],status="PASS"))
        self.assertFalse(memory.audit(self.root)["can_handoff"])

    def test_managed_tool_missing_blocks_structure(self):
        p=memory.entry(self.root)/"memory-manifest.json"
        m=memory.read_json(p); m["managed_files"]=["scripts/memory.py"]; memory.atomic_json(p,m)
        self.assertEqual(memory.audit(self.root)["dimensions"]["structure"]["status"],"BLOCK")

    def test_generated_cache_does_not_change_snapshot(self):
        self.put(); memory.seal(self.root)
        p=memory.entry(self.root)/"__pycache__/cache.pyc"; p.parent.mkdir(); p.write_bytes(b"cache")
        self.assertEqual(memory.verify_snapshot(self.root)["status"],"PASS")

    def test_corrupt_synced_source_returns_block_without_crash(self):
        self.put(); memory.seal(self.root)
        p=memory.entry(self.root)/"records/rule-1.json"
        r=memory.read_json(p); r["sources"]=[17]; memory.atomic_json(p,r)
        self.assertEqual(memory.audit(self.root)["status"],"BLOCK")
        self.assertEqual(memory.retrieve(self.root,"实验6")["status"],"BLOCK")
        self.assertEqual(memory.verify_snapshot(self.root)["status"],"BLOCK")


if __name__ == "__main__":
    unittest.main()
