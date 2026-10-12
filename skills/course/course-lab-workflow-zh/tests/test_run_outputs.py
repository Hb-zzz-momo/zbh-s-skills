"""Diagnostic and completion-gate regression tests; fixtures are synthetic."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('run_audit', ROOT / 'scripts/audit_run_outputs.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class OutputGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.requirements = self.root / 'requirements.txt'
        self.requirements.write_text('Synthetic fixture: execute one cell and verify its result.', encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def notebook(self, outputs=None, count=1, source='1 + 1'):
        path = self.root / 'run.ipynb'
        path.write_text(json.dumps({'nbformat': 4, 'nbformat_minor': 5,
            'cells': [{'cell_type': 'code', 'source': source, 'execution_count': count, 'outputs': outputs or []}],
            'metadata': {}}), encoding='utf-8')
        return path

    def ref(self, path, **extra):
        return {'path': str(path), 'sha256': audit.file_hash(path), **extra}

    def checklist(self, path, status='passed'):
        return {'requirements_basis': [self.ref(self.requirements)],
                'checks': [{'id': 'fixture-execution', 'required': True,
                            'status': status, 'evidence': [self.ref(path)]}]}

    def review(self, result, decision='expected'):
        return {'reviews': [{'finding_id': result['findings'][0]['id'], 'decision': decision,
                'reason': 'Synthetic fixture purpose', 'impact': 'Expected fixture message only',
                'basis': 'Explicit requirement in synthetic requirements.txt',
                'evidence': [self.ref(self.requirements)]}]}

    def test_numeric_result_plus_futurewarning_is_not_pass(self):
        path = self.notebook([{'output_type': 'stream', 'name': 'stderr', 'text': 'sklearn.py:12: FutureWarning: penalty deprecated\n'},
                             {'output_type': 'execute_result', 'data': {'text/plain': '0.6610169491525424'}}])
        result = audit.audit_outputs([path], [], [], expected_code_cells=1, checklist=self.checklist(path))
        self.assertEqual(result['diagnostics_status'], 'BLOCK')
        self.assertEqual(result['warning_count'], 1)
        self.assertFalse(result['can_claim_full_completion'])

    def test_warning_on_stdout_is_detected(self):
        path = self.notebook([{'output_type': 'stream', 'name': 'stdout', 'text': 'ConvergenceWarning: limit reached\n'}])
        result = audit.audit_outputs([path], [], [])
        self.assertEqual(result['warning_count'], 1)
        self.assertEqual(result['diagnostics_status'], 'BLOCK')

    def test_source_and_data_label_are_not_runtime_warnings(self):
        path = self.notebook([{'output_type': 'execute_result', 'data': {'text/plain': 'Warning Error deprecated'}}], source='# FutureWarning: example comment\n1 + 1')
        result = audit.audit_outputs([path], [], [])
        self.assertEqual(result['findings'], [])
        self.assertFalse(result['can_claim_full_completion'])

    def test_unexplained_stderr_is_reviewed(self):
        path = self.notebook([{'output_type': 'stream', 'name': 'stderr', 'text': 'unrecognized native diagnostic'}])
        self.assertEqual(audit.audit_outputs([path], [], [])['diagnostics_status'], 'BLOCK')

    def test_expected_stderr_is_kept_and_may_pass(self):
        path = self.notebook([{'output_type': 'stream', 'name': 'stderr', 'text': '100% progress'}])
        initial = audit.audit_outputs([path], [], [])
        result = audit.audit_outputs([path], [], [], reviews=self.review(initial), checklist=self.checklist(path))
        self.assertEqual(result['completion_status'], 'PASS')
        self.assertEqual(result['stderr_count'], 1)
        self.assertEqual(result['findings'][0]['message'], '100% progress')

    def test_nonblocking_warning_still_means_caution(self):
        path = self.notebook([{'output_type': 'stream', 'name': 'stderr', 'text': 'FutureWarning: compatibility\n'}])
        initial = audit.audit_outputs([path], [], [])
        result = audit.audit_outputs([path], [], [], reviews=self.review(initial, 'nonblocking'), checklist=self.checklist(path))
        self.assertEqual(result['completion_status'], 'CAUTION')
        self.assertEqual(result['warning_count'], 1)
        self.assertFalse(result['can_claim_full_completion'])

    def test_unexpected_exception_cannot_be_softened(self):
        path = self.notebook([{'output_type': 'error', 'ename': 'ValueError', 'evalue': 'bad dimensions', 'traceback': ['ValueError: bad dimensions']}])
        initial = audit.audit_outputs([path], [], [])
        result = audit.audit_outputs([path], [], [], reviews=self.review(initial, 'nonblocking'), checklist=self.checklist(path))
        self.assertEqual(result['completion_status'], 'BLOCK')

    def test_expected_exception_requires_basis_and_keeps_count(self):
        path = self.notebook([{'output_type': 'error', 'ename': 'ValueError', 'evalue': 'intentional fixture'}])
        initial = audit.audit_outputs([path], [], [])
        result = audit.audit_outputs([path], [], [], reviews=self.review(initial), checklist=self.checklist(path))
        self.assertEqual(result['completion_status'], 'PASS')
        self.assertEqual(result['error_count'], 1)

    def test_unexecuted_cell_blocks_even_with_filled_output(self):
        path = self.notebook([{'output_type': 'execute_result', 'data': {'text/plain': '2'}}], count=None)
        self.assertEqual(audit.audit_outputs([path], [], [], checklist=self.checklist(path))['completion_status'], 'BLOCK')

    def test_clean_run_without_acceptance_checklist_is_not_full_pass(self):
        path = self.notebook()
        result = audit.audit_outputs([path], [], [])
        self.assertEqual(result['diagnostics_status'], 'PASS')
        self.assertEqual(result['completion_status'], 'BLOCK')
        self.assertFalse(result['can_claim_full_completion'])

    def test_pending_visual_check_blocks_completion(self):
        path = self.notebook()
        self.assertEqual(audit.audit_outputs([path], [], [], checklist=self.checklist(path, 'pending'))['completion_status'], 'BLOCK')

    def test_stale_evidence_hash_blocks_completion(self):
        path = self.notebook()
        checklist = self.checklist(path)
        path.write_text(path.read_text() + '\n', encoding='utf-8')
        self.assertEqual(audit.audit_outputs([path], [], [], checklist=checklist)['completion_status'], 'BLOCK')

    def test_changed_snapshot_invalidates_old_review(self):
        path = self.notebook([{'output_type': 'stream', 'name': 'stderr', 'text': 'FutureWarning: first version'}])
        previous = audit.audit_outputs([path], [], [])
        path = self.notebook([{'output_type': 'stream', 'name': 'stderr', 'text': 'FutureWarning: changed version'}])
        self.assertEqual(audit.audit_outputs([path], [], [], reviews=self.review(previous))['diagnostics_status'], 'BLOCK')

    def test_middle_of_complete_log_is_scanned(self):
        path = self.root / 'driver.log'
        path.write_text('started\n' * 100 + '[Kernel] WARNING | diagnostic\n' + 'finished\n' * 100, encoding='utf-8')
        self.assertEqual(audit.audit_outputs([], [path], [])['warning_count'], 1)

    def test_full_log_decode_failure_is_not_zero_warnings(self):
        path = self.root / 'bad.log'; path.write_bytes(b'\xffbad')
        self.assertEqual(audit.audit_outputs([], [path], [])['diagnostics_status'], 'BLOCK')

    def test_warning_in_html_mime_is_not_hidden_by_plain_model_text(self):
        path = self.notebook([{'output_type': 'display_data', 'data': {
            'text/plain': 'LogisticRegression()',
            'text/html': '<style>/* Warning: CSS example */</style><p>FutureWarning: API changed</p>'}}])
        result = audit.audit_outputs([path], [], [])
        self.assertEqual(result['warning_count'], 1)
        self.assertEqual(result['diagnostics_status'], 'BLOCK')

    def test_malformed_review_cannot_crash_or_release_gate(self):
        path = self.notebook([{'output_type': 'stream', 'name': 'stderr', 'text': 'FutureWarning: compatibility'}])
        initial = audit.audit_outputs([path], [], [])
        reviews = self.review(initial); reviews['reviews'][0]['decision'] = []
        self.assertEqual(audit.audit_outputs([path], [], [], reviews=reviews)['diagnostics_status'], 'BLOCK')

    def test_cli_resolves_each_config_evidence_from_its_own_directory(self):
        path = self.notebook([{'output_type': 'stream', 'name': 'stderr', 'text': '100% progress'}])
        initial = audit.audit_outputs([path], [], [])
        review_dir = self.root / 'reviews'; review_dir.mkdir()
        check_dir = self.root / 'checks'; check_dir.mkdir()
        review_basis = review_dir / 'basis.txt'
        review_basis.write_text('Synthetic expected progress purpose.', encoding='utf-8')
        check_basis = check_dir / 'basis.txt'
        check_basis.write_text('Synthetic final acceptance requirements.', encoding='utf-8')
        reviews = self.review(initial)
        reviews['reviews'][0]['evidence'] = [{'path': 'basis.txt', 'sha256': audit.file_hash(review_basis)}]
        checklist = self.checklist(path)
        checklist['requirements_basis'] = [{'path': 'basis.txt', 'sha256': audit.file_hash(check_basis)}]
        review_file = review_dir / 'reviews.json'
        review_file.write_text(json.dumps(reviews), encoding='utf-8')
        check_file = check_dir / 'checklist.json'
        check_file.write_text(json.dumps(checklist), encoding='utf-8')
        run = subprocess.run([sys.executable, str(ROOT / 'scripts/audit_run_outputs.py'),
            '--notebook', str(path), '--reviews', str(review_file), '--checklist', str(check_file)],
            cwd=self.root, text=True, capture_output=True, encoding='utf-8')
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        result = json.loads(run.stdout)
        self.assertEqual(result['stderr_count'], 1)
        self.assertTrue(result['can_claim_full_completion'])

    def test_zip_crc_pass_does_not_accept_stale_replay_alias(self):
        path = self.notebook(); package = self.root / 'report.zip'
        with zipfile.ZipFile(package, 'w') as archive:
            archive.writestr('final-rerun.ipynb', '{"old": true}')
        checklist = self.checklist(path)
        checklist['checks'].append({'id': 'package-replay', 'required': True, 'status': 'passed',
            'evidence': [{'path': str(package), 'member': 'final-rerun.ipynb', 'sha256': audit.file_hash(path)}]})
        with zipfile.ZipFile(package) as archive:
            self.assertIsNone(archive.testzip())
        self.assertEqual(audit.audit_outputs([path], [], [], checklist=checklist)['completion_status'], 'BLOCK')


if __name__ == '__main__':
    unittest.main()
