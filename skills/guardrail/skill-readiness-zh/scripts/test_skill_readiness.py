"""Behavioral checks for the invocation gate; no real installations or network."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timedelta, timezone

SCRIPT = Path(__file__).with_name("skill_readiness.py")


def definitions_digest(contract):
    import hashlib
    return hashlib.sha256(json.dumps({k: v for k, v in contract.items() if k not in {"review", "profile_reviews"}},
                                    sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.skill = self.root / "skills" / "example"
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text(
            "---\nname: example\ndescription: Example\n---\nUse [guide](references/guide.md).\n",
            encoding="utf-8")
        (self.skill / "references").mkdir()
        (self.skill / "references/guide.md").write_text("Local instructions", encoding="utf-8")
        self.manifest = self.root / "manifest.json"

    def run_cli(self, *args):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertTrue(result.stdout, result.stderr)
        return result.returncode, json.loads(result.stdout)

    def contract(self, requirements=None, **changes):
        code, draft = self.run_cli("draft", "--skill", self.skill)
        self.assertEqual(code, 0)
        draft["review"] = {"complete": True, "reviewer": "test",
                           "note": "Reviewed all bundled instructions and dependencies"}
        draft["requirements"] = requirements or []
        draft.update(changes)
        draft["review"]["definition_sha256"] = definitions_digest(draft)
        for name in draft.get("profiles", {}):
            draft.setdefault("profile_reviews", {})[name] = {**draft["review"]}
        self.manifest.write_text(json.dumps(draft), encoding="utf-8")
        return draft

    def check(self, *extra):
        return self.run_cli("check", "--skill", self.skill, "--manifest", self.manifest, *extra)

    def test_unreviewed_never_becomes_ready(self):
        code, result = self.run_cli("check", "--skill", self.skill)
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "UNKNOWN")

    def test_ready_checks_real_resource_and_tool(self):
        self.contract([{"id": "python", "kind": "executable", "command": sys.executable,
                        "version_args": ["--version"], "minimum": "3.11.0"}])
        code, result = self.check()
        self.assertEqual(code, 0, result)
        self.assertEqual(result["status"], "READY")

    def test_incomplete_review_still_reports_known_missing_dependencies(self):
        self.contract([{"id": "known-missing", "kind": "executable", "command": "missing-example-777"}],
                      review={"complete": False, "reviewer": "", "note": "Still auditing"})
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["dependency_review_complete"])
        self.assertEqual(result["requirements"][0]["status"], "MISSING")

    def test_missing_link_blocks_even_with_empty_contract(self):
        (self.skill / "references/guide.md").unlink()
        self.contract()
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any(x["status"] == "MISSING" for x in result["resources"]))

    def test_resource_change_invalidates_review(self):
        self.contract()
        (self.skill / "references/guide.md").write_text("New requirements", encoding="utf-8")
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "STALE")

    def test_missing_executable_blocks(self):
        self.contract([{"id": "missing", "kind": "executable", "command": "nonexistent-rea-test-876"}])
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["requirements"][0]["status"], "MISSING")

    def test_incompatible_version_blocks(self):
        self.contract([{"id": "python", "kind": "executable", "command": sys.executable,
                        "version_args": ["--version"], "minimum": "99.0.0"}])
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["requirements"][0]["status"], "INCOMPATIBLE")

    def test_unknown_check_kind_fails_closed(self):
        self.contract([{"id": "unknown", "kind": "guess"}])
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["requirements"][0]["status"], "UNKNOWN")

    def test_failed_probe_does_not_count_as_installed(self):
        self.contract([{"id": "broken", "kind": "executable", "command": sys.executable,
                        "version_args": ["--definitely-invalid"]}])
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["requirements"][0]["status"], "ERROR")

    def test_profile_cannot_silently_skip_requirements(self):
        self.contract([{"id": "missing", "kind": "executable", "command": "nonexistent-rea-test-876",
                        "profiles": ["other"]}], profiles={"selected": {"description": "Specific task"}})
        code, result = self.check("--profile", "selected")
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "BLOCKED")
        code, result = self.check("--profile", "selected", "--scope-reason", "User selected this task")
        self.assertEqual(code, 0, result)
        self.assertFalse(result["full_skill_ready"])
        self.assertEqual(result["requirements"][0]["status"], "NOT_SELECTED")

    def test_no_platform_waiver_in_full_check(self):
        self.contract([{"id": "foreign", "kind": "executable", "command": "anything",
                        "platforms": ["nonexistent-platform"]}])
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["requirements"][0]["status"], "UNSUPPORTED_HOST")

    def test_remote_reference_needs_local_material_or_classification(self):
        with (self.skill / "SKILL.md").open("a", encoding="utf-8") as f:
            f.write("\nRead [required](https://example.invalid/guide).\n")
        self.contract()
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "UNKNOWN")

    def test_downloaded_material_digest_is_verified(self):
        data = self.root / "material.txt"
        data.write_text("wrong revision", encoding="utf-8")
        self.contract([{"id": "material", "kind": "file", "path": str(data), "sha256": "0" * 64}])
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["requirements"][0]["status"], "MISMATCH")

    def test_mcp_registration_is_not_connection(self):
        config = self.root / "config.toml"
        config.write_text('[mcp_servers.rea]\ncommand="rea"\n', encoding="utf-8")
        self.contract([{"id": "registration", "kind": "mcp_registration", "path": str(config), "server": "rea"},
                       {"id": "connection", "kind": "session_tool", "name_pattern": "*binary_session*"}])
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["requirements"][0]["status"], "READY")
        self.assertEqual(result["requirements"][1]["status"], "UNKNOWN")

    def test_expired_or_other_session_snapshot_blocks(self):
        self.contract([{"id": "session", "kind": "session_tool", "name_pattern": "*binary_session*"}])
        snapshot = self.root / "session.json"
        snapshot.write_text(json.dumps({"session_id": "this", "observed_at":
            (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "tools": ["mcp__rea__binary_session"]}), encoding="utf-8")
        code, result = self.check("--session-tools", snapshot, "--session-id", "this")
        self.assertEqual(code, 2)
        self.assertEqual(result["requirements"][0]["status"], "STALE")
        snapshot.write_text(json.dumps({"session_id": "other", "observed_at": datetime.now(timezone.utc).isoformat(),
            "tools": ["mcp__rea__binary_session"]}), encoding="utf-8")
        code, result = self.check("--session-tools", snapshot, "--session-id", "this")
        self.assertEqual(code, 2)

    def test_inventory_keeps_duplicate_names_and_discovers_new_skill(self):
        second = self.root / "plugins" / "example"
        second.mkdir(parents=True)
        (second / "SKILL.md").write_text((self.skill / "SKILL.md").read_text(encoding="utf-8"), encoding="utf-8")
        code, result = self.run_cli("inventory", "--root", f"user={self.root / 'skills'}",
                                  "--root", f"plugin={self.root / 'plugins'}")
        self.assertEqual(code, 0)
        self.assertEqual(len(result["skills"]), 2)
        self.assertEqual(len({s["id"] for s in result["skills"]}), 2)
        added = self.root / "skills" / "new"
        added.mkdir()
        (added / "SKILL.md").write_text("---\nname: new\ndescription: New\n---\n", encoding="utf-8")
        code, result = self.run_cli("inventory", "--root", f"user={self.root / 'skills'}",
                                  "--root", f"plugin={self.root / 'plugins'}")
        self.assertEqual(len(result["skills"]), 3)

    def test_unreadable_or_missing_root_is_visible(self):
        code, result = self.run_cli("inventory", "--root", f"missing={self.root / 'absent'}")
        self.assertEqual(code, 2)
        self.assertTrue(result["discovery_errors"])

    def test_malformed_contract_is_json_error_and_nonzero(self):
        self.manifest.write_text("{invalid", encoding="utf-8")
        code, result = self.check()
        self.assertEqual(code, 3)
        self.assertEqual(result["status"], "ERROR")

    def test_duplicate_root_label_cannot_hide_an_inventory_scope(self):
        code, result = self.run_cli("inventory", "--root", f"same={self.root / 'skills'}",
                                  "--root", f"same={self.root / 'absent'}")
        self.assertEqual(code, 3)
        self.assertEqual(result["status"], "ERROR")

    def test_missing_skill_identity_cannot_receive_a_permit(self):
        (self.skill / "SKILL.md").write_text("No frontmatter", encoding="utf-8")
        self.contract()
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "ERROR")

    def test_external_markdown_closure_catches_missing_second_level_material(self):
        shared = self.root / "skills/shared"
        shared.mkdir()
        (shared / "guide.md").write_text("Read [template](missing-template.docx).", encoding="utf-8")
        (self.skill / "SKILL.md").write_text("---\nname: example\ndescription: Example\n---\nRead [guide](../shared/guide.md).", encoding="utf-8")
        self.contract()
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "BLOCKED")

    def test_external_markdown_closure_catches_unclassified_remote_material(self):
        shared = self.root / "skills/shared"
        shared.mkdir()
        (shared / "guide.md").write_text("Read [guide](https://example.invalid/required).", encoding="utf-8")
        (self.skill / "SKILL.md").write_text("---\nname: example\ndescription: Example\n---\nRead [guide](../shared/guide.md).", encoding="utf-8")
        self.contract()
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "UNKNOWN")

    def test_reference_style_markdown_and_html_resources_are_checked(self):
        for link in ("[required][doc]\n\n[doc]: references/missing.md\n", '<img src="assets/required.png">'):
            with self.subTest(link=link):
                (self.skill / "SKILL.md").write_text("---\nname: example\ndescription: Example\n---\n" + link, encoding="utf-8")
                self.contract()
                code, result = self.check()
                self.assertEqual(code, 2)
                self.assertEqual(result["status"], "BLOCKED")

    def test_markdown_cycles_terminate_without_hiding_missing_resources(self):
        (self.skill / "references/guide.md").write_text("[back](../SKILL.md) [missing](missing.dat)", encoding="utf-8")
        self.contract()
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "BLOCKED")

    def test_manifest_definition_change_invalidates_old_review(self):
        contract = self.contract([{"id": "missing", "kind": "executable", "command": "missing-89765"}])
        self.assertEqual(self.check()[0], 2)
        contract["requirements"] = []
        self.manifest.write_text(json.dumps(contract), encoding="utf-8")
        code, result = self.check()
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "STALE")

    def test_explicit_nonexistent_manifest_is_not_silently_replaced(self):
        self.contract()
        code, result = self.run_cli("check", "--skill", self.skill, "--manifest", self.root / "typo.json")
        self.assertEqual(code, 3)
        self.assertEqual(result["status"], "ERROR")

    def test_profile_review_is_independent_from_unfinished_full_review(self):
        draft = self.contract(profiles={"chosen": {"description": "User-selected task"}})
        draft["review"]["complete"] = False
        self.manifest.write_text(json.dumps(draft), encoding="utf-8")
        self.assertEqual(self.check()[1]["status"], "UNKNOWN")
        code, result = self.check("--profile", "chosen", "--scope-reason", "Explicit user choice")
        self.assertEqual(code, 0, result)
        self.assertTrue(result["dependency_review_complete"])
        self.assertFalse(result["full_dependency_review_complete"])
        self.assertFalse(result["full_skill_ready"])

    def test_full_review_does_not_automatically_approve_a_new_profile(self):
        draft = self.contract(profiles={"chosen": {"description": "Task"}})
        draft["profile_reviews"] = {}
        self.manifest.write_text(json.dumps(draft), encoding="utf-8")
        code, result = self.check("--profile", "chosen", "--scope-reason", "Explicit user choice")
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "UNKNOWN")

    def test_profile_definition_change_invalidates_its_review(self):
        draft = self.contract(profiles={"chosen": {"description": "Task"}})
        draft["profiles"]["chosen"]["description"] = "Different task"
        self.manifest.write_text(json.dumps(draft), encoding="utf-8")
        code, result = self.check("--profile", "chosen", "--scope-reason", "Explicit user choice")
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "STALE")

    def test_rea_owned_mcp_probe_requires_actual_request_flow(self):
        spec = importlib.util.spec_from_file_location("readiness_under_test", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        node = self.root / "node.exe"
        node.write_bytes(b"fixture executable")
        package = self.root / "rea"
        (package / "scripts").mkdir(parents=True)
        launcher = package / "scripts/rea.mjs"
        launcher.write_text("fixture", encoding="utf-8")
        (package / "package.json").write_text('{"name":"rea-agents","version":"6.8.0"}', encoding="utf-8")
        requirement = {"id":"rea", "kind":"rea_probe", "mode":"mcp", "node":str(node), "launcher":str(launcher)}
        for report, expected in (({"healthy":True}, "BLOCKED"),
            ({"healthy":True,"request_flow":{"ok":True,"tool":"binary_session"}},"READY"),
            ({"healthy":False,"request_flow":{"ok":True,"tool":"binary_session"}},"BLOCKED")):
            with mock.patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess([],0,json.dumps(report),"")):
                result = module.probe(requirement,self.skill,{})
            self.assertEqual(result["status"],expected)
            self.assertIn("not the active Codex chat",result["scope"])

    def test_rea_selected_provider_does_not_require_all_other_providers(self):
        spec = importlib.util.spec_from_file_location("readiness_under_test", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        node = self.root / "node.exe"
        node.write_bytes(b"fixture executable")
        package = self.root / "rea"
        (package / "scripts").mkdir(parents=True)
        launcher = package / "scripts/rea.mjs"
        launcher.write_text("fixture", encoding="utf-8")
        (package / "package.json").write_text('{"name":"rea-agents","version":"6.8.0"}', encoding="utf-8")
        requirement = {"id":"ghidra", "kind":"rea_probe", "mode":"ghidra", "node":str(node), "launcher":str(launcher)}
        report={"healthy":True,"environment_healthy":False,"scope_checks":[{"ok":True,"name":"ghidra"}]}
        with mock.patch.object(module.subprocess,"run",return_value=subprocess.CompletedProcess([],0,json.dumps(report),"")):
            self.assertEqual(module.probe(requirement,self.skill,{})["status"],"READY")

    def test_css_selector_in_code_is_not_an_html_resource(self):
        with (self.skill / "SKILL.md").open("a", encoding="utf-8") as stream:
            stream.write('\n```json\n{"selector":"nav a[href=\'/settings\']"}\n```\n')
        self.contract()
        self.assertEqual(self.check()[0],0)


if __name__ == "__main__":
    unittest.main()
