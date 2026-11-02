"""Read-only, fail-closed skill dependency inspection. Python 3.11+, stdlib only.

Inventory is not an execution permit. `check` recomputes all evidence every time.
No installer, credential reader, target launcher, or arbitrary shell evaluation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import fnmatch
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib
from urllib.parse import unquote, urlparse

IGNORED = {".git", "__pycache__", ".venv", "node_modules", ".local"}
LINK = re.compile(r"\[[^\]]*\]\(<?([^\s)>]+)>?(?:\s+[^)]*)?\)")
REFERENCE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?([^\s>]+)>?", re.M)
HTML_RESOURCE = re.compile(r"\b(?:src|href)\s*=\s*(?:\"([^\"]+)\"|'([^']+)'|([^\s>]+))", re.I)
HTML_TAG = re.compile(r"<[a-z][a-z0-9:-]*\b[^>]*>", re.I)
URL = re.compile(r"https?://[^\s<>\]`)\"']+")
VERSION = re.compile(r"(?<!\d)(\d+)\.(\d+)(?:\.(\d+))?")
BAD = {"MISSING", "INCOMPATIBLE", "ERROR", "MISMATCH", "UNSUPPORTED_HOST"}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pending = destination.with_suffix(destination.suffix + ".pending")
    pending.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pending.replace(destination)


def metadata(text):
    head = text.split("---", 2)[1] if text.startswith("---") else ""
    name = re.search(r"^name:\s*['\"]?([^\r\n'\"]+)", head, re.M)
    version = re.search(r"^\s+version:\s*['\"]?([^\r\n'\"]+)", head, re.M)
    return {"name": name.group(1).strip() if name else None,
            "version": version.group(1).strip() if version else None}


def bundle(skill):
    """Hash all bundled files and referenced local materials; report missing links.

    Markdown references are followed transitively with cycle detection. External
    directories and symlink directories require an explicit material audit.
    """
    skill = Path(skill).resolve()
    entry = skill / "SKILL.md"
    text = entry.read_text(encoding="utf-8-sig")
    files, errors, resources, remote, pending, visited = {}, [], {}, set(), [], set()

    def walk_error(error):
        errors.append({"path": str(error.filename), "status": "ERROR", "reason": str(error)})

    for current, dirs, names in os.walk(skill, onerror=walk_error, followlinks=False):
        for name in list(dirs):
            p = Path(current) / name
            if name in IGNORED:
                dirs.remove(name)
            elif p.is_symlink():
                errors.append({"path": str(p), "status": "UNKNOWN", "reason": "symlink directory needs explicit audit"})
                dirs.remove(name)
        for name in names:
            if name == "readiness.json" or name.endswith((".pyc", ".pending")):
                continue
            p = Path(current) / name
            try:
                files[p.relative_to(skill).as_posix()] = digest(p)
                resources[str(p)] = {"path": str(p), "status": "READY", "sha256": files[p.relative_to(skill).as_posix()]}
                if p.suffix.lower() == ".md":
                    pending.append(p)
            except (OSError, UnicodeError) as error:
                errors.append({"path": str(p), "status": "ERROR", "reason": str(error)})
    while pending:
        p = pending.pop().resolve()
        if p in visited:
            continue
        visited.add(p)
        if len(visited) > 20000:
            errors.append({"status": "UNKNOWN", "reason": "Markdown closure limit exceeded; completeness not established"})
            break
        try:
            body = p.read_text(encoding="utf-8-sig")
            remote.update(URL.findall(body))
            links = LINK.findall(body) + REFERENCE.findall(body)
            tags = HTML_TAG.findall(body)
            links += [next(value for value in values if value) for tag in tags for values in HTML_RESOURCE.findall(tag)]
            if any(re.search(r"\bsrcset\s*=", tag, re.I) for tag in tags):
                errors.append({"path": str(p), "status": "UNKNOWN", "reason": "srcset resources need an explicit audit"})
            for link in links:
                parsed = urlparse(link)
                if parsed.scheme in {"http", "https"}:
                    remote.add(link)
                    continue
                if parsed.scheme in {"mailto", "plugin", "app", "codex"} or link.startswith("#"):
                    continue
                local = unquote(link.split("#", 1)[0].split("?", 1)[0])
                if not local:
                    continue
                if "://" in local or (parsed.scheme and not re.match(r"^[a-zA-Z]:[\\/]", local)):
                    errors.append({"path": str(p), "status": "UNKNOWN", "reason": "unhandled resource scheme: " + parsed.scheme})
                    continue
                target = Path(os.path.expandvars(os.path.expanduser(local)))
                if not target.is_absolute():
                    target = p.parent / target
                target = target.resolve()
                if target.is_file():
                    resources[str(target)] = {"path": str(target), "status": "READY", "sha256": digest(target)}
                    if target.suffix.lower() == ".md" and target not in visited:
                        pending.append(target)
                elif target.is_dir():
                    resources[str(target)] = {"path": str(target), "status": "UNKNOWN", "reason": "directory reference requires explicit material audit"}
                else:
                    resources[str(target)] = {"path": str(target), "status": "MISSING", "referenced_by": str(p)}
        except (OSError, UnicodeError, ValueError) as error:
            errors.append({"path": str(p), "status": "ERROR", "reason": str(error)})
    if len(files) > 20000:
        errors.append({"status": "ERROR", "reason": "bundle exceeds supported audit size"})
    # Include existence and content of external referenced files in review identity.
    identity = {"files": files, "resources": sorted(resources.values(), key=lambda r: r["path"]), "errors": errors}
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {**metadata(text), "path": str(skill), "bundle_sha256": fingerprint,
            "resources": list(resources.values()) + errors, "remote_urls": sorted(remote),
            "bundled_file_count": len(files), "errors": errors}


def draft(skill):
    b = bundle(skill)
    return {"schema_version": 1, "skill_name": b["name"], "bundle_sha256": b["bundle_sha256"],
            "review": {"complete": False, "reviewer": "", "note": "Read all instructions, scripts, assets and dependencies before completing"},
            "requirements": [], "remote_materials": {url: {"classification": "unreviewed"} for url in b["remote_urls"]},
            "profiles": {}, "profile_reviews": {}, "source": {"skill_path": b["path"], "skill_version": b["version"]}}


def definition_digest(contract):
    content = {key: value for key, value in contract.items() if key not in {"review", "profile_reviews"}}
    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def version_tuple(value):
    match = VERSION.search(str(value))
    return tuple(int(x or 0) for x in match.groups()) if match else None


def acceptable(version, requirement):
    actual = version_tuple(version)
    if actual is None:
        return False
    ranges = requirement.get("accepted_versions")
    if ranges:
        return any(("major" not in item or actual[0] == item["major"]) and
                   ("minimum" not in item or actual >= version_tuple(item["minimum"])) and
                   ("maximum_exclusive" not in item or actual < version_tuple(item["maximum_exclusive"])) for item in ranges)
    if "minimum" in requirement and actual < version_tuple(requirement["minimum"]):
        return False
    return "exact_version" not in requirement or actual == version_tuple(requirement["exact_version"])


def expanded(value, skill):
    p = Path(os.path.expandvars(os.path.expanduser(str(value))))
    return p if p.is_absolute() else Path(skill) / p


def fresh_snapshot(context):
    path = context.get("session_tools")
    if not path or not context.get("session_id"):
        return "UNKNOWN", None
    snapshot = read_json(path)
    if snapshot.get("session_id") != context["session_id"]:
        return "STALE", None
    timestamp = datetime.fromisoformat(snapshot["observed_at"].replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - timestamp).total_seconds()
    if age < -30 or age > 300:
        return "STALE", None
    if not isinstance(snapshot.get("tools"), list) or not all(isinstance(x, str) for x in snapshot["tools"]):
        return "ERROR", None
    return "READY", snapshot


def probe(requirement, skill, context):
    result = {"id": requirement["id"], "kind": requirement.get("kind"), "checked_at": now()}
    try:
        platforms = requirement.get("platforms", [])
        if platforms and sys.platform not in platforms:
            return {**result, "status": "UNSUPPORTED_HOST", "host": sys.platform, "supported": platforms}
        kind = requirement.get("kind")
        if kind == "rea_probe":
            node = expanded(requirement["node"], skill)
            launcher = expanded(requirement["launcher"], skill)
            if not node.is_file() or not launcher.is_file():
                return {**result, "status": "MISSING", "reason": "dedicated Node or public REA launcher is missing"}
            info = read_json(launcher.parent.parent / "package.json")
            if node.name.lower() not in {"node", "node.exe"} or launcher.name != "rea.mjs" or info.get("name") != "rea-agents":
                return {**result, "status": "ERROR", "reason": "not the declared public Node/REA entrypoint"}
            mode = requirement.get("mode")
            arguments = {"cli": ["--version"], "ghidra": ["doctor", "--provider", "ghidra", "--format", "json"],
                         "mcp": ["mcp", "doctor", "--json"]}.get(mode)
            if arguments is None:
                return {**result, "status": "UNKNOWN", "reason": "unsupported read-only REA probe"}
            environment = os.environ.copy()
            overrides = requirement.get("environment", {})
            if set(overrides) - {"JAVA_HOME", "GHIDRA_INSTALL_DIR"}:
                return {**result, "status": "ERROR", "reason": "unsupported environment override"}
            environment.update(overrides)
            environment["PATH"] = str(node.parent) + os.pathsep + environment.get("PATH", "")
            process = subprocess.run([str(node), str(launcher), *arguments], env=environment, capture_output=True,
                                     timeout=60, text=True, encoding="utf-8", errors="replace", shell=False)
            result.update(returncode=process.returncode, package_version=info.get("version"), launcher_sha256=digest(launcher))
            if process.returncode:
                return {**result, "status": "ERROR", "reason": "REA read-only probe failed", "output": (process.stdout + process.stderr)[:4000]}
            if mode == "cli":
                return {**result, "status": "READY" if acceptable(process.stdout, requirement) else "INCOMPATIBLE", "version": process.stdout.strip()}
            report = json.loads(process.stdout)
            ok = report.get("healthy") is True
            if mode == "ghidra":
                checks = report.get("scope_checks", [])
                ok = ok and bool(checks) and all(item.get("ok") is True for item in checks)
                return {**result, "status": "READY" if ok else "BLOCKED", "scope_checks": checks,
                        "scope": "selected Ghidra provider; not every REA capability"}
            flow = report.get("request_flow", {})
            ok = ok and flow.get("ok") is True and flow.get("tool") == "binary_session"
            return {**result, "status": "READY" if ok else "BLOCKED", "request_flow": flow,
                    "scope": "fresh owned MCP validation connection; not the active Codex chat"}
        if kind == "rea_package":
            roots = [Path.home() / "AppData/Local/npm-cache/_npx", Path.home() / ".npm/_npx"]
            packages = []
            for root in roots:
                if root.is_dir():
                    packages += list(root.glob("*/node_modules/rea-agents/package.json"))
            global_root = Path.home() / "AppData/Roaming/npm/node_modules/rea-agents/package.json"
            if global_root.is_file():
                packages.append(global_root)
            found = []
            for path in packages:
                info = read_json(path)
                if info.get("name") == "rea-agents":
                    launcher = path.parent / "scripts/rea.mjs"
                    found.append({"path": str(path), "version": info.get("version"),
                                  "node_requirement": info.get("engines", {}).get("node"),
                                  "public_launcher_exists": launcher.is_file()})
            return {**result, "status": "READY" if any(x["public_launcher_exists"] for x in found) else "MISSING",
                    "packages": found, "scope": "package bytes only; runtime, CLI and MCP are separate"}
        if kind == "file":
            p = expanded(requirement["path"], skill)
            result["path"] = str(p)
            if not p.is_file():
                return {**result, "status": "MISSING"}
            result["sha256"] = digest(p)
            return {**result, "status": "MISMATCH" if requirement.get("sha256") and requirement["sha256"] != result["sha256"] else "READY"}
        if kind == "executable":
            command = requirement["command"]
            path = shutil.which(command)
            if not path:
                return {**result, "status": "MISSING", "command": command}
            result["path"] = path
            args = requirement.get("version_args")
            if not args:
                return {**result, "status": "UNKNOWN", "reason": "path found, no functional/version probe declared"}
            # Only these inert version flags are accepted; never execute snippets.
            if args not in (["--version"], ["-version"], ["-V"], ["/version"]):
                return {**result, "status": "ERROR", "reason": "only version flags are allowed"}
            if Path(path).suffix.lower() in {".ps1", ".cmd", ".bat"}:
                return {**result, "status": "UNKNOWN", "reason": "shell launcher requires explicit read-only adapter"}
            process = subprocess.run([path, *args], capture_output=True, timeout=10, text=True, encoding="utf-8", errors="replace", shell=False)
            output = (process.stdout + process.stderr).strip()[:4000]
            result.update(returncode=process.returncode, output=output)
            if process.returncode:
                return {**result, "status": "ERROR"}
            if not version_tuple(output):
                return {**result, "status": "UNKNOWN", "reason": "version output not recognized"}
            return {**result, "status": "READY" if acceptable(output, requirement) else "INCOMPATIBLE"}
        if kind == "python_distribution":
            installed = importlib.metadata.version(requirement["distribution"])
            return {**result, "version": installed, "interpreter": sys.executable,
                    "status": "READY" if acceptable(installed, requirement) else "INCOMPATIBLE"}
        if kind == "mcp_registration":
            p = expanded(requirement["path"], skill)
            if not p.is_file():
                return {**result, "status": "MISSING", "path": str(p)}
            cfg = tomllib.loads(p.read_text(encoding="utf-8-sig"))
            server = cfg.get("mcp_servers", {}).get(requirement["server"])
            valid = isinstance(server, dict) and server.get("enabled", True) and bool(server.get("command") or server.get("url"))
            # Do not expose configuration contents, env values, URLs or credentials.
            return {**result, "status": "READY" if valid else "MISSING", "path": str(p),
                    "scope": "registration only; active connection is separate"}
        if kind in {"session_tool", "session_health"}:
            state, snapshot = fresh_snapshot(context)
            if state != "READY":
                return {**result, "status": state, "reason": "fresh evidence from this active session is required"}
            names = [name for name in snapshot["tools"] if fnmatch.fnmatchcase(name, requirement["name_pattern"])]
            if not names:
                return {**result, "status": "MISSING", "reason": "not advertised in current session"}
            if kind == "session_health":
                observations = snapshot.get("health", {})
                matching = [observations.get(name, {}) for name in names]
                # Health evidence must identify a successful actual read-only call.
                ok = any(x.get("ok") is True and x.get("evidence_id") and x.get("operation") for x in matching)
                return {**result, "status": "READY" if ok else "UNKNOWN", "tools": names,
                        "reason": "actual successful health-call evidence required"}
            return {**result, "status": "READY", "tools": names, "scope": "advertised, not functionally verified"}
        return {**result, "status": "UNKNOWN", "reason": "unsupported dependency type; add a verified adapter or material evidence"}
    except importlib.metadata.PackageNotFoundError:
        return {**result, "status": "MISSING"}
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        return {**result, "status": "ERROR", "reason": str(error)}


def check(skill, manifest=None, profile="full", scope_reason=None, context=None):
    b = bundle(skill)
    result = {"schema_version": 1, "checked_at": now(), "skill": {k: b[k] for k in ("name", "version", "path", "bundle_sha256")},
              "profile": profile, "scope_reason": scope_reason, "status": "UNKNOWN", "full_skill_ready": False,
              "manifest_path": str(manifest) if manifest else None,
              "resources": b["resources"], "requirements": [], "issues": []}
    if not b["name"]:
        result.update(status="ERROR")
        result["issues"].append("Missing or unsupported skill identity metadata")
        return result
    if not manifest or not Path(manifest).is_file():
        result["issues"].append("No reviewed dependency manifest: discovery is not readiness")
        return result
    contract = read_json(manifest)
    if contract.get("schema_version") != 1 or contract.get("skill_name") != b["name"]:
        raise ValueError("Manifest schema or skill identity mismatch")
    profiles = contract.get("profiles", {})
    if not isinstance(profiles, dict) or any(not isinstance(value, dict) for value in profiles.values()):
        raise ValueError("Every profile must be an object with its explicit scope")
    if contract.get("bundle_sha256") != b["bundle_sha256"]:
        result.update(status="STALE")
        result["issues"].append("Skill/material fingerprint changed; re-audit the dependency manifest")
        return result
    review = contract.get("review", {}) if profile == "full" else contract.get("profile_reviews", {}).get(profile, {})
    reviewed = review.get("complete") is True and bool(review.get("reviewer")) and bool(review.get("note"))
    result["dependency_review_complete"] = reviewed
    result["review_scope"] = profile
    full_review = contract.get("review", {})
    result["full_dependency_review_complete"] = full_review.get("complete") is True and bool(full_review.get("reviewer")) and bool(full_review.get("note")) and full_review.get("definition_sha256") == definition_digest(contract)
    if reviewed and review.get("definition_sha256") != definition_digest(contract):
        result.update(status="STALE")
        result["issues"].append("Dependency definitions changed or are not bound to the review; re-review required")
        return result
    if not reviewed:
        result["issues"].append("Dependency completeness has not been explicitly reviewed")
    if profile != "full" and (not scope_reason or profile not in contract.get("profiles", {})):
        result.update(status="BLOCKED")
        result["issues"].append("A known profile and explicit scope-selection reason are required; default is full")
        return result
    requirements = contract.get("requirements")
    if not isinstance(requirements, list) or any(not isinstance(r, dict) or not r.get("id") for r in requirements):
        raise ValueError("Every dependency must have a unique id")
    ids = [r["id"] for r in requirements]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate dependency id")
    for requirement in requirements:
        if profile != "full" and "profiles" in requirement and profile not in requirement["profiles"]:
            result["requirements"].append({"id": requirement["id"], "status": "NOT_SELECTED"})
        else:
            result["requirements"].append(probe(requirement, skill, context or {}))
    for url in b["remote_urls"]:
        info = contract.get("remote_materials", {}).get(url, {})
        if profile != "full":
            info = contract.get("profiles", {}).get(profile, {}).get("remote_materials", {}).get(url, info)
        classification = info.get("classification")
        if profile != "full" and classification == "not_selected" and info.get("reason"):
            result["requirements"].append({"id": url, "status": "NOT_SELECTED", "reason": info["reason"]})
        elif classification == "citation" and info.get("reason"):
            result["requirements"].append({"id": url, "status": "REFERENCE_ONLY", "reason": info["reason"]})
        elif classification == "material" and info.get("path") and info.get("sha256"):
            result["requirements"].append(probe({"id": url, "kind": "file", "path": info["path"], "sha256": info["sha256"]}, skill, context or {}))
        else:
            result["requirements"].append({"id": url, "status": "UNKNOWN", "reason": "Classify citation explicitly or verify local material and SHA-256"})
    states = [item["status"] for item in result["resources"] + result["requirements"]]
    if any(state in BAD for state in states):
        result["status"] = "BLOCKED"
    elif "STALE" in states:
        result["status"] = "STALE"
    elif not reviewed or any(state not in {"READY", "REFERENCE_ONLY", "NOT_SELECTED"} for state in states):
        result["status"] = "UNKNOWN"
    else:
        result["status"] = "READY"
        result["full_skill_ready"] = profile == "full"
    return result


def defaults():
    home = Path.home()
    return {"agents": home / ".agents/skills", "codex": home / ".codex/skills",
            "plugins": home / ".codex/plugins/cache"}


def manifest_name(path):
    return hashlib.sha256(str(Path(path).resolve()).encode()).hexdigest() + ".json"


def inventory(roots, state_dir, context):
    errors, entries = [], []
    for label, root in roots.items():
        root = Path(root).resolve()
        if not root.is_dir():
            errors.append({"root": str(root), "reason": "root missing or not a directory"})
            continue
        def onerror(error):
            errors.append({"root": str(root), "path": str(error.filename), "reason": str(error)})
        for current, dirs, files in os.walk(root, onerror=onerror, followlinks=False):
            for name in list(dirs):
                p = Path(current) / name
                if name in IGNORED:
                    dirs.remove(name)
                elif p.is_symlink():
                    errors.append({"root": str(root), "path": str(p), "reason": "symlink directory not traversed"})
                    dirs.remove(name)
            if "SKILL.md" not in files:
                continue
            skill = Path(current)
            identity = label + ":" + skill.relative_to(root).as_posix()
            manifest = skill / "readiness.json"
            if not manifest.is_file() and state_dir:
                manifest = Path(state_dir) / "manifests" / manifest_name(skill)
            try:
                report = check(skill, manifest, context=context)
                if manifest.is_file():
                    contract = read_json(manifest)
                    report["profile_statuses"] = []
                    for profile in contract.get("profiles", {}):
                        scoped = check(skill, manifest, profile, "Read-only inventory; not a task execution permit", context)
                        report["profile_statuses"].append({key: scoped.get(key) for key in
                            ("profile", "status", "checked_at", "full_skill_ready", "dependency_review_complete", "issues")})
                entries.append({"id": identity, **report})
            except (OSError, ValueError, KeyError, TypeError) as error:
                entries.append({"id": identity, "status": "ERROR", "full_skill_ready": False,
                                "skill": {"path": str(skill)}, "issues": [str(error)]})
    return {"schema_version": 1, "checked_at": now(), "host": sys.platform,
            "roots": {label: str(path) for label, path in roots.items()},
            "discovery_complete": not errors, "discovery_errors": errors,
            "summary": dict(Counter(s["status"] for s in entries)), "skills": entries,
            "notice": "Inventory is a snapshot, not permission to execute. Run check immediately before invocation."}


def markdown(report):
    lines = ["# Skill 当前状态", "", f"检查时间（UTC）：{report['checked_at']}", "",
             "这是盘点快照；执行前必须重新 check。未知和过期均不允许执行。", "",
             "| 来源/身份 | 技能 | 版本 | 全技能状态 | 已声明范围状态 | 缺项/待核实 |", "|---|---|---|---|---|---|"]
    for item in report["skills"]:
        skill = item["skill"]
        pending = [r.get("id", r.get("path", "resource")) for r in item.get("requirements", []) + item.get("resources", [])
                   if r["status"] not in {"READY", "REFERENCE_ONLY"}]
        details = item.get("issues", []) + pending
        profiles = "; ".join(p["profile"] + ": " + p["status"] for p in item.get("profile_statuses", [])) or "未审阅"
        cells = [item["id"], skill.get("name") or "未解析", skill.get("version") or "未声明", item["status"], profiles, "; ".join(details[:4])]
        lines.append("| " + " | ".join(str(x).replace("|", "\\|").replace("\n", " ") for x in cells) + " |")
    if report["discovery_errors"]:
        lines += ["", "发现错误：", "```json", json.dumps(report["discovery_errors"], ensure_ascii=False, indent=2), "```"]
    return "\n".join(lines) + "\n"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    hashing = sub.add_parser("definition-digest", help="Compute the definition hash to record after explicit completeness review")
    hashing.add_argument("--manifest", required=True, type=Path)
    for operation in ("draft", "check", "inventory"):
        p = sub.add_parser(operation)
        p.add_argument("--output", help="Optional explicit JSON destination")
        if operation != "inventory":
            p.add_argument("--skill", required=True, type=Path)
        if operation != "draft":
            p.add_argument("--session-tools", type=Path)
            p.add_argument("--session-id")
        if operation == "check":
            p.add_argument("--manifest", type=Path)
            p.add_argument("--profile", default="full")
            p.add_argument("--scope-reason")
        if operation == "inventory":
            p.add_argument("--root", action="append", help="label=absolute-path; repeat for all intended roots")
            p.add_argument("--state-dir", type=Path, default=Path.home() / ".agents/.local/skill-readiness")
            p.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    try:
        context = {"session_tools": getattr(args, "session_tools", None), "session_id": getattr(args, "session_id", None)}
        if args.operation == "definition-digest":
            result, code = {"definition_sha256": definition_digest(read_json(args.manifest))}, 0
        elif args.operation == "draft":
            result, code = draft(args.skill), 0
        elif args.operation == "check":
            if args.manifest and not args.manifest.is_file():
                raise ValueError("Explicit manifest does not exist: " + str(args.manifest))
            manifest = args.manifest or args.skill / "readiness.json"
            if not args.manifest and not manifest.is_file():
                manifest = Path.home() / ".agents/.local/skill-readiness/manifests" / manifest_name(args.skill)
            result = check(args.skill, manifest, args.profile, args.scope_reason, context)
            code = 0 if result["status"] == "READY" else 2
        else:
            pairs = [item.split("=", 1) for item in args.root] if args.root else list(defaults().items())
            if any(len(pair) != 2 or not pair[0] or not pair[1] for pair in pairs):
                raise ValueError("Each root must be label=path")
            if len({pair[0] for pair in pairs}) != len(pairs):
                raise ValueError("Duplicate root labels would hide a discovery scope")
            roots = dict(pairs)
            result = inventory(roots, args.state_dir, context)
            code = 0 if result["discovery_complete"] else 2
            if args.markdown:
                args.markdown.parent.mkdir(parents=True, exist_ok=True)
                args.markdown.write_text(markdown(result), encoding="utf-8")
        if getattr(args, "output", None):
            write_json(args.output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"status": "ERROR", "reason": str(error)}, ensure_ascii=False))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
