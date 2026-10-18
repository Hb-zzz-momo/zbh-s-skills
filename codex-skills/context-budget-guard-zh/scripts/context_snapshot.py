"""Bounded local file observations. Hash equality is never domain verification."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat
import sys
import tempfile
import time

MAX_FILES = 64
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_CONTROL_BYTES = 128 * 1024
MAX_SECONDS = 2.0
KINDS = {'code', 'evidence', 'requirement', 'report', 'environment', 'map'}


class Unknown(Exception):
    pass


def require(condition, reason):
    if not condition:
        raise Unknown(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


@lru_cache(maxsize=1)
def windows_api():
    import ctypes
    from ctypes import wintypes

    class BasicInfo(ctypes.Structure):
        _fields_ = [('creation', ctypes.c_int64), ('access', ctypes.c_int64),
                    ('write', ctypes.c_int64), ('change', ctypes.c_int64),
                    ('attributes', wintypes.DWORD)]

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                   wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.GetFileInformationByHandleEx.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                                   wintypes.LPVOID, wintypes.DWORD]
    kernel.GetFileInformationByHandleEx.restype = wintypes.BOOL
    kernel.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
    kernel.GetDriveTypeW.restype = wintypes.UINT
    return ctypes, kernel, BasicInfo


@contextmanager
def windows_handle(path, share, access=0x80):
    ctypes, kernel, BasicInfo = windows_api()
    # Read attributes, never write; open the reparse point itself, not its target.
    handle = kernel.CreateFileW(str(path), access, share, None, 3, 0x02200000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        info = BasicInfo()
        if not kernel.GetFileInformationByHandleEx(handle, 0, ctypes.byref(info), ctypes.sizeof(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        require(not info.attributes & 0x400, 'reparse path unsupported: ' + str(path))
        yield info
    finally:
        kernel.CloseHandle(handle)


def file_stamp(path):
    value = path.stat()
    base = (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    if os.name == 'nt':
        # st_ctime on Windows is creation time, not the actual NTFS ChangeTime.
        # Share read/write/delete: the observation must not deny other writers.
        with windows_handle(path, 7) as info:
            return base + (info.change,)
    return base


@contextmanager
def pin_record_directory(cache):
    from contextlib import ExitStack
    require(os.name == 'nt', 'record directory pinning is supported on Windows only')
    # Pin ancestors before children, so a reparse swap cannot redirect later writes.
    # Share read/write, exclude delete/rename only; no input file write locks.
    with ExitStack() as stack:
        for directory in reversed((cache, *cache.parents)):
            # Attribute-only handles do not enforce all Windows sharing checks.
            stack.enter_context(windows_handle(directory, 3, access=0x80000000))
        reject_links(cache)
        yield


def local_root(raw):
    require(not str(raw).startswith(('\\\\', '//')), 'network/device root unsupported')
    root = Path(os.path.abspath(raw))
    require(root.is_dir(), 'project root missing')
    reject_links(root)
    if os.name == 'nt':
        _, kernel, _ = windows_api()
        require(kernel.GetDriveTypeW(root.anchor) != 4, 'mapped network drive unsupported')
    return root


def reject_links(path):
    # Inspect all existing ancestors, including Windows junctions/cloud reparse points.
    for node in (path, *path.parents):
        try:
            info = node.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and not
                (getattr(info, 'st_file_attributes', 0) & 0x400),
                'symlink/reparse path unsupported: ' + str(node))


def safe_path(root, relative):
    require(isinstance(relative, str) and 0 < len(relative) <= 512, 'invalid relative path')
    parts = relative.replace('\\', '/').split('/')
    require(not PureWindowsPath(relative).drive and not PurePosixPath(relative).is_absolute(),
            'absolute path unsupported')
    require(all(p and p not in {'.', '..'} and not any(c in p for c in '*?[]:')
                for p in parts), 'path traversal/wildcard/device path unsupported')
    path = root.joinpath(*parts)
    reject_links(path)
    require(path.resolve().is_relative_to(root.resolve()), 'path escaped project root')
    return path


def stable_bytes(path, maximum, deadline):
    require(time.monotonic() <= deadline, 'time budget exceeded')
    reject_links(path)
    before = path.stat()
    before_stamp = file_stamp(path)
    require(stat.S_ISREG(before.st_mode), 'not a regular file: ' + str(path))
    require(before.st_size <= maximum, 'file budget exceeded: ' + str(path))
    chunks = []
    total = 0
    with path.open('rb') as handle:
        while True:
            require(time.monotonic() <= deadline, 'time budget exceeded')
            block = handle.read(min(65536, maximum + 1 - total))
            if not block:
                break
            total += len(block)
            require(total <= maximum, 'file grew beyond budget')
            chunks.append(block)
        after_open = os.fstat(handle.fileno())
    after = path.stat()
    fingerprint = lambda x: (x.st_dev, x.st_ino, x.st_size, x.st_mtime_ns, x.st_ctime_ns)
    # Windows path stat and handle fstat can round creation-time differently.
    identity = lambda x: (x.st_dev, x.st_ino, x.st_size, x.st_mtime_ns)
    require(identity(before) == identity(after_open) == identity(after) and
            fingerprint(before) == fingerprint(after),
            'file changed while reading: ' + str(path))
    after_stamp = file_stamp(path)
    require(before_stamp == after_stamp, 'file change stamp changed while reading: ' + str(path))
    return b''.join(chunks), after_stamp


def load_json(path, deadline):
    raw, stamp = stable_bytes(path, MAX_CONTROL_BYTES, deadline)
    value = json.loads(raw.decode('utf-8-sig'))
    require(isinstance(value, dict), 'JSON object required')
    return value, hashlib.sha256(raw).hexdigest(), stamp


def validate_manifest(manifest):
    allowed = {'schema_version', 'scope_id', 'current_status', 'last_verified_at',
               'open_issues', 'external_dependencies', 'files', 'max_age_hours'}
    require(not (manifest.keys() - allowed), 'unknown manifest keys')
    require(manifest.get('schema_version') == 1, 'unsupported manifest version')
    for key in ('scope_id', 'current_status'):
        require(isinstance(manifest.get(key), str) and 0 < len(manifest[key]) <= 256,
                'invalid ' + key)
    for key in ('open_issues', 'external_dependencies'):
        entries = manifest.get(key)
        require(isinstance(entries, list) and len(entries) <= 64 and
                all(isinstance(x, str) and 0 < len(x) <= 512 for x in entries), 'invalid ' + key)
    verified = manifest.get('last_verified_at')
    require(verified is None or (isinstance(verified, str) and len(verified) <= 64),
            'invalid last_verified_at')
    age = manifest.get('max_age_hours', 24)
    require(type(age) in (int, float) and 0 < age <= 24, 'max_age_hours must be within (0,24]')
    files = manifest.get('files')
    require(isinstance(files, list) and 1 <= len(files) <= MAX_FILES, 'file count outside 1..64')
    seen = set()
    for item in files:
        require(isinstance(item, dict) and set(item) == {'path', 'kind', 'field'},
                'file requires exactly path/kind/field')
        require(item['kind'] in KINDS, 'unknown file kind')
        require(isinstance(item['field'], str) and 0 < len(item['field']) <= 128, 'invalid field')
        require(isinstance(item['path'], str), 'invalid file path')
        key = item['path'].replace('\\', '/').casefold()
        require(key not in seen, 'duplicate file path')
        seen.add(key)


def observe(root, cache, deadline):
    manifest_path = cache / 'manifest.json'
    manifest, manifest_hash, manifest_stamp = load_json(manifest_path, deadline)
    validate_manifest(manifest)
    files, stamps, total = {}, {}, 0
    for item in manifest['files']:
        path = safe_path(root, item['path'])
        require(path not in {manifest_path, cache / 'state.json', cache / '.state.lock'} and
                not path.name.startswith('.state-'), 'snapshot cannot watch its own control files')
        raw, stamp = stable_bytes(path, min(MAX_FILE_BYTES, MAX_TOTAL_BYTES - total), deadline)
        total += len(raw)
        files[item['path']] = {'sha256': hashlib.sha256(raw).hexdigest(),
                               'kind': item['kind'], 'field': item['field']}
        stamps[path] = stamp
    for path, stamp in {**stamps, manifest_path: manifest_stamp}.items():
        require(stamp == file_stamp(path),
                'inputs changed during observation')
    observation = {'schema_version': 1, 'root': str(root), 'scope_id': manifest['scope_id'],
                   'manifest_hash': manifest_hash, 'files': files}
    observation['evidence_hash'] = digest(observation)
    observation.update({key: manifest[key] for key in
                        ('current_status', 'open_issues', 'external_dependencies')})
    observation['last_verified_at'] = manifest.get('last_verified_at')
    observation['observed_at'] = datetime.now(timezone.utc).isoformat()
    return observation, manifest.get('max_age_hours', 24), total


def baseline(cache, deadline):
    path = cache / 'state.json'
    if not path.exists():
        return None
    value, _, _ = load_json(path, deadline)
    payload = {key: value[key] for key in
               ('schema_version', 'root', 'scope_id', 'manifest_hash', 'files')}
    require(value['evidence_hash'] == digest(payload), 'baseline integrity mismatch')
    require(value['schema_version'] == 1 and isinstance(value['files'], dict), 'invalid baseline')
    when = datetime.fromisoformat(value['observed_at'])
    require(when.tzinfo is not None, 'baseline timestamp needs timezone')
    return value


def comparison(current, previous, max_age):
    paths = sorted(set(current['files']) | set(previous['files'] if previous else {}))
    changed = [p for p in paths if not previous or
               current['files'].get(p) != previous['files'].get(p)]
    fields = {data[p]['field'] for p in changed for data in
              (current['files'], previous['files'] if previous else {}) if p in data}
    same_context = previous and all(current[k] == previous[k] for k in
                                   ('root', 'scope_id', 'manifest_hash'))
    if not same_context:
        fields.add('manifest_or_scope')
    if changed or not same_context:
        return 'CHANGED', changed, sorted(fields)
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(previous['observed_at'])).total_seconds()
    if not 0 <= age <= max_age * 3600 or current['open_issues'] or current['external_dependencies']:
        return 'REVIEW_REQUIRED', [], []
    return 'UNCHANGED', [], []


@contextmanager
def record_lock(cache):
    path = cache / '.state.lock'
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.close(descriptor)
        yield
    finally:
        path.unlink()


def atomic_record(cache, value):
    descriptor, temporary = tempfile.mkstemp(prefix='.state-', suffix='.tmp', dir=cache)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        reject_links(cache / 'state.json')
        os.replace(temporary, cache / 'state.json')
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run(args):
    started = time.monotonic()
    deadline = started + MAX_SECONDS
    root = local_root(args.root)
    cache = safe_path(root, args.cache_dir)
    require(cache.is_dir(), 'cache directory missing; initialize from templates first')
    require(not (cache / '.state.lock').exists(), 'record lock exists; inspect instead of clearing it')

    def process():
        previous = baseline(cache, deadline)
        current, max_age, total = observe(root, cache, deadline)
        status, changed, fields = comparison(current, previous, max_age)
        require(time.monotonic() <= deadline, 'time budget exceeded')
        if args.command == 'record':
            current['changed_fields'] = fields
            atomic_record(cache, current)
            status = 'RECORDED'
        return {'status': status, 'message': '无变化' if status == 'UNCHANGED' else status,
                'can_skip_repeated_analysis': status == 'UNCHANGED',
                'scope_id': current['scope_id'], 'evidence_hash': current['evidence_hash'],
                'current_status': current['current_status'], 'changed_paths': changed,
                'changed_fields': fields, 'observed_bytes': total,
                'elapsed_ms': round((time.monotonic() - started) * 1000, 2),
                'coverage': 'explicit_files_only; no domain or external verification'}

    if args.command == 'record':
        with pin_record_directory(cache), record_lock(cache):
            return process()
    return process()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('check', 'record'))
    parser.add_argument('--root', required=True)
    parser.add_argument('--cache-dir', default='.context-cache', help='existing project-relative directory')
    args = parser.parse_args()
    try:
        result = run(args)
    except (Unknown, OSError, ValueError, KeyError, TypeError) as exc:
        result = {'status': 'UNKNOWN', 'can_skip_repeated_analysis': False,
                  'reason': str(exc), 'fallback': 'use normal targeted reads and required validation'}
    print(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
    return 0 if result['status'] in {'UNCHANGED', 'RECORDED'} else 2 if result['status'] == 'UNKNOWN' else 1


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
