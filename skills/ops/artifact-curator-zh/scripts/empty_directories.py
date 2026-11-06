#!/usr/bin/env python3
"""Plan and remove confirmed empty directories only. Python 3.11+, stdlib.

No file deletion, recursive removal, cloud API, process control or force retry.
Callers must stop writers, review dependencies/references and freeze the plan.
Windows path checks reduce mistakes, not hostile concurrent ancestor swaps.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from datetime import datetime, timezone

SCHEMA = 'empty-directories-v1'
PROTECTED_NAMES = {'.git', '.hg', '.svn', 'backup', 'backups', '独立备份', '恢复备份'}
# Offline/recall directories can hide remote members; never assume them empty.
UNCERTAIN_ATTRIBUTES = 0x400 | 0x1000 | 0x40000 | 0x400000


def require(ok, message):
    if not ok:
        raise ValueError(message)


def io_path(p):
    s = str(p)
    if os.name == 'nt':
        return '\\\\?\\UNC\\' + s[2:] if s.startswith('\\\\') else '\\\\?\\' + s
    return s


def clean_absolute(value):
    p = Path(value)
    require(p.is_absolute() and str(p) == os.path.abspath(str(p)), 'Noncanonical absolute path')
    require(not str(p).startswith(('\\\\?\\', '\\\\.\\')), 'Device paths not accepted')
    return p


def checked_stat(p, directory=False):
    s = os.lstat(io_path(p))  # fresh result, not cached DirEntry.stat
    require(not stat.S_ISLNK(s.st_mode), f'Link rejected: {p}')
    require(not getattr(s, 'st_file_attributes', 0) & UNCERTAIN_ATTRIBUTES,
            f'Reparse/offline/recall state unknown: {p}')
    if directory:
        require(stat.S_ISDIR(s.st_mode), f'Not a directory: {p}')
        require(s.st_ino != 0, f'Directory identity unavailable: {p}')
    return s


def safe_chain(p):
    for part in reversed([p, *p.parents]):
        checked_stat(part, directory=True)
    resolved = str(Path(io_path(p)).resolve(strict=True))
    if os.name == 'nt':
        if resolved.startswith('\\\\?\\UNC\\'):
            resolved = '\\\\' + resolved[8:]
        elif resolved.startswith('\\\\?\\'):
            resolved = resolved[4:]
    require(os.path.normcase(resolved) == os.path.normcase(str(p)),
            f'Path alias rejected: {p}')


def identity(p):
    s = checked_stat(p, directory=True)
    return [s.st_dev, s.st_ino]


def relative(value):
    require(isinstance(value, str), 'Path must be text')
    p = PurePosixPath(value)
    require(value and str(p) == value and not p.is_absolute() and
            all(x not in ('', '.', '..') and ':' not in x and '\\' not in x and
                not x.endswith((' ', '.')) for x in value.split('/')),
            f'Unsafe relative path: {value}')
    return p


def below(value, parent):
    a, b = value.casefold(), parent.casefold()
    return a == b or a.startswith(b + '/')


def names(p):
    with os.scandir(io_path(p)) as entries:
        return sorted(e.name for e in entries)


def remove_empty(p):
    os.rmdir(io_path(p))


def scan(root, protected):
    root = clean_absolute(root)
    require(root.parent != root, 'Volume root rejected')
    safe_chain(root)
    require(not any(x.casefold() in PROTECTED_NAMES for x in root.parts),
            'Root inside a protected backup/version-control location')
    protected = [str(relative(x)) for x in protected]
    for r in protected:
        require(os.path.lexists(io_path(root / r)), f'Protected path missing: {r}')
    plan = dict(schema=SCHEMA, root=str(root), root_id=identity(root),
                protected=protected, directories={}, items=[], unknown=[], skipped=[])

    def walk(p, rel):
        if rel and (any(below(rel, x) for x in protected) or p.name.casefold() in PROTECTED_NAMES):
            plan['skipped'].append(rel)
            return False
        try:
            before = identity(p)
            plan['directories'][rel] = before
            children = names(p)
            removable = True
            for name in children:
                child, sub = p / name, f'{rel}/{name}' if rel else name
                try:
                    s = checked_stat(child)
                    if stat.S_ISDIR(s.st_mode):
                        if not walk(child, sub):
                            removable = False
                    else:
                        removable = False  # includes zero-byte, hidden and special files
                except (OSError, ValueError) as e:
                    plan['unknown'].append(dict(path=sub, error=str(e)))
                    removable = False
            require(identity(p) == before and names(p) == children,
                    f'Directory changed during scan: {p}')
            if removable and rel:
                plan['items'].append(dict(path=rel, identity=before))
            return removable
        except (OSError, ValueError) as e:
            plan['unknown'].append(dict(path=rel, error=str(e)))
            # Drop any candidates below a subtree whose final enumeration failed.
            plan['items'] = [x for x in plan['items'] if not (not rel or below(x['path'], rel))]
            return False

    walk(root, '')
    plan['items'].sort(key=lambda x: (-len(relative(x['path']).parts), x['path'].casefold()))
    return plan


def validate_target(plan, root, item, allowed_children):
    rel = item['path']
    p = root.joinpath(*relative(rel).parts)
    require(not any(below(rel, x) or below(x, rel) for x in plan['protected']),
            f'Protected path/ancestor: {rel}')
    require(not any(x.casefold() in PROTECTED_NAMES for x in p.parts), 'Protected name')
    safe_chain(p)
    for ancestor in [p, *p.parents]:
        if ancestor == root.parent:
            break
        key = '' if ancestor == root else ancestor.relative_to(root).as_posix()
        require(identity(ancestor) == plan['directories'].get(key), f'Identity changed: {ancestor}')
    require(identity(p) == item['identity'], f'Candidate identity changed: {rel}')
    for name in names(p):
        child = p / name
        sub = f'{rel}/{name}'
        require(sub in allowed_children, f'Unexpected member (not empty): {sub}')
        checked_stat(child, directory=True)
    return p


def preflight(plan):
    require(plan.get('schema') == SCHEMA, 'Unknown plan schema')
    root = clean_absolute(plan['root'])
    require(root.parent != root, 'Volume root rejected')
    safe_chain(root)
    require(identity(root) == plan['root_id'] == plan['directories'].get(''), 'Root identity changed')
    for x in plan['protected']:
        relative(x)
    items = plan['items']
    paths = [str(relative(x['path'])) for x in items]
    require(len(set(x.casefold() for x in paths)) == len(paths), 'Duplicate/case-alias candidates')
    require(items == sorted(items, key=lambda x: (-len(relative(x['path']).parts), x['path'].casefold())),
            'Candidates must be bottom-up')
    for item in items:
        validate_target(plan, root, item, set(paths))
    return root


def safe_output(path):
    p = clean_absolute(path)
    safe_chain(p.parent)
    if os.name == 'nt':
        require(p.drive.casefold() == 'd:', 'Nonconfiguration outputs must be on D:')
    return p


def write_json(path, value):
    p = safe_output(path)
    with open(io_path(p), 'x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def execute(plan, journal, workers_stopped=False, plan_file_sha256=None):
    require(workers_stopped, 'Stop consumers/writers before apply')
    root = preflight(plan)  # whole batch checked before any removal or log creation
    journal = safe_output(journal)
    require(not any(below(str(journal).replace('\\', '/'),
                          str(root / x['path']).replace('\\', '/')) for x in plan['items']),
            'Journal cannot be inside a candidate')
    removed = []
    with open(io_path(journal), 'x', encoding='utf-8') as f:
        def log(event, **kw):
            f.write(json.dumps(dict(event=event, utc=datetime.now(timezone.utc).isoformat(), **kw),
                               ensure_ascii=False) + '\n')
            f.flush()
            os.fsync(f.fileno())
        log('start', root=str(root), plan_file_sha256=plan_file_sha256, plan_content_sha256=hashlib.sha256(
            json.dumps(plan, sort_keys=True, ensure_ascii=False).encode()).hexdigest())
        try:
            for item in plan['items']:
                p = validate_target(plan, root, item, set())
                log('intent', path=item['path'])
                remove_empty(p)  # nonrecursive, refuses files or newly arrived children
                removed.append(item['path'])
                log('removed', path=item['path'])
            log('complete', count=len(removed))
        except (OSError, ValueError) as e:
            log('partial', removed=removed, error=str(e))
            raise
    return removed


def read_plan(path):
    p = clean_absolute(path)
    safe_chain(p.parent)
    s = checked_stat(p)
    require(stat.S_ISREG(s.st_mode), 'Plan must be a regular file')
    raw = Path(io_path(p)).read_bytes()
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique), hashlib.sha256(raw).hexdigest()


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    sub = cli.add_subparsers(dest='command', required=True)
    s = sub.add_parser('scan')
    s.add_argument('--root', required=True)
    s.add_argument('--protect', action='append', default=[])
    s.add_argument('--out', required=True)
    for name in ('check', 'apply'):
        p = sub.add_parser(name)
        p.add_argument('--plan', required=True)
        if name == 'apply':
            p.add_argument('--plan-sha256', required=True)
            p.add_argument('--journal', required=True)
            p.add_argument('--workers-stopped', action='store_true')
    a = cli.parse_args()
    try:
        if a.command == 'scan':
            plan = scan(a.root, a.protect)
            write_json(a.out, plan)
            result = dict(candidates=len(plan['items']), unknown=plan['unknown'], skipped=plan['skipped'])
        else:
            plan, digest = read_plan(a.plan)
            preflight(plan)
            if a.command == 'apply':
                require(digest == a.plan_sha256, 'Frozen plan SHA256 mismatch')
                removed = execute(plan, a.journal, a.workers_stopped, digest)
                result = dict(status='complete', removed=len(removed))
            else:
                result = dict(status='dry-run', candidates=len(plan['items']), sha256=digest)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(json.dumps(dict(status='ERROR', error=str(e)), ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
