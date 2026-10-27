#!/usr/bin/env python3
"""Conservative, journalled same-volume archive moves using the Python stdlib.

All editors, sync jobs, game engines and other consumers must be stopped first.
Checks detect ordinary changes; they do not lock out concurrent or malicious writes.
No command deletes content, deduplicates files, follows links, or overwrites a target.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
import stat
import sys
from datetime import datetime, timezone


VERSION = 1
HASH_BUFFER_SIZE = 64 * 1024
REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
RESERVED = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\..*)?$", re.I)


class ArchiveError(ValueError):
    pass


class HashMemoryError(MemoryError):
    """An incomplete file hash; never turn this into a skipped scan entry."""
    def __init__(self, path, phase, bytes_hashed):
        self.details = {"path": str(path), "phase": phase, "bytes_hashed": bytes_hashed,
                        "process_memory": process_memory()}
        super().__init__(f"MemoryError during hashing: {path}; phase={phase}; bytes_hashed={bytes_hashed}")


def process_memory():
    """Best-effort Windows process counters, including OS-recorded peaks."""
    if os.name != "nt":
        return {}
    try:
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in (
                    "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                    "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")]
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            return {}
        return {"working_set_bytes": counters.WorkingSetSize,
                "peak_working_set_bytes": counters.PeakWorkingSetSize,
                "private_bytes": counters.PrivateUsage,
                "peak_pagefile_bytes": counters.PeakPagefileUsage}
    except (MemoryError, OSError, AttributeError):
        return {}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def is_link(info):
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & REPARSE_POINT
    )


def absolute(value, label):
    p = Path(value)
    if not p.is_absolute():
        raise ArchiveError(f"{label} must be an absolute path: {value}")
    if str(p).startswith(("\\\\?\\", "\\\\.\\")):
        raise ArchiveError(f"{label} must not use a Windows device namespace: {value}")
    # Validate before abspath removes dot components; reject Windows aliases in
    # explicitly supplied root/output/evidence paths too.
    for part in p.parts[1:]:
        relative(part, label)
    return Path(os.path.abspath(p))


def path_key(path):
    # Apply Windows' case-insensitive comparison on every supported host.
    return os.path.normpath(str(path)).replace("\\", "/").casefold()


def within(path, parent):
    key, base = path_key(path), path_key(parent).rstrip("/")
    return key == base or key.startswith(base + "/")


def relative(value, label):
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ArchiveError(f"{label} must be a nonempty relative path")
    value = value.replace("\\", "/")
    if value.startswith("/") or ntpath.splitdrive(value)[0]:
        raise ArchiveError(f"{label} must be relative: {value}")
    parts = value.split("/")
    for part in parts:
        if part in ("", ".", "..") or part.endswith((".", " ")):
            raise ArchiveError(f"{label} has an unsafe path component: {value}")
        if any(c in part for c in '<>:"|?*') or any(ord(c) < 32 for c in part):
            raise ArchiveError(f"{label} has a Windows path alias or invalid name: {value}")
        if RESERVED.fullmatch(part):
            raise ArchiveError(f"{label} uses a Windows reserved name: {value}")
    return "/".join(parts)


def io_path(path):
    """Add a Windows long-path prefix only after validating a normal path.

    This representation stays inside the IO layer. User input, manifests,
    comparisons and journals always use ordinary absolute/relative paths.
    """
    value = str(absolute(path, "IO path"))
    if os.name != "nt":
        return value
    if value.startswith("\\\\"):
        return "\\\\?\\UNC\\" + value[2:]
    return "\\\\?\\" + value


def ordinary_realpath(path):
    # realpath may return an extended prefix when fed an extended IO path.
    # Strip only the prefix that this module itself added, then validate again.
    value = os.path.realpath(io_path(path))
    if os.name == "nt":
        if value.upper().startswith("\\\\?\\UNC\\"):
            value = "\\\\" + value[8:]
        elif value.startswith("\\\\?\\"):
            value = value[4:]
    return absolute(value, "resolved IO path")


def io_lstat(path):
    return os.lstat(io_path(path))


def io_open(path, *args, **kwargs):
    return open(io_path(path), *args, **kwargs)


def is_directory(path):
    try:
        info = io_lstat(path)
    except FileNotFoundError:
        return False
    return not is_link(info) and stat.S_ISDIR(info.st_mode)


def volume_id(path):
    return io_lstat(path).st_dev


def safe_ancestors(path, must_exist=False):
    """lstat every existing ancestor, never resolve a link or a junction."""
    p = absolute(path, "path")
    chain = list(reversed(p.parents)) + [p]
    missing = False
    for current in chain:
        try:
            info = io_lstat(current)
        except FileNotFoundError:
            missing = True
            continue
        if missing:
            raise ArchiveError(f"Unexpected existing path below a missing ancestor: {current}")
        if is_link(info):
            raise ArchiveError(f"Link/reparse path is forbidden: {current}")
        if os.name == "nt" and path_key(current) != path_key(ordinary_realpath(current)):
            raise ArchiveError(f"Windows resolved path alias is forbidden: {current}")
        if current != p and not stat.S_ISDIR(info.st_mode):
            raise ArchiveError(f"Ancestor is not a directory: {current}")
    if must_exist and missing:
        raise ArchiveError(f"Path does not exist: {p}")
    return p


def lexists(path):
    try:
        io_lstat(path)
    except FileNotFoundError:
        return False
    return True


def reject_case_collision(path):
    """Also catch case aliases when tests run on a case-sensitive host."""
    current = safe_ancestors(path)
    if lexists(current):
        raise ArchiveError(f"Target already exists: {current}")
    while current.parent != current:
        parent = current.parent
        if lexists(parent):
            with os.scandir(io_path(parent)) as children:
                for child in children:
                    if child.name.casefold() == current.name.casefold():
                        if child.name != current.name or current == Path(path):
                            raise ArchiveError(f"Target has a Windows case alias: {current} / {parent / child.name}")
            break
        current = parent


def digest(path):
    path = safe_ancestors(path, must_exist=True)
    before = io_lstat(path)
    if is_link(before) or not stat.S_ISREG(before.st_mode):
        raise ArchiveError(f"Not an ordinary file: {path}")
    sha = hashlib.sha256()
    phase, bytes_hashed = "allocate_buffer", 0
    buffer = view = None
    try:
        buffer = bytearray(HASH_BUFFER_SIZE)
        view = memoryview(buffer)
        phase = "open"
        # Raw FileIO.readinto reuses one small buffer; no fresh 1 MiB bytes
        # allocation per read. Every byte still participates in SHA-256.
        with io_open(path, "rb", buffering=0) as stream:
            opened = os.fstat(stream.fileno())
            if is_link(opened) or not stat.S_ISREG(opened.st_mode):
                raise ArchiveError(f"File changed type while opening: {path}")
            while True:
                phase = "readinto"
                count = stream.readinto(buffer)
                if count == 0:
                    break
                if count is None:
                    raise ArchiveError(f"Unexpected nonblocking read on ordinary file: {path}")
                phase = "sha256_update"
                sha.update(view[:count])
                bytes_hashed += count
            phase = "final_file_stat"
            after_open = os.fstat(stream.fileno())
    except MemoryError as error:
        # Release the buffer before allocating an actionable error report.
        view = buffer = None
        raise HashMemoryError(path, phase, bytes_hashed) from error
    finally:
        view = buffer = None
    after = io_lstat(path)
    keys = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    if keys(before) != keys(opened) or keys(opened) != keys(after_open) or keys(after_open) != keys(after):
        raise ArchiveError(f"File changed during hashing: {path}")
    if is_link(after):
        raise ArchiveError(f"File became a link/reparse path: {path}")
    if bytes_hashed != before.st_size:
        raise ArchiveError(f"Incomplete file read: {path}; expected_bytes={before.st_size}; bytes_hashed={bytes_hashed}")
    return {"size": before.st_size, "sha256": sha.hexdigest()}


def collect(root):
    root = safe_ancestors(root, must_exist=True)
    result = {"version": VERSION, "root": str(root), "created_at": utc_now(),
              "files": [], "directories": [], "empty_directories": [],
              "read_errors": [], "skipped_links": []}
    info = io_lstat(root)
    if not stat.S_ISDIR(info.st_mode):
        raise ArchiveError(f"Scan root must be a directory: {root}")

    def visit(folder):
        name = folder.relative_to(root).as_posix()
        try:
            with os.scandir(io_path(folder)) as entries:
                children = sorted(entries, key=lambda e: (e.name.casefold(), e.name))
        except OSError as error:
            result["read_errors"].append({"path": name, "operation": "scandir", "error": str(error)})
            return
        if not children:
            result["empty_directories"].append(name)
        for entry in children:
            path = folder / entry.name
            rel = path.relative_to(root).as_posix()
            try:
                info = entry.stat(follow_symlinks=False)
                if is_link(info):
                    result["skipped_links"].append({"path": rel, "reason": "symlink_or_reparse_point"})
                elif stat.S_ISDIR(info.st_mode):
                    result["directories"].append(rel)
                    visit(path)
                elif stat.S_ISREG(info.st_mode):
                    result["files"].append({"path": rel, **digest(path)})
                else:
                    result["read_errors"].append({"path": rel, "operation": "type", "error": "not an ordinary file/directory"})
            except (OSError, ArchiveError) as error:
                result["read_errors"].append({"path": rel, "operation": "read", "error": str(error)})
    visit(root)
    return result


def exclusive_json(path, value):
    path = safe_ancestors(path)
    reject_case_collision(path)
    if not is_directory(path.parent):
        raise ArchiveError(f"Output parent does not exist: {path.parent}")
    with io_open(path, "x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def load_json(path):
    safe_ancestors(path, must_exist=True)
    with io_open(path, "r", encoding="utf-8") as stream:
        return json.load(stream)


def subset(inventory, source):
    prefix = source + "/"
    files = {}
    for item in inventory["files"]:
        name = item["path"]
        if name == source or name.startswith(prefix):
            files["." if name == source else name[len(prefix):]] = {
                "size": item["size"], "sha256": item["sha256"]}
    directories = []
    for name in inventory["directories"]:
        if name == source or name.startswith(prefix):
            directories.append("." if name == source else name[len(prefix):])
    for key in ("read_errors", "skipped_links"):
        for item in inventory.get(key, []):
            name = item["path"]
            if name == source or name.startswith(prefix):
                raise ArchiveError(f"Source includes an unreadable or linked path: {name}")
    if not files and not directories:
        raise ArchiveError(f"Source was not present in the frozen inventory: {source}")
    return {"kind": "directory" if "." in directories else "file",
            "files": files, "directories": sorted(directories)}


def snapshot(path):
    safe_ancestors(path, must_exist=True)
    info = io_lstat(path)
    if stat.S_ISREG(info.st_mode):
        return {"kind": "file", "files": {".": digest(path)}, "directories": []}
    if not stat.S_ISDIR(info.st_mode):
        raise ArchiveError(f"Source is not an ordinary file/directory: {path}")
    data = collect(path)
    if data["read_errors"] or data["skipped_links"]:
        raise ArchiveError(f"Source contains unreadable or linked entries: {path}")
    return {"kind": "directory", "files": {x["path"]: {"size": x["size"], "sha256": x["sha256"]} for x in data["files"]},
            "directories": sorted(["."] + data["directories"])}


def check_snapshot(path, expected):
    actual = snapshot(path)
    if actual != expected:
        expected_files, actual_files = expected["files"], actual["files"]
        missing = sorted(set(expected_files) - set(actual_files))
        added = sorted(set(actual_files) - set(expected_files))
        changed = sorted(x for x in set(expected_files) & set(actual_files) if expected_files[x] != actual_files[x])
        raise ArchiveError(f"Frozen contents differ at {path}; missing={missing[:5]}, added={added[:5]}, changed={changed[:5]}, directories_equal={expected['directories'] == actual['directories']}")


def nearest_existing(path):
    current = path
    while not lexists(current):
        if current.parent == current:
            raise ArchiveError(f"No existing ancestor for {path}")
        current = current.parent
    safe_ancestors(current, must_exist=True)
    return current


def no_overlaps(paths, label):
    for i, left in enumerate(paths):
        for right in paths[i + 1:]:
            if within(left, right) or within(right, left):
                raise ArchiveError(f"Overlapping {label}: {left} / {right}")


def prepare(plan_path, check_sources=True):
    plan_path = absolute(plan_path, "plan")
    plan = load_json(plan_path)
    return prepare_data(plan, plan_path, check_sources)


def prepare_data(plan, plan_path, check_sources=True):
    if plan.get("version", plan.get("schema_version")) != VERSION:
        raise ArchiveError("Unsupported plan version; expected version=1")
    root = absolute(plan["root"], "root")
    destination = absolute(plan["destination"], "destination")
    inventory_path = absolute(plan["inventory"], "inventory")
    safe_ancestors(root, must_exist=True)
    safe_ancestors(destination)
    if not is_directory(root):
        raise ArchiveError("Plan root is not a directory")
    if within(root, destination):
        raise ArchiveError("Destination must not equal or contain the source root")
    frozen_hash = digest(inventory_path)["sha256"]
    if frozen_hash != plan.get("inventory_sha256"):
        raise ArchiveError("Inventory SHA-256 does not match the frozen plan")
    inventory = load_json(inventory_path)
    if inventory.get("version") != VERSION or path_key(inventory.get("root", "")) != path_key(root):
        raise ArchiveError("Inventory version/root does not match plan")
    # Reject aliases in the inventory as well as plan path components.
    seen = set()
    for name in [x["path"] for x in inventory["files"]] + inventory["directories"]:
        name = relative(name, "inventory path")
        if name.casefold() in seen:
            raise ArchiveError(f"Duplicate or case-aliased inventory entry: {name}")
        seen.add(name.casefold())
    moves = []
    if not isinstance(plan.get("moves"), list) or not plan["moves"]:
        raise ArchiveError("Plan must contain at least one move")
    for item in plan["moves"]:
        src_rel = relative(item["source"], "source")
        dst_rel = relative(item["destination"], "destination")
        src, dst = root / src_rel, destination / dst_rel
        safe_ancestors(src, must_exist=check_sources)
        safe_ancestors(dst)
        if within(destination, src) or within(dst, src) or within(src, dst):
            raise ArchiveError(f"Source and destination overlap: {src} / {dst}")
        expected = subset(inventory, src_rel)
        moves.append({"source": str(src), "destination": str(dst), "expected": expected})
    no_overlaps([Path(x["source"]) for x in moves], "sources")
    no_overlaps([Path(x["destination"]) for x in moves], "targets")
    for move in moves:
        for other in moves:
            if within(Path(move["destination"]), Path(other["source"])) or within(Path(other["source"]), Path(move["destination"])):
                raise ArchiveError("A target overlaps another source")
        for evidence in (plan_path, inventory_path):
            if within(evidence, Path(move["source"])) or within(evidence, Path(move["destination"])):
                raise ArchiveError(f"Plan/inventory must remain outside moved units: {evidence}")
        if check_sources:
            reject_case_collision(Path(move["destination"]))
            check_snapshot(Path(move["source"]), move["expected"])
            if volume_id(Path(move["source"])) != volume_id(nearest_existing(Path(move["destination"]).parent)):
                raise ArchiveError(f"Cross-volume moves are forbidden: {move['source']}")
    return plan, inventory, moves


class Journal:
    def __init__(self, path, metadata):
        self.path = safe_ancestors(absolute(path, "journal"))
        reject_case_collision(self.path)
        if not is_directory(self.path.parent):
            raise ArchiveError("Journal parent must already exist")
        self.stream = io_open(self.path, "x", encoding="utf-8", newline="\n")
        self.write({"event": "metadata", "version": VERSION, **metadata})

    def write(self, record):
        self.stream.write(json.dumps({"time": utc_now(), **record}, ensure_ascii=False) + "\n")
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def close(self):
        self.stream.close()


def ensure_parents(path, journal):
    pending = []
    current = path.parent
    while not lexists(current):
        pending.append(current)
        current = current.parent
    safe_ancestors(current, must_exist=True)
    for folder in reversed(pending):
        safe_ancestors(folder)
        reject_case_collision(folder)
        journal.write({"event": "mkdir_intent", "path": str(folder)})
        os.mkdir(io_path(folder))
        journal.write({"event": "mkdir_done", "path": str(folder)})


def apply_plan(plan_path, journal_path):
    plan, inventory, moves = prepare(plan_path)
    journal_path = absolute(journal_path, "journal")
    for move in moves:
        if within(journal_path, Path(move["source"])) or within(journal_path, Path(move["destination"])):
            raise ArchiveError("Journal must be outside every moved source/target")
    journal = Journal(journal_path, {"operation": "apply", "plan": plan, "plan_path": str(absolute(plan_path, "plan")),
                                    "concurrency": "All consumers must be stopped; no concurrent-write guarantee."})
    completed = 0
    try:
        for index, move in enumerate(moves):
            src, dst = Path(move["source"]), Path(move["destination"])
            # Recheck before each move, in addition to the all-or-nothing preflight.
            check_snapshot(src, move["expected"])
            safe_ancestors(dst)
            reject_case_collision(dst)
            ensure_parents(dst, journal)
            journal.write({"event": "intent", "index": index, **move})
            os.rename(io_path(src), io_path(dst))
            journal.write({"event": "done", "index": index})
            completed += 1
        journal.write({"event": "complete", "completed": completed})
        return {"status": "complete", "moved_units": completed, "journal": str(journal_path),
                "files_covered": sum(len(x["expected"]["files"]) for x in moves),
                "inventory_files": len(inventory["files"])}
    except BaseException as error:
        try:
            journal.write({"event": "failed", "completed": completed, "error": str(error),
                           "recovery": "Use rollback with this journal; inspect actual paths after interruption."})
        except OSError:
            pass
        raise
    finally:
        journal.close()


def read_journal(path):
    safe_ancestors(path, must_exist=True)
    records = []
    with io_open(path, "r", encoding="utf-8") as stream:
        lines = stream.readlines()
    for index, line in enumerate(lines):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            # A torn final write is possible after power loss. Never guess past it.
            if index == len(lines) - 1 and not line.endswith("\n"):
                break
            raise ArchiveError(f"Malformed journal record at line {index + 1}")
    if not records or records[0].get("event") != "metadata" or records[0].get("version") != VERSION:
        raise ArchiveError("Unsupported or missing journal metadata")
    return records


def rollback(journal_path, out_path):
    journal_path, out_path = absolute(journal_path, "journal"), absolute(out_path, "rollback output")
    records = read_journal(journal_path)
    meta = records[0]
    if meta.get("operation") != "apply":
        raise ArchiveError("Rollback expects the original apply journal; re-run against it to resume recovery")
    plan = meta["plan"]
    # Re-validate the journal's frozen plan, and derive fingerprints again from
    # its SHA-256-pinned inventory. Intent payloads alone are not authoritative.
    _, _, planned_moves = prepare_data(plan, absolute(meta["plan_path"], "plan"), check_sources=False)
    root, destination = absolute(plan["root"], "root"), absolute(plan["destination"], "destination")
    intents = [x for x in records if x.get("event") == "intent"]
    indexes = set()
    actions = []
    for record in intents:
        index = record["index"]
        if not isinstance(index, int) or index < 0 or index >= len(plan["moves"]) or index in indexes:
            raise ArchiveError("Duplicate or invalid move index in journal")
        indexes.add(index)
        item = plan["moves"][index]
        src = root / relative(item["source"], "source")
        dst = destination / relative(item["destination"], "destination")
        if path_key(src) != path_key(record["source"]) or path_key(dst) != path_key(record["destination"]):
            raise ArchiveError("Journal paths do not match its recorded plan")
        if record["expected"] != planned_moves[index]["expected"]:
            raise ArchiveError("Journal fingerprints do not match the frozen inventory")
        if within(src, dst) or within(dst, src):
            raise ArchiveError("Journal source and target overlap")
        for evidence in (journal_path, out_path):
            if within(evidence, src) or within(evidence, dst):
                raise ArchiveError("Recovery evidence must be outside moved units")
        safe_ancestors(src)
        safe_ancestors(dst)
        src_exists, dst_exists = lexists(src), lexists(dst)
        if src_exists and dst_exists:
            raise ArchiveError(f"Rollback conflict: source and target both exist: {src}")
        if not src_exists and not dst_exists:
            raise ArchiveError(f"Rollback cannot find either copy: {src}")
        current = src if src_exists else dst
        check_snapshot(current, record["expected"])
        if dst_exists:
            reject_case_collision(src)
            if volume_id(dst) != volume_id(nearest_existing(src.parent)):
                raise ArchiveError("Rollback cannot cross volumes")
        actions.append((record, src_exists))
    no_overlaps([Path(x[0]["source"]) for x in actions], "journal sources")
    no_overlaps([Path(x[0]["destination"]) for x in actions], "journal targets")
    journal = Journal(out_path, {"operation": "rollback", "apply_journal": str(journal_path),
                                 "retained_directories": "Created archive parent directories are retained; no recursive deletion."})
    restored = 0
    try:
        for record, already_original in reversed(actions):
            if already_original:
                journal.write({"event": "already_original", "index": record["index"]})
                continue
            src, dst = Path(record["source"]), Path(record["destination"])
            check_snapshot(dst, record["expected"])
            safe_ancestors(src)
            reject_case_collision(src)
            ensure_parents(src, journal)
            journal.write({"event": "restore_intent", "index": record["index"], "source": str(dst), "destination": str(src)})
            os.rename(io_path(dst), io_path(src))
            journal.write({"event": "restore_done", "index": record["index"]})
            restored += 1
        journal.write({"event": "complete", "restored_units": restored})
        return {"status": "complete", "restored_units": restored,
                "already_original_units": len(actions) - restored, "journal": str(out_path),
                "created_parent_directories": "retained"}
    except BaseException as error:
        try:
            journal.write({"event": "failed", "restored_units": restored, "error": str(error),
                           "recovery": "Re-run rollback against the original apply journal with a new output path."})
        except OSError:
            pass
        raise
    finally:
        journal.close()


def verify_plan(plan_path):
    plan, inventory, moves = prepare(plan_path, check_sources=False)
    checked = []
    covered_files = 0
    covered_directories = 0
    for index, move in enumerate(moves):
        src, dst = Path(move["source"]), Path(move["destination"])
        src_exists, dst_exists = lexists(src), lexists(dst)
        if src_exists == dst_exists:
            raise ArchiveError(f"Expected exactly one original/archive copy for {src}")
        actual = src if src_exists else dst
        check_snapshot(actual, move["expected"])
        covered_files += len(move["expected"]["files"])
        covered_directories += len(move["expected"]["directories"])
        checked.append({"index": index, "state": "original" if src_exists else "archived", "path": str(actual),
                        "files": len(move["expected"]["files"]), "directories": len(move["expected"]["directories"])})
    return {"status": "verified", "coverage": "planned moves only", "files_covered": covered_files,
            "inventory_files": len(inventory["files"]), "files_outside_plan": len(inventory["files"]) - covered_files,
            "directories_covered": covered_directories, "inventory_directories": len(inventory["directories"]),
            "directories_outside_plan": len(inventory["directories"]) - covered_directories,
            "moves": checked}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("scan", help="Read-only complete inventory; links/reparse entries are recorded and skipped")
    scan.add_argument("--root", required=True)
    scan.add_argument("--out", required=True)
    apply = commands.add_parser("apply", help="Preflight frozen plan and move whole units with a durable journal")
    apply.add_argument("--plan", required=True)
    apply.add_argument("--journal", required=True)
    recovery = commands.add_parser("rollback", help="Restore using original apply journal; retain empty parent directories")
    recovery.add_argument("--journal", required=True)
    recovery.add_argument("--out", required=True)
    verify = commands.add_parser("verify", help="Verify planned units against frozen fingerprints at original/archive locations")
    verify.add_argument("--plan", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "scan":
            data = collect(absolute(args.root, "root"))
            exclusive_json(absolute(args.out, "out"), data)
            result = {"status": "scanned", "inventory": str(absolute(args.out, "out")),
                      "inventory_sha256": digest(absolute(args.out, "out"))["sha256"],
                      "files": len(data["files"]), "directories": len(data["directories"]),
                      "empty_directories": len(data["empty_directories"]),
                      "read_errors": len(data["read_errors"]), "skipped_links": len(data["skipped_links"])}
        elif args.command == "apply":
            result = apply_plan(args.plan, args.journal)
        elif args.command == "rollback":
            result = rollback(args.journal, args.out)
        else:
            result = verify_plan(args.plan)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except MemoryError as error:
        try:
            print(json.dumps({"status": "error", "error": "MemoryError; operation incomplete",
                              "details": getattr(error, "details", {}),
                              "process_memory": process_memory()}, ensure_ascii=False), file=sys.stderr)
        except MemoryError:
            # A fixed preallocated ASCII fallback avoids Python text streams
            # when the interpreter has too little memory to format diagnostics.
            os.write(2, b'{"status":"error","error":"MemoryError; operation incomplete"}\n')
        return 2
    except (ArchiveError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
