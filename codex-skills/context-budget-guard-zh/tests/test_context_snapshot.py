import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'context_snapshot.py'


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cache = self.root / '.context-cache'
        self.cache.mkdir()
        (self.root / '原始结果.txt').write_text('Dice=0.8123\n', encoding='utf-8')
        self.manifest = {
            'schema_version': 1, 'scope_id': 'project-A/student-A',
            'current_status': '待核验', 'last_verified_at': None,
            'open_issues': [], 'external_dependencies': [],
            'files': [{'path': '原始结果.txt', 'kind': 'evidence', 'field': 'results'}],
        }
        self.save_manifest()

    def save_manifest(self):
        (self.cache / 'manifest.json').write_text(json.dumps(self.manifest), encoding='utf-8')

    def cli(self, command='check', code=None):
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), command,
                                 '--root', str(self.root)], capture_output=True, encoding='utf-8')
        if code is not None:
            self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertLessEqual(len(result.stdout.splitlines()), 1)
        return data

    def test_first_check_does_not_write(self):
        self.assertEqual(self.cli(code=1)['status'], 'CHANGED')
        self.assertFalse((self.cache / 'state.json').exists())

    def test_record_then_unchanged_is_read_only(self):
        recorded = self.cli('record', 0)
        state = self.cache / 'state.json'
        before = state.read_bytes()
        result = self.cli(code=0)
        self.assertEqual(result['status'], 'UNCHANGED')
        self.assertTrue(result['can_skip_repeated_analysis'])
        self.assertEqual(state.read_bytes(), before)
        self.assertEqual(recorded['current_status'], '待核验')
        self.assertIsNone(json.loads(before)['last_verified_at'])

    def test_same_size_and_mtime_change_detected(self):
        self.cli('record', 0)
        source = self.root / '原始结果.txt'
        stamp = source.stat()
        source.write_text('Dice=0.7123\n', encoding='utf-8')
        os.utime(source, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        data = self.cli(code=1)
        self.assertEqual(data['status'], 'CHANGED')
        self.assertEqual(data['changed_fields'], ['results'])

    def test_check_never_advances_baseline(self):
        self.cli('record', 0)
        before = (self.cache / 'state.json').read_bytes()
        (self.root / '原始结果.txt').write_text('new', encoding='utf-8')
        self.cli(code=1)
        self.cli(code=1)
        self.assertEqual(before, (self.cache / 'state.json').read_bytes())

    def test_missing_file_unknown_preserves_baseline(self):
        self.cli('record', 0)
        before = (self.cache / 'state.json').read_bytes()
        (self.root / '原始结果.txt').unlink()
        self.assertEqual(self.cli('record', 2)['status'], 'UNKNOWN')
        self.assertEqual(before, (self.cache / 'state.json').read_bytes())

    def test_open_issue_and_external_dependency_prevent_shortcut(self):
        for field in ['open_issues', 'external_dependencies']:
            with self.subTest(field=field):
                self.manifest[field] = ['待人工复核' if field == 'open_issues' else 'teacher-platform']
                self.save_manifest()
                self.cli('record', 0)
                data = self.cli(code=1)
                self.assertEqual(data['status'], 'REVIEW_REQUIRED')
                self.assertFalse(data['can_skip_repeated_analysis'])
                self.manifest[field] = []

    def test_manifest_and_scope_change_detected(self):
        self.cli('record', 0)
        self.manifest['scope_id'] = 'project-A/student-B'
        self.save_manifest()
        self.assertEqual(self.cli(code=1)['status'], 'CHANGED')

    def test_invalid_empty_duplicate_escape_or_wildcard_manifest(self):
        for paths in [[], ['原始结果.txt', '原始结果.txt'], ['../escape'], ['*.txt'], ['C:/outside']]:
            with self.subTest(paths=paths):
                self.manifest['files'] = [{'path': p, 'kind': 'code', 'field': 'x'} for p in paths]
                self.save_manifest()
                self.assertEqual(self.cli(code=2)['status'], 'UNKNOWN')

    def test_large_file_and_too_many_files_rejected(self):
        source = self.root / '原始结果.txt'
        with source.open('wb') as handle:
            handle.truncate(8 * 1024 * 1024 + 1)
        self.cli(code=2)
        self.manifest['files'] = [{'path': f'f{i}', 'kind': 'code', 'field': 'x'} for i in range(65)]
        self.save_manifest()
        self.cli(code=2)

    def test_corrupt_and_stale_baseline_no_shortcut(self):
        self.cli('record', 0)
        path = self.cache / 'state.json'
        old = json.loads(path.read_text(encoding='utf-8'))
        path.write_text('{', encoding='utf-8')
        self.cli(code=2)
        path.write_text(json.dumps(old), encoding='utf-8')
        old['observed_at'] = '2000-01-01T00:00:00+00:00'
        path.write_text(json.dumps(old), encoding='utf-8')
        self.assertEqual(self.cli(code=1)['status'], 'REVIEW_REQUIRED')

    def test_lock_blocks_record_and_check(self):
        (self.cache / '.state.lock').write_text('held')
        self.cli('record', 2)
        self.cli(code=2)
        self.assertEqual((self.cache / '.state.lock').read_text(), 'held')

    def test_symlink_file_and_cache_rejected(self):
        target = self.root / 'real'
        target.write_text('real')
        link = self.root / 'link'
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest('symlink privileges unavailable')
        self.manifest['files'][0]['path'] = 'link'
        self.save_manifest()
        self.cli(code=2)

    def test_import_has_no_side_effect(self):
        spec = importlib.util.spec_from_file_location('snapshot_test', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertFalse((self.cache / 'state.json').exists())

    def module(self):
        spec = importlib.util.spec_from_file_location('snapshot_race', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @unittest.skipUnless(os.name == 'nt', 'Windows ChangeTime regression')
    def test_write_after_read_with_restored_mtime_is_unknown(self):
        self.cli('record', 0)
        module = self.module()
        original = module.stable_bytes
        source = self.root / '原始结果.txt'
        stamp = source.stat()

        def interleaved(path, maximum, deadline):
            result = original(path, maximum, deadline)
            if path == source:
                source.write_text('Dice=0.7123\n', encoding='utf-8')
                os.utime(source, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
            return result

        module.stable_bytes = interleaved
        args = type('Args', (), {'root': str(self.root), 'cache_dir': '.context-cache',
                                  'command': 'check'})()
        with self.assertRaises(module.Unknown):
            module.run(args)

    @unittest.skipUnless(os.name == 'nt', 'Windows directory pinning regression')
    def test_cache_swap_before_record_never_writes_outside(self):
        from contextlib import contextmanager
        module = self.module()
        original_lock = module.record_lock
        outside = self.root.parent / (self.root.name + '-outside')
        outside.mkdir()
        self.addCleanup(outside.rmdir)
        moved = self.root / 'old-cache'

        @contextmanager
        def swapped(cache):
            cache.rename(moved)
            try:
                cache.symlink_to(outside, target_is_directory=True)
                try:
                    with original_lock(cache):
                        self.fail('lock entered through replaced cache')
                finally:
                    cache.unlink()
            finally:
                moved.rename(cache)
            yield

        module.record_lock = swapped
        args = type('Args', (), {'root': str(self.root), 'cache_dir': '.context-cache',
                                  'command': 'record'})()
        with self.assertRaises(OSError):
            module.run(args)
        self.assertEqual(list(outside.iterdir()), [])

    @unittest.skipUnless(os.name == 'nt', 'Windows noninterference')
    def test_directory_pin_allows_writes_and_releases(self):
        module = self.module()
        moved = self.root / 'moved-cache'
        with module.pin_record_directory(self.cache):
            (self.cache / 'ordinary-save.txt').write_text('normal writes allowed')
            (self.root / '原始结果.txt').write_text('input writes allowed', encoding='utf-8')
            with self.assertRaises(OSError):
                self.cache.rename(moved)
        self.cache.rename(moved)
        moved.rename(self.cache)


if __name__ == '__main__':
    unittest.main()
