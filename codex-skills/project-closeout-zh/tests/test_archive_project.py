"""Meaningful safety and recovery checks; no third-party dependencies."""
import importlib.util
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "archive_project.py"
SPEC = importlib.util.spec_from_file_location("archive_project", SCRIPT)
archive = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(archive)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "source"
        self.root.mkdir()
        self.unit = self.root / "工程"
        (self.unit / "Library").mkdir(parents=True)
        (self.unit / "Library" / "cache.bin").write_bytes(b"cached\x00bytes")
        (self.unit / "Assets").mkdir()
        (self.unit / "Assets" / "story.txt").write_text("原始资料", encoding="utf-8")
        (self.unit / "Empty").mkdir()
        (self.root / "retained.txt").write_text("stay", encoding="utf-8")
        self.dest = self.root / "归档"
        self.inv = self.base / "inventory.json"
        self.plan_path = self.base / "plan.json"
        self.journal = self.base / "apply.jsonl"
        self.recovery = self.base / "rollback.jsonl"

    def freeze(self, moves=None):
        inventory = archive.collect(self.root)
        archive.exclusive_json(self.inv, inventory)
        self.plan = {"version": 1, "root": str(self.root), "destination": str(self.dest),
                     "inventory": str(self.inv), "inventory_sha256": archive.digest(self.inv)["sha256"],
                     "moves": moves or [{"source": "工程", "destination": "工程_完整"}]}
        self.save_plan()
        return inventory

    def save_plan(self):
        self.plan_path.write_text(json.dumps(self.plan, ensure_ascii=False), encoding="utf-8")

    def apply(self):
        return archive.apply_plan(self.plan_path, self.journal)

    def assert_rejected(self):
        with self.assertRaises((archive.ArchiveError, OSError)):
            self.apply()
        self.assertTrue(self.unit.is_dir())
        self.assertFalse(self.journal.exists())

    def test_scan_includes_cache_and_empty_directories(self):
        inv = self.freeze()
        self.assertIn("工程/Library/cache.bin", [x["path"] for x in inv["files"]])
        self.assertIn("工程/Empty", inv["empty_directories"])

    def test_whole_directory_apply_verify_and_rollback(self):
        self.freeze()
        result = self.apply()
        self.assertEqual(result["moved_units"], 1)
        self.assertFalse(self.unit.exists())
        self.assertTrue((self.dest / "工程_完整" / "Empty").is_dir())
        checked = archive.verify_plan(self.plan_path)
        self.assertEqual(checked["moves"][0]["state"], "archived")
        self.assertEqual(checked["files_outside_plan"], 1)
        archive.rollback(self.journal, self.recovery)
        self.assertTrue(self.unit.is_dir())
        self.assertEqual(archive.verify_plan(self.plan_path)["moves"][0]["state"], "original")
        self.assertTrue(self.dest.is_dir())

    def test_tampered_source_rejects_before_any_move(self):
        self.freeze()
        (self.unit / "Library" / "cache.bin").write_bytes(b"changed")
        self.assert_rejected()

    def test_added_member_rejects(self):
        self.freeze()
        (self.unit / "new.txt").write_text("new", encoding="utf-8")
        self.assert_rejected()

    def test_removed_empty_directory_rejects(self):
        self.freeze()
        (self.unit / "Empty").rmdir()
        self.assert_rejected()

    def test_all_moves_preflight_before_first_move(self):
        self.freeze([{"source": "工程", "destination": "工程"}, {"source": "retained.txt", "destination": "stay.txt"}])
        (self.root / "retained.txt").write_text("changed", encoding="utf-8")
        self.assert_rejected()

    def test_inventory_tamper_rejects(self):
        self.freeze()
        with self.inv.open("a", encoding="utf-8") as stream:
            stream.write(" ")
        self.assert_rejected()

    def test_target_collision_rejects(self):
        self.freeze()
        (self.dest / "工程_完整").mkdir(parents=True)
        self.assert_rejected()

    def test_case_alias_collision_rejects(self):
        self.freeze([{"source": "工程", "destination": "Bundle"}])
        self.dest.mkdir()
        (self.dest / "bundle").write_bytes(b"keep")
        self.assert_rejected()

    def test_path_escape_and_windows_aliases_reject(self):
        self.freeze()
        for value in ("../outside", "C:/outside", "/outside", "a//b", "a/../b", "AUX.txt", "COM¹.txt", "folder.", "a:b", "a "):
            with self.subTest(value=value):
                self.plan["moves"][0]["destination"] = value
                self.save_plan()
                self.assert_rejected()

    def test_overlapping_sources_reject(self):
        self.freeze([{"source": "工程", "destination": "whole"}, {"source": "工程/Assets", "destination": "assets"}])
        self.assert_rejected()

    def test_overlapping_targets_reject(self):
        self.freeze([{"source": "工程", "destination": "whole"}, {"source": "retained.txt", "destination": "whole/file"}])
        self.assert_rejected()

    def test_destination_inside_moved_source_rejects(self):
        self.freeze()
        self.plan["destination"] = str(self.unit / "archive")
        self.save_plan()
        self.assert_rejected()

    def test_output_never_overwrites(self):
        self.freeze()
        before = self.inv.read_bytes()
        with self.assertRaises(archive.ArchiveError):
            archive.exclusive_json(self.inv, {})
        self.assertEqual(self.inv.read_bytes(), before)

    def test_symlink_recorded_not_followed_and_move_rejected(self):
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "secret").write_bytes(b"not in inventory")
        link = self.unit / "linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("OS did not permit symlink creation")
        inv = self.freeze()
        self.assertEqual(inv["skipped_links"][0]["path"], "工程/linked")
        self.assertFalse(any("secret" in x["path"] for x in inv["files"]))
        self.assert_rejected()

    def test_reparse_attribute_is_link(self):
        class Info:
            st_mode = 0o100644
            st_file_attributes = 0x400
        self.assertTrue(archive.is_link(Info()))

    def test_symlink_ancestor_rejects(self):
        link = self.base / "link"
        try:
            link.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("OS did not permit symlink creation")
        with self.assertRaises(archive.ArchiveError):
            archive.collect(link)

    def test_cross_volume_rejected_before_move(self):
        self.freeze()
        with patch.object(archive, "volume_id", side_effect=[12345, 54321]):
            self.assert_rejected()

    def test_rollback_after_rename_without_done_record(self):
        self.freeze()
        real_rename = os.rename
        def rename_then_interrupt(src, dst):
            real_rename(src, dst)
            raise KeyboardInterrupt("simulated interruption after rename")
        with patch.object(archive.os, "rename", side_effect=rename_then_interrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.apply()
        self.assertFalse(self.unit.exists())
        events = [x["event"] for x in archive.read_journal(self.journal)]
        self.assertIn("intent", events)
        self.assertNotIn("done", events)
        archive.rollback(self.journal, self.recovery)
        self.assertTrue(self.unit.exists())

    def test_partial_move_failure_and_repeat_recovery(self):
        self.freeze([{"source": "工程", "destination": "工程"}, {"source": "retained.txt", "destination": "retained.txt"}])
        real_rename = os.rename
        calls = []
        def fail_second(src, dst):
            calls.append(str(src))
            if len(calls) == 2:
                raise OSError("simulated second-move failure")
            return real_rename(src, dst)
        with patch.object(archive.os, "rename", side_effect=fail_second):
            with self.assertRaises(OSError):
                self.apply()
        self.assertFalse(self.unit.exists())
        self.assertTrue((self.root / "retained.txt").exists())
        archive.rollback(self.journal, self.recovery)
        second = self.base / "rollback-again.jsonl"
        result = archive.rollback(self.journal, second)
        self.assertEqual(result["restored_units"], 0)
        self.assertEqual(result["already_original_units"], 2)

    def test_rollback_detects_tampered_archive_and_source_conflict(self):
        self.freeze()
        self.apply()
        target = self.dest / "工程_完整" / "Library" / "cache.bin"
        old = target.read_bytes()
        target.write_bytes(b"tampered")
        with self.assertRaises(archive.ArchiveError):
            archive.rollback(self.journal, self.recovery)
        self.assertFalse(self.recovery.exists())
        target.write_bytes(old)
        self.unit.mkdir()
        with self.assertRaises(archive.ArchiveError):
            archive.rollback(self.journal, self.recovery)

    def test_empty_directory_unit(self):
        self.freeze([{"source": "工程/Empty", "destination": "empty"}])
        self.apply()
        self.assertTrue((self.dest / "empty").is_dir())
        archive.verify_plan(self.plan_path)
        archive.rollback(self.journal, self.recovery)
        self.assertTrue((self.unit / "Empty").is_dir())

    def test_independent_archive_directory(self):
        self.dest = self.base / "independent"
        self.freeze()
        self.apply()
        archive.verify_plan(self.plan_path)
        archive.rollback(self.journal, self.recovery)

    def test_absolute_path_aliases_reject(self):
        self.freeze()
        self.plan["destination"] = str(self.root / "archive.")
        self.save_plan()
        self.assert_rejected()

    def test_rollback_torn_last_line_is_recoverable(self):
        self.freeze()
        self.apply()
        with self.journal.open("a", encoding="utf-8") as stream:
            stream.write('{"event":"incomplete')
        archive.rollback(self.journal, self.recovery)
        self.assertTrue(self.unit.exists())

    def test_rollback_interruption_resumes_from_original_journal(self):
        self.freeze([{"source": "工程", "destination": "whole"}, {"source": "retained.txt", "destination": "stay.txt"}])
        self.apply()
        real_rename = os.rename
        def rename_then_interrupt(src, dst):
            real_rename(src, dst)
            raise KeyboardInterrupt("interrupted restore")
        with patch.object(archive.os, "rename", side_effect=rename_then_interrupt):
            with self.assertRaises(KeyboardInterrupt):
                archive.rollback(self.journal, self.recovery)
        self.assertTrue((self.root / "retained.txt").exists())
        second = self.base / "rollback-resumed.jsonl"
        result = archive.rollback(self.journal, second)
        self.assertEqual(result["restored_units"], 1)
        self.assertTrue(self.unit.exists())

    def test_rollback_rejects_modified_fingerprints_in_journal(self):
        self.freeze()
        self.apply()
        records = archive.read_journal(self.journal)
        for record in records:
            if record.get("event") == "intent":
                record["expected"]["files"]["Library/cache.bin"]["sha256"] = "0" * 64
        self.journal.write_text("".join(json.dumps(x) + "\n" for x in records), encoding="utf-8")
        with self.assertRaisesRegex(archive.ArchiveError, "frozen inventory"):
            archive.rollback(self.journal, self.recovery)
        self.assertFalse(self.recovery.exists())

    @unittest.skipUnless(os.name == "nt", "Windows alias comparison is platform-specific")
    def test_windows_resolved_alias_is_rejected(self):
        target = self.root
        realpath = archive.ordinary_realpath
        def alias(path):
            if archive.path_key(path) == archive.path_key(target):
                return str(self.base / "DIFFERENT_CANONICAL_NAME")
            return realpath(path)
        with patch.object(archive, "ordinary_realpath", side_effect=alias):
            with self.assertRaisesRegex(archive.ArchiveError, "resolved path alias"):
                archive.collect(target)

    @unittest.skipUnless(os.name == "nt", "Windows device namespace is platform-specific")
    def test_external_extended_namespace_still_rejected(self):
        with self.assertRaisesRegex(archive.ArchiveError, "device namespace"):
            archive.collect("\\\\?\\" + str(self.root))
        with self.assertRaisesRegex(archive.ArchiveError, "device namespace"):
            archive.io_path("\\\\?\\" + str(self.root))

    def test_hash_boundaries_match_complete_bytes(self):
        path = self.unit / "binary.bin"
        for size in (0, 1, 65535, 65536, 65537, 2 * 1024 * 1024 + 37):
            with self.subTest(size=size):
                payload = (bytes(range(256)) * (size // 256 + 1))[:size]
                path.write_bytes(payload)
                self.assertEqual(archive.digest(path), {"size": size, "sha256": hashlib.sha256(payload).hexdigest()})

    def test_hash_readinto_reuses_one_small_buffer(self):
        path = self.unit / "binary.bin"
        payload = bytes(range(256)) * 1024 + b"tail"
        path.write_bytes(payload)
        real_open = archive.io_open
        buffers = []
        class Reader:
            def __enter__(self):
                self.stream = real_open(path, "rb", buffering=0)
                return self
            def __exit__(self, *args):
                self.stream.close()
            def fileno(self):
                return self.stream.fileno()
            def readinto(self, buffer):
                buffers.append((id(buffer), len(buffer)))
                return self.stream.readinto(buffer)
        with patch.object(archive, "io_open", return_value=Reader()):
            result = archive.digest(path)
        self.assertEqual(result["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertGreater(len(buffers), 2)
        self.assertEqual(len(set(buffers)), 1)
        self.assertEqual(buffers[0][1], 65536)

    def test_hash_memoryerror_records_file_phase_and_does_not_skip(self):
        path = self.unit / "binary.bin"
        path.write_bytes(b"data")
        real_open = archive.io_open
        class Reader:
            def __enter__(self):
                self.stream = real_open(path, "rb", buffering=0)
                return self
            def __exit__(self, *args):
                self.stream.close()
            def fileno(self):
                return self.stream.fileno()
            def readinto(self, buffer):
                raise MemoryError("injected read failure")
        with patch.object(archive, "io_open", return_value=Reader()):
            with self.assertRaises(archive.HashMemoryError) as caught:
                archive.digest(path)
        self.assertEqual(caught.exception.details["path"], str(path))
        self.assertEqual(caught.exception.details["phase"], "readinto")
        self.assertEqual(caught.exception.details["bytes_hashed"], 0)
        with patch.object(archive, "digest", side_effect=caught.exception):
            with self.assertRaises(archive.HashMemoryError):
                archive.collect(self.unit)
            output = self.base / "not-created.json"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = archive.main(["scan", "--root", str(self.unit), "--out", str(output)])
        self.assertEqual(code, 2)
        self.assertIn("MemoryError", stderr.getvalue())
        self.assertFalse(output.exists())

    def test_hash_premature_eof_cannot_return_success_fingerprint(self):
        path = self.unit / "binary.bin"
        path.write_bytes(bytes(range(256)) * 513 + b"tail")
        real_open = archive.io_open
        class Reader:
            def __init__(self, chunks):
                self.chunks = chunks
            def __enter__(self):
                self.stream = real_open(path, "rb", buffering=0)
                return self
            def __exit__(self, *args):
                self.stream.close()
            def fileno(self):
                return self.stream.fileno()
            def readinto(self, buffer):
                if not self.chunks:
                    return 0
                self.chunks -= 1
                return self.stream.readinto(buffer)
        for chunks in (0, 1):
            with self.subTest(successful_chunks_before_early_eof=chunks):
                with patch.object(archive, "io_open", return_value=Reader(chunks)):
                    with self.assertRaisesRegex(archive.ArchiveError, "Incomplete file read"):
                        archive.digest(path)


@unittest.skipUnless(os.name == "nt", "Real Windows long-path integration test")
class WindowsLongPathTests(unittest.TestCase):
    def test_real_long_paths_scan_apply_verify_rollback(self):
        # Retain this dedicated integration fixture for review. No cleanup or
        # deletion is attempted, including when the test fails.
        fixture = Path(tempfile.mkdtemp(prefix="closeout-longpath-evidence-"))
        root = fixture
        for index in range(6):
            root /= f"segment_{index}_" + "a" * 44
        root /= "source"
        unit = root / "工程"
        source = unit / "Library" / "PackageCache" / "package" / "deep" / "payload.bin"
        empty = unit / "Assets" / "Empty"
        evidence = root.parent / "evidence"
        os.makedirs(archive.io_path(source.parent))
        os.makedirs(archive.io_path(empty))
        os.makedirs(archive.io_path(evidence))
        self.assertGreater(len(str(root)), 300)
        payload = b"long-path-content\x00" * 257
        with archive.io_open(source, "wb") as stream:
            stream.write(payload)
        # Confirm this host's plain-path limit where it is enabled; extended IO
        # must work whether or not the global long-path policy is enabled.
        try:
            plain = source.stat()
            plain_status = f"ok(size={plain.st_size})"
        except OSError as error:
            plain_status = f"error(winerror={getattr(error, 'winerror', None)})"
        self.assertEqual(archive.io_lstat(source).st_size, len(payload))
        inventory = evidence / "inventory.json"
        plan_path = evidence / "plan.json"
        journal = evidence / "apply.jsonl"
        recovery = evidence / "rollback.jsonl"
        destination = root / "archive"
        data = archive.collect(root)
        self.assertEqual(data["read_errors"], [])
        self.assertEqual(data["skipped_links"], [])
        self.assertIn("工程/Assets/Empty", data["empty_directories"])
        self.assertEqual(len(data["files"]), 1)
        self.assertEqual(data["root"], str(root))
        self.assertFalse(data["root"].startswith("\\\\?\\"))
        archive.exclusive_json(inventory, data)
        plan = {"version": 1, "root": str(root), "destination": str(destination),
                "inventory": str(inventory), "inventory_sha256": archive.digest(inventory)["sha256"],
                "moves": [{"source": "工程", "destination": "complete"}]}
        archive.exclusive_json(plan_path, plan)
        self.assertEqual(archive.apply_plan(plan_path, journal)["moved_units"], 1)
        self.assertEqual(archive.verify_plan(plan_path)["moves"][0]["state"], "archived")
        self.assertTrue(archive.is_directory(destination / "complete" / "Assets" / "Empty"))
        self.assertEqual(archive.rollback(journal, recovery)["restored_units"], 1)
        self.assertEqual(archive.verify_plan(plan_path)["moves"][0]["state"], "original")
        with archive.io_open(source, "rb") as stream:
            self.assertEqual(stream.read(), payload)
        for record in archive.read_journal(journal):
            for key in ("source", "destination"):
                if key in record:
                    self.assertFalse(record[key].startswith("\\\\?\\"))
        print(f"\nLONG_PATH_EVIDENCE={fixture}; root_length={len(str(root))}; file_length={len(str(source))}; plain_stat={plain_status}; extended_scan_apply_verify_rollback=OK")


if __name__ == "__main__":
    unittest.main(verbosity=2)
