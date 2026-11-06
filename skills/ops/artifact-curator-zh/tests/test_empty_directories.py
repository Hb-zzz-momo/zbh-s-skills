"""Safety regressions for explicitly scoped empty-directory cleanup."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'empty_directories.py'
spec = importlib.util.spec_from_file_location('empty_directories', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class EmptyDirectoriesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'project'
        self.root.mkdir()
        self.journal = Path(self.tmp.name) / 'journal.jsonl'

    def directory(self, name):
        p = self.root / name
        p.mkdir(parents=True, exist_ok=True)
        return p

    def test_nested_empty_tree_removed_but_hidden_zero_byte_file_kept(self):
        self.directory('obsolete/a/b')
        self.directory('active').joinpath('.keep').write_bytes(b'')
        plan = m.scan(self.root, [])
        self.assertEqual({x['path'] for x in plan['items']},
                         {'obsolete', 'obsolete/a', 'obsolete/a/b'})
        m.execute(plan, self.journal, workers_stopped=True)
        self.assertFalse((self.root / 'obsolete').exists())
        self.assertEqual((self.root / 'active/.keep').read_bytes(), b'')
        self.assertTrue(self.root.is_dir())
        self.assertEqual(sum(json.loads(x)['event'] == 'removed'
                             for x in self.journal.read_text().splitlines()), 3)

    def test_protected_engine_and_backup_not_traversed(self):
        self.directory('engine/assets/empty')
        self.directory('backup/empty')
        self.directory('ordinary')
        plan = m.scan(self.root, ['engine'])
        self.assertEqual([x['path'] for x in plan['items']], ['ordinary'])

    def test_dry_run_is_read_only(self):
        self.directory('empty')
        plan = m.scan(self.root, [])
        m.preflight(plan)
        self.assertTrue((self.root / 'empty').is_dir())
        self.assertFalse(self.journal.exists())

    def test_new_file_anywhere_in_plan_rejects_whole_batch(self):
        self.directory('first')
        self.directory('second')
        plan = m.scan(self.root, [])
        (self.root / 'second/new.txt').write_text('keep')
        with self.assertRaises(ValueError):
            m.execute(plan, self.journal, workers_stopped=True)
        self.assertTrue((self.root / 'first').is_dir())
        self.assertFalse(self.journal.exists())

    def test_no_writer_acknowledgement_rejected(self):
        plan = m.scan(self.root, [])
        with self.assertRaises(ValueError):
            m.execute(plan, self.journal, workers_stopped=False)

    def test_traversal_duplicate_and_root_rejected(self):
        self.directory('empty')
        for bad in ('../outside', '.', 'empty/..', '/absolute', 'C:/outside'):
            plan = m.scan(self.root, [])
            plan['items'][0]['path'] = bad
            with self.assertRaises(ValueError):
                m.preflight(plan)
        plan = m.scan(self.root, [])
        plan['items'].append(plan['items'][0].copy())
        with self.assertRaises(ValueError):
            m.preflight(plan)

    def test_unknown_enumeration_does_not_make_parent_empty(self):
        self.directory('parent/unreadable')
        original = m.names
        def read(p):
            if Path(p).name == 'unreadable':
                raise PermissionError('test read denied')
            return original(p)
        with patch.object(m, 'names', side_effect=read):
            plan = m.scan(self.root, [])
        self.assertEqual(plan['items'], [])
        self.assertEqual(plan['unknown'][0]['path'], 'parent/unreadable')

    def test_partial_failure_stops_and_keeps_journal(self):
        self.directory('a')
        self.directory('b')
        plan = m.scan(self.root, [])
        original = m.remove_empty
        def remove(p):
            if Path(p).name == 'b':
                raise PermissionError('test locked')
            original(p)
        with patch.object(m, 'remove_empty', side_effect=remove):
            with self.assertRaises(PermissionError):
                m.execute(plan, self.journal, workers_stopped=True)
        self.assertFalse((self.root / 'a').exists())
        self.assertTrue((self.root / 'b').is_dir())
        self.assertEqual(json.loads(self.journal.read_text().splitlines()[-1])['event'], 'partial')

    def test_links_never_followed(self):
        target = Path(self.tmp.name) / 'outside'
        target.mkdir()
        try:
            (self.root / 'link').symlink_to(target, target_is_directory=True)
        except OSError as e:
            self.skipTest(f'Host cannot create symlink: {e}')
        plan = m.scan(self.root, [])
        self.assertEqual(plan['items'], [])
        self.assertTrue(plan['unknown'])
        self.assertTrue(target.is_dir())

    def test_new_file_after_preflight_is_not_deleted(self):
        p = self.directory('empty')
        plan = m.scan(self.root, [])
        original = m.preflight
        def checked(value):
            result = original(value)
            (p / 'arrived.txt').write_text('keep')
            return result
        with patch.object(m, 'preflight', side_effect=checked):
            with self.assertRaises(ValueError):
                m.execute(plan, self.journal, workers_stopped=True)
        self.assertEqual((p / 'arrived.txt').read_text(), 'keep')
        self.assertEqual(json.loads(self.journal.read_text().splitlines()[-1])['event'], 'partial')

    def test_changed_directory_identity_rejected(self):
        p = self.directory('empty')
        plan = m.scan(self.root, [])
        p.rename(self.root / 'held')
        p.mkdir()
        with self.assertRaises(ValueError):
            m.preflight(plan)

    def test_existing_journal_never_overwritten(self):
        self.directory('empty')
        plan = m.scan(self.root, [])
        self.journal.write_text('previous evidence')
        with self.assertRaises(FileExistsError):
            m.execute(plan, self.journal, workers_stopped=True)
        self.assertEqual(self.journal.read_text(), 'previous evidence')
        self.assertTrue((self.root / 'empty').exists())

    def test_directory_paths_can_be_recreated_from_recorded_removals(self):
        self.directory('a/b/c')
        plan = m.scan(self.root, [])
        m.execute(plan, self.journal, workers_stopped=True)
        removed = [json.loads(x)['path'] for x in self.journal.read_text().splitlines()
                   if json.loads(x)['event'] == 'removed']
        for name in sorted(removed, key=lambda x: len(x.split('/'))):
            (self.root / name).mkdir()
        self.assertTrue((self.root / 'a/b/c').is_dir())

    @unittest.skipUnless(os.name == 'nt', 'Windows long-path regression')
    def test_long_paths_without_system_setting_change(self):
        current = self.root
        created = []
        try:
            for i in range(23):
                current = current / f'directory_{i:02}_long_name'
                os.mkdir(m.io_path(current))
                created.append(current)
            self.assertGreater(len(str(current).encode('utf-16-le')) // 2, 400)
            plan = m.scan(self.root, [])
            self.assertEqual(plan['unknown'], [])
            self.assertEqual(len(plan['items']), 23)
            m.preflight(plan)
            m.execute(plan, self.journal, workers_stopped=True, plan_file_sha256='a' * 64)
            start = json.loads(self.journal.read_text().splitlines()[0])
            self.assertEqual(start['plan_file_sha256'], 'a' * 64)
            self.assertIn('plan_content_sha256', start)
            self.assertFalse(os.path.lexists(m.io_path(created[0])))
        finally:
            for p in reversed(created):
                if os.path.lexists(m.io_path(p)):
                    os.rmdir(m.io_path(p))


if __name__ == '__main__':
    unittest.main()
