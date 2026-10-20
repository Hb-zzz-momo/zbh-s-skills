"""Isolated behavioral tests; never inspect or clean a real project."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "closeout_artifacts.py"


class CloseoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "owned").mkdir()
        (self.root / "protected").mkdir()
        self.write("protected/final.csv", b"final")
        self.write("owned/cache.tmp", b"cache")
        self.write("owned/model.pt", b"weights")
        self.write("protected/model.pt", b"weights")
        self.write("validation.json", b'{"status":"PASS"}')
        self.plan = {
            "root": str(self.root), "owned_roots": ["owned"],
            "protected": ["protected"], "workers_stopped": True,
            "validation": {"path": "validation.json", "sha256": self.digest("validation.json")},
            "items": [self.item("owned/cache.tmp", "temporary", generator="render task")],
        }
        self.plan_path = self.root / "plan.json"
        self.journal = self.root / "cleanup.jsonl"

    def write(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def digest(self, name):
        return hashlib.sha256((self.root / name).read_bytes()).hexdigest()

    def item(self, name, reason, **extra):
        return dict(path=name, size=(self.root / name).stat().st_size,
                    sha256=self.digest(name), reason=reason, **extra)

    def run_cli(self, apply=False, journal=True):
        self.plan_path.write_text(json.dumps(self.plan), encoding="utf-8")
        args = [sys.executable, "-B", str(SCRIPT), "--plan", str(self.plan_path)]
        if apply:
            args.append("--apply")
        if journal:
            args.extend(["--journal", str(self.journal)])
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
        return result, json.loads(result.stdout)

    def assert_rejected(self):
        before = {p.relative_to(self.root): p.read_bytes()
                  for p in self.root.rglob("*") if p.is_file() and p != self.plan_path}
        result, out = self.run_cli(apply=True)
        self.assertNotEqual(result.returncode, 0, out)
        self.assertEqual(out["logical_bytes_removed"], 0)
        self.assertFalse(self.journal.exists())
        for rel, data in before.items():
            self.assertEqual((self.root / rel).read_bytes(), data)

    def test_default_dryrun_changes_nothing(self):
        result, out = self.run_cli()
        self.assertEqual(result.returncode, 0, out)
        self.assertEqual(out["status"], "dry_run")
        self.assertEqual(out["planned_bytes"], 5)
        self.assertEqual(out["logical_bytes_removed"], 0)
        self.assertTrue((self.root / "owned/cache.tmp").exists())
        self.assertFalse(self.journal.exists())

    def test_apply_deletes_only_exact_candidates_and_durable_journal(self):
        self.plan["items"].append(self.item("owned/model.pt", "duplicate", keeper="protected/model.pt"))
        result, out = self.run_cli(apply=True)
        self.assertEqual(result.returncode, 0, out)
        self.assertEqual(out["logical_bytes_removed"], 12)
        self.assertFalse((self.root / "owned/cache.tmp").exists())
        self.assertFalse((self.root / "owned/model.pt").exists())
        self.assertEqual((self.root / "protected/model.pt").read_bytes(), b"weights")
        rows = [json.loads(line) for line in self.journal.read_text().splitlines()]
        self.assertEqual(rows[0]["event"], "plan")
        self.assertEqual(rows[0]["root"], str(self.root))
        self.assertEqual(rows[-1]["event"], "result")
        self.assertEqual(sum(row["event"] == "deleted" for row in rows), 2)

    def test_mixed_invalid_plan_deletes_nothing(self):
        self.plan["items"].append(self.item("owned/model.pt", "temporary", generator="train"))
        self.assert_rejected()

    def test_escape_and_absolute_candidates(self):
        for path in ["../outside.tmp", str(self.root / "owned/cache.tmp"), "C:relative.tmp", "/owned/cache.tmp"]:
            with self.subTest(path=path):
                self.plan["items"][0]["path"] = path
                self.assert_rejected()

    def test_protected_subtree_and_unowned_candidates(self):
        self.plan["protected"].append("owned")
        self.assert_rejected()
        self.plan["protected"] = ["protected"]
        self.plan["items"] = [self.item("validation.json", "temporary", generator="test")]
        self.assert_rejected()

    def test_stale_hash_size_and_duplicate_paths(self):
        original = copy.deepcopy(self.plan)
        for field, value in [("sha256", "0" * 64), ("size", 999), ("size", True)]:
            with self.subTest(field=field, value=value):
                self.plan = copy.deepcopy(original)
                self.plan["items"][0][field] = value
                self.assert_rejected()
        self.plan = original
        self.plan["items"].append(copy.deepcopy(self.plan["items"][0]))
        self.assert_rejected()

    def test_keeper_deleted_cycle_missing_and_different_content(self):
        self.write("owned/copy.pt", b"weights")
        original = copy.deepcopy(self.plan)
        for keeper in ["owned/model.pt", "owned/missing.pt", "protected/final.csv"]:
            with self.subTest(keeper=keeper):
                self.plan["items"] = [self.item("owned/model.pt", "duplicate", keeper=keeper)]
                self.assert_rejected()
        self.plan = original
        self.plan["items"] = [self.item("owned/model.pt", "duplicate", keeper="owned/copy.pt"),
                              self.item("owned/copy.pt", "duplicate", keeper="owned/model.pt")]
        self.assert_rejected()

    def test_unknown_reason_extensions_and_empty_generator(self):
        for reason, generator in [("old", "render"), ("temporary", "")]:
            self.plan["items"] = [self.item("owned/cache.tmp", reason, generator=generator)]
            self.assert_rejected()
        for suffix in [".pt", ".csv", ".py", ".ipynb", ".html", ".json", ".xyz"]:
            with self.subTest(suffix=suffix):
                name = "owned/artifact" + suffix
                self.write(name, b"x")
                self.plan["items"] = [self.item(name, "temporary", generator="test")]
                self.assert_rejected()

    def test_unsupported_cache_error_locates_candidate_and_guides_correction(self):
        self.write("owned/render.cache", b"cache")
        self.plan["items"].append(self.item("owned/render.cache", "temporary", generator="renderer"))
        result, out = self.run_cli(apply=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("owned/render.cache", out["error"])
        self.assertIn(".tmp", out["error"])
        self.assertIn(".png", out["error"])
        self.assertEqual(out["logical_bytes_removed"], 0)
        self.assertTrue((self.root / "owned/cache.tmp").exists())
        self.assertTrue((self.root / "owned/render.cache").exists())
        self.assertFalse(self.journal.exists())

    def test_worker_and_validation_gates(self):
        self.plan["workers_stopped"] = False
        self.assert_rejected()
        self.plan["workers_stopped"] = True
        self.write("validation.json", b'{"status":"FAIL"}')
        self.plan["validation"]["sha256"] = self.digest("validation.json")
        self.assert_rejected()
        self.write("validation.json", b'{"status":"PASS"}')
        self.assert_rejected()  # recorded hash is now stale

    def test_empty_protection_root_ownership_and_files_only(self):
        original = copy.deepcopy(self.plan)
        for update in [{"protected": []}, {"owned_roots": ["."]},
                       {"owned_roots": ["owned/cache.tmp"]}, {"root": self.root.anchor}]:
            with self.subTest(update=update):
                self.plan = dict(copy.deepcopy(original), **update)
                self.assert_rejected()
        self.plan = original
        self.plan["items"][0]["path"] = "owned"
        self.assert_rejected()

    def test_apply_requires_new_safe_journal(self):
        result, _ = self.run_cli(apply=True, journal=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.root / "owned/cache.tmp").exists())
        self.journal.write_text("existing", encoding="utf-8")
        result, _ = self.run_cli(apply=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.journal.read_text(), "existing")
        self.assertTrue((self.root / "owned/cache.tmp").exists())

    def test_journal_escape_and_candidate_collision(self):
        self.journal = self.root.parent / (self.root.name + "-outside.jsonl")
        self.assert_rejected()
        self.journal = self.root / "owned/cache.tmp"
        result, out = self.run_cli(apply=True)
        self.assertNotEqual(result.returncode, 0, out)
        self.assertEqual(self.journal.read_bytes(), b"cache")

    def test_plan_and_validation_are_automatically_protected(self):
        self.write("owned/validation.json", b'{"status":"PASS"}')
        self.write("protected/validation.json", b'{"status":"PASS"}')
        self.plan["validation"] = dict(path="owned/validation.json", sha256=self.digest("owned/validation.json"))
        self.plan["items"] = [self.item("owned/validation.json", "duplicate", keeper="protected/validation.json")]
        self.assert_rejected()
        self.plan_path = self.root / "owned/plan.json"
        self.plan["items"] = [dict(path="owned/plan.json", size=0, sha256="0" * 64,
                                   reason="duplicate", keeper="protected/validation.json")]
        self.assert_rejected()

    def test_registered_generated_views_and_cautioned_validation(self):
        self.write("validation.json", b'{"status":"PASS_WITH_NONBLOCKING_CAUTIONS"}')
        self.plan["validation"]["sha256"] = self.digest("validation.json")
        self.write("owned/view.png", b"generated image")
        self.plan["items"] = [self.item("owned/view.png", "temporary", generator="render_report.py")]
        result, out = self.run_cli(apply=True)
        self.assertEqual(result.returncode, 0, out)
        self.assertFalse((self.root / "owned/view.png").exists())

    def test_repeated_apply_never_removes_new_files(self):
        result, _ = self.run_cli(apply=True)
        self.assertEqual(result.returncode, 0)
        self.write("owned/new.tmp", b"new")
        self.journal = self.root / "second.jsonl"
        self.assert_rejected()

    def test_symlink_and_ancestor_escape(self):
        link = self.root / "owned/link"
        try:
            link.symlink_to(self.root / "protected", target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest("symlink unavailable: " + str(exc))
        self.plan["items"] = [self.item("owned/link/model.pt", "duplicate", keeper="protected/model.pt")]
        self.assert_rejected()

    def test_os_resolved_alias_is_rejected_before_any_delete(self):
        spec = importlib.util.spec_from_file_location("closeout_alias", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.plan_path.write_text(json.dumps(self.plan), encoding="utf-8")
        candidate = self.root / "owned/cache.tmp"
        original_resolve = Path.resolve

        def resolve_alias(path, *args, **kwargs):
            if path == candidate:
                return self.root / "protected/final.csv"
            return original_resolve(path, *args, **kwargs)

        # Simulates an OS canonicalization mismatch; this is not a native 8.3 test.
        with patch.object(Path, "resolve", resolve_alias):
            out = module.execute(self.plan_path, apply=True, journal_path=self.journal)
        self.assertEqual(out["status"], "rejected")
        self.assertIn("alias", out["error"])
        self.assertEqual(out["logical_bytes_removed"], 0)
        self.assertEqual(candidate.read_bytes(), b"cache")
        self.assertEqual((self.root / "protected/final.csv").read_bytes(), b"final")
        self.assertFalse(self.journal.exists())

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_windows_junction(self):
        link = self.root / "owned/junction"
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(self.root / "protected")],
                                capture_output=True)
        if result.returncode:
            self.skipTest("junction unavailable")
        self.addCleanup(lambda: os.rmdir(link) if link.exists() else None)
        self.plan["owned_roots"] = ["owned/junction"]
        self.assert_rejected()

    def test_runtime_failure_is_partial_and_stops(self):
        spec = importlib.util.spec_from_file_location("closeout", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.write("owned/second.tmp", b"second")
        self.plan["items"].append(self.item("owned/second.tmp", "temporary", generator="test"))
        self.plan_path.write_text(json.dumps(self.plan), encoding="utf-8")
        original_unlink = Path.unlink

        def fail_second(path, *args, **kwargs):
            if path.name == "second.tmp":
                raise PermissionError("injected file lock")
            return original_unlink(path, *args, **kwargs)

        with patch.object(Path, "unlink", fail_second):
            out = module.execute(self.plan_path, apply=True, journal_path=self.journal)
        self.assertEqual(out["status"], "partial")
        self.assertEqual(out["logical_bytes_removed"], 5)
        self.assertTrue((self.root / "owned/second.tmp").exists())
        self.assertEqual(json.loads(self.journal.read_text().splitlines()[-1])["status"], "partial")

    def test_keeper_is_rechecked_before_each_delete(self):
        spec = importlib.util.spec_from_file_location("closeout_dynamic", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.plan["items"].append(self.item("owned/model.pt", "duplicate", keeper="protected/model.pt"))
        self.plan_path.write_text(json.dumps(self.plan), encoding="utf-8")
        original_unlink = Path.unlink

        def change_keeper(path, *args, **kwargs):
            result = original_unlink(path, *args, **kwargs)
            self.write("protected/model.pt", b"changed")
            return result

        with patch.object(Path, "unlink", change_keeper):
            out = module.execute(self.plan_path, apply=True, journal_path=self.journal)
        self.assertEqual(out["status"], "partial")
        self.assertEqual(out["logical_bytes_removed"], 5)
        self.assertTrue((self.root / "owned/model.pt").exists())


if __name__ == "__main__":
    unittest.main()
