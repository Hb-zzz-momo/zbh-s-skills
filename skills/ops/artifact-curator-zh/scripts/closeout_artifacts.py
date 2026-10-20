"""Execute a reviewed, task-owned cleanup manifest. Default: read-only dry run.

Authorization comes from the user/session, never from a manifest or --apply.
This tool does no discovery, process termination or command execution;
it makes no cloud service API calls.
Byte counts describe logical file lengths, not disk blocks freed or memory.
Workers must stay stopped; filesystem checks do not lock out hostile writers.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import stat


TEMPORARY_SUFFIXES = frozenset({".pyc", ".pyo", ".tmp", ".part", ".png", ".jpg", ".jpeg", ".svg", ".pdf"})
PASS_STATUSES = {"PASS", "PASS_WITH_NONBLOCKING_CAUTIONS"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_chain(path, missing_leaf=False):
    """lstat every ancestor, including ancestors above the task root."""
    for component in reversed((path, *path.parents)):
        try:
            info = component.lstat()
        except FileNotFoundError:
            if missing_leaf and component == path:
                continue
            raise
        require(not stat.S_ISLNK(info.st_mode)
                and not (getattr(info, "st_file_attributes", 0)
                         & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)),
                "symlink/junction/reparse point forbidden: " + str(component))
        if component != path:
            require(stat.S_ISDIR(info.st_mode), "ancestor must be a directory")
    # Windows short names (8.3) can alias protected paths without being links.
    # Compare only after rejecting reparse ancestors; never normalize and allow.
    require(path.is_absolute() and path == path.resolve(strict=not missing_leaf),
            "noncanonical path/alias forbidden: " + str(path))
    return path


def relative_path(root, value):
    require(isinstance(value, str) and bool(value), "path must be a nonempty relative string")
    parts = value.replace("\\", "/").split("/")
    win = PureWindowsPath(value)
    require(not win.drive and not win.root and not Path(value).is_absolute(), "absolute/drive path forbidden")
    require(all(part not in {"", ".", ".."} and ":" not in part
                and not part.endswith((" ", ".")) for part in parts), "unsafe relative path")
    path = root.joinpath(*parts)
    require(path != root and path.is_relative_to(root), "path outside task root")
    return path


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(path):
    safe_chain(path)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), "ordinary files only: " + str(path))
    digest = hashlib.sha256()
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(path, flags), "rb") as stream:
        opened = os.fstat(stream.fileno())
        require((before.st_dev, before.st_ino) == (opened.st_dev, opened.st_ino), "file changed before read")
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
        after = os.fstat(stream.fileno())
    safe_chain(path)
    current = path.lstat()
    # Windows Python may expose different ctime semantics for stat and fstat.
    # Compare each API's ctime with itself, plus shared identity/size/mtime.
    stamp = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
    require(stamp(before) == stamp(opened) == stamp(after) == stamp(current)
            and before.st_ctime_ns == current.st_ctime_ns
            and opened.st_ctime_ns == after.st_ctime_ns,
            "file changed while hashing: " + str(path))
    return before.st_size, digest.hexdigest()


def expected_fingerprint(item):
    require(type(item.get("size")) is int and item["size"] >= 0, "size must be a nonnegative integer")
    digest = item.get("sha256")
    require(isinstance(digest, str) and re.fullmatch(r"[0-9a-fA-F]{64}", digest), "invalid sha256")
    return item["size"], digest.lower()


def absolute_path(value):
    require(isinstance(value, (str, os.PathLike)), "invalid path")
    return Path(os.path.abspath(value))


def load_json(path):
    # Reject duplicate object keys instead of silently accepting a shadowed field.
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    safe_chain(path)
    fingerprint(path)
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique)


def check_validation(context):
    validation = context["validation"]
    require(fingerprint(validation)[1] == context["validation_sha256"], "validation fingerprint changed")
    record = load_json(validation)
    require(isinstance(record, dict) and record.get("status") in PASS_STATUSES, "validation has not passed")


def check_context(context):
    safe_chain(context["root"])
    require(context["root"].is_dir(), "task root is not a directory")
    for owned in context["owned"]:
        safe_chain(owned)
        require(owned.is_dir(), "owned root is not a directory")
    for protected in context["protected"]:
        safe_chain(protected)
    require(fingerprint(context["plan_path"])[1] == context["plan_sha256"], "plan changed")
    check_validation(context)
    if context["journal"] is not None:
        safe_chain(context["journal"], missing_leaf=True)


def check_item(context, item):
    path = item["absolute_path"]
    require(any(path.is_relative_to(owned) for owned in context["owned"]), "candidate is not task-owned")
    for protected in context["protected"] + context["keepers"]:
        require(path != protected and not path.is_relative_to(protected), "candidate is protected: " + str(path))
    require(fingerprint(path) == item["fingerprint"], "candidate fingerprint changed: " + str(path))
    if item.get("keeper_path") is not None:
        require(fingerprint(item["keeper_path"]) == item["fingerprint"], "keeper missing or different")


def preflight(plan_path, journal_path, apply):
    plan_path = absolute_path(plan_path)
    plan_hash = fingerprint(plan_path)[1]
    plan = load_json(plan_path)
    require(isinstance(plan, dict), "plan must be a JSON object")
    value = plan.get("root")
    require(isinstance(value, str) and Path(value).is_absolute(), "root must be absolute")
    require(".." not in Path(value).parts, "root contains parent traversal")
    root = Path(value)
    require(root != Path(root.anchor), "drive/filesystem root forbidden")
    safe_chain(root)
    require(root.is_dir(), "root must be an existing task directory")
    require(plan.get("workers_stopped") is True, "workers_stopped must be true")
    owned_values, protected_values = plan.get("owned_roots"), plan.get("protected")
    require(isinstance(owned_values, list) and bool(owned_values), "owned_roots must be nonempty")
    require(isinstance(protected_values, list) and bool(protected_values), "protected must be nonempty")
    owned = [relative_path(root, value) for value in owned_values]
    protected = [relative_path(root, value) for value in protected_values]
    validation = plan.get("validation")
    require(isinstance(validation, dict), "validation record required")
    validation_path = relative_path(root, validation.get("path"))
    validation_hash = validation.get("sha256")
    require(isinstance(validation_hash, str) and re.fullmatch(r"[0-9a-fA-F]{64}", validation_hash), "invalid validation sha256")
    journal = None
    require(not apply or journal_path is not None, "--apply requires --journal")
    if journal_path is not None:
        journal = absolute_path(journal_path)
        require(journal != root and journal.is_relative_to(root), "journal must be inside task root")
        safe_chain(journal, missing_leaf=True)
        require(not journal.exists(), "journal already exists; never overwrite")
    protected.extend([plan_path, validation_path])
    if journal is not None:
        protected.append(journal)
    # Missing journal is the only protected path allowed not to exist.
    context = dict(root=root, owned=owned, protected=protected, validation=validation_path,
                   validation_sha256=validation_hash.lower(), plan_path=plan_path,
                   plan_sha256=plan_hash, journal=journal, keepers=[])
    for protected_path in protected:
        safe_chain(protected_path, missing_leaf=(protected_path == journal))
    require(isinstance(plan.get("items"), list), "items must be a list")
    items, paths = [], set()
    for raw in plan["items"]:
        require(isinstance(raw, dict), "item must be an object")
        item = dict(raw)
        item.pop("keeper_path", None)  # Internal fields never come from plan data.
        path = relative_path(root, item.get("path"))
        require(path not in paths, "duplicate candidate path")
        paths.add(path)
        item.update(absolute_path=path, fingerprint=expected_fingerprint(item))
        if item.get("reason") == "duplicate":
            keeper = relative_path(root, item.get("keeper"))
            require(path != keeper, "keeper must be a different file")
            item["keeper_path"] = keeper
            context["keepers"].append(keeper)
        elif item.get("reason") == "temporary":
            require(path.suffix.lower() in TEMPORARY_SUFFIXES,
                    "unregistered temporary file type: " + item["path"]
                    + "; allowed suffixes: " + ", ".join(sorted(TEMPORARY_SUFFIXES)))
            require(isinstance(item.get("generator"), str) and bool(item["generator"].strip()), "temporary file needs generator provenance")
        else:
            raise ValueError("unknown cleanup reason")
        items.append(item)
    require(not paths.intersection(context["keepers"]), "keeper is also in deletion set (including cycles)")
    # Journal is absent during preflight; protect it without treating it as an existing artifact.
    protected_without_journal = [p for p in protected if p != journal]
    context["protected"] = protected_without_journal
    check_context(context)
    context["protected"] = protected
    for item in items:
        check_item(context, item)
    context["items"] = items
    context["items_sha256"] = sha256_bytes(json.dumps(plan["items"], sort_keys=True, ensure_ascii=True,
                                                     separators=(",", ":")).encode("utf-8"))
    return context


def write_event(stream, event):
    stream.write(json.dumps(event, ensure_ascii=True, sort_keys=True) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def execute(plan_path, apply=False, journal_path=None):
    result = dict(status="rejected", planned_bytes=0, logical_bytes_removed=0, deleted_count=0)
    try:
        context = preflight(plan_path, journal_path, apply)
        result["planned_bytes"] = sum(item["size"] for item in context["items"])
    except (OSError, ValueError, TypeError) as exc:
        result["error"] = str(exc)
        return result
    if not apply:
        result["status"] = "dry_run"
        return result
    try:
        # Exclusive creation protects an existing journal, including a concurrent creator.
        with context["journal"].open("x", encoding="utf-8", newline="\n") as stream:
            try:
                write_event(stream, dict(event="plan", root=str(context["root"]),
                                         plan_sha256=context["plan_sha256"],
                                         items_sha256=context["items_sha256"],
                                         planned_bytes=result["planned_bytes"],
                                         items=[{k: v for k, v in item.items()
                                                 if k not in {"absolute_path", "fingerprint", "keeper_path"}}
                                                for item in context["items"]]))
                for item in context["items"]:
                    check_context(context)
                    check_item(context, item)
                    item["absolute_path"].unlink()
                    result["logical_bytes_removed"] += item["size"]
                    result["deleted_count"] += 1
                    write_event(stream, dict(event="deleted", path=item["path"],
                                             size=item["size"], sha256=item["sha256"]))
                result["status"] = "complete"
            except (OSError, ValueError, TypeError) as exc:
                result.update(status="partial", error=str(exc))
            write_event(stream, dict(event="result", **result))
    except (OSError, ValueError, TypeError) as exc:
        result.update(status="partial" if result["deleted_count"] else "rejected", error=str(exc))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--journal", type=Path)
    args = parser.parse_args()
    result = execute(args.plan, apply=args.apply, journal_path=args.journal)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["status"] in {"dry_run", "complete"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
