"""Unit tests use synthetic fixtures, not user experiment results."""
from __future__ import annotations
import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lab_validator', ROOT / 'scripts' / 'validate.py')
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


def fixture():
    return {
        'schema_version': '1.0', 'lab_id': 'test-course-lab1', 'attempt_id': 'unit-test-only',
        'report_status': 'draft',
        'requirements': [{'id': 'R01', 'title': 'Synthetic requirement', 'required': True,
                          'execution_status': 'passed', 'evidence_status': 'verified',
                          'validation': 'Expected test marker is present', 'actual_result': 'Synthetic test marker found',
                          'evidence_ids': ['E01'], 'na_reason': ''}],
        'evidence': [{'id': 'E01', 'kind': 'log', 'verification': 'verified',
                      'lab_id': 'test-course-lab1', 'attempt_id': 'unit-test-only',
                      'path': 'evidence/run.txt', 'description': 'Synthetic test fixture only'}]
    }


class RegisterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        (self.base/'evidence').mkdir()
        (self.base/'evidence/run.txt').write_text('synthetic unit test fixture\n', encoding='utf-8')
        self.data = fixture()

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, **kwargs):
        return validator.validate_record(self.data, self.base, **kwargs)

    def test_valid_verified_record(self):
        self.assertEqual(self.check(check_files=True, require_ready=True)['errors'], [])

    def test_draft_missing_evidence_is_not_fake_success(self):
        r = self.data['requirements'][0]
        r.update(execution_status='not_started', evidence_status='missing', actual_result='', evidence_ids=[])
        self.data['evidence'] = []
        result = self.check()
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['summary']['pending_ids'], ['R01'])

    def test_draft_not_ready(self):
        r = self.data['requirements'][0]
        r.update(execution_status='not_started', evidence_status='missing', actual_result='', evidence_ids=[])
        self.data['evidence'] = []
        self.assertTrue(self.check(require_ready=True)['errors'])

    def test_example_cannot_prove_pass(self):
        self.data['requirements'][0]['evidence_status'] = 'example'
        self.data['evidence'][0].update(kind='example', verification='example')
        self.assertTrue(self.check()['errors'])

    def test_wrong_course_rejected(self):
        self.data['evidence'][0]['lab_id'] = 'another-course-lab1'
        self.assertTrue(self.check()['errors'])

    def test_stale_attempt_rejected(self):
        self.data['evidence'][0]['attempt_id'] = 'old-run'
        self.assertTrue(self.check()['errors'])

    def test_path_traversal_rejected(self):
        self.data['evidence'][0]['path'] = '../outside.txt'
        self.assertTrue(self.check()['errors'])

    def test_absolute_windows_path_rejected(self):
        self.data['evidence'][0]['path'] = 'C:/Users/someone/result.txt'
        self.assertTrue(self.check()['errors'])

    def test_missing_local_file_rejected(self):
        self.data['evidence'][0]['path'] = 'evidence/not-found.txt'
        self.assertTrue(self.check(check_files=True)['errors'])

    def test_duplicate_evidence_rejected(self):
        self.data['evidence'].append(copy.deepcopy(self.data['evidence'][0]))
        self.assertTrue(self.check()['errors'])

    def test_duplicate_requirement_rejected(self):
        self.data['requirements'].append(copy.deepcopy(self.data['requirements'][0]))
        self.assertTrue(self.check()['errors'])

    def test_unknown_reference_rejected(self):
        self.data['requirements'][0]['evidence_ids'] = ['E99']
        self.assertTrue(self.check()['errors'])

    def test_source_code_is_not_runtime_evidence(self):
        self.data['evidence'][0]['kind'] = 'source'
        self.assertTrue(self.check()['errors'])

    def test_user_reported_allowed_but_not_ready(self):
        self.data['requirements'][0]['evidence_status'] = 'user_reported'
        self.data['evidence'][0].update(kind='user_statement', verification='user_reported',
                                      path='', locator='synthetic-message-1')
        self.assertEqual(self.check()['errors'], [])
        self.assertTrue(self.check(require_ready=True)['errors'])

    def test_pass_without_actual_result_rejected(self):
        self.data['requirements'][0]['actual_result'] = ''
        self.assertTrue(self.check()['errors'])

    def test_not_applicable_needs_reason(self):
        self.data['requirements'][0].update(execution_status='not_applicable', evidence_status='missing',
                                          evidence_ids=[], na_reason='')
        self.assertTrue(self.check()['errors'])

    def test_empty_requirements_rejected(self):
        self.data['requirements'] = []
        self.assertTrue(self.check()['errors'])

    def test_bad_input_type_rejected(self):
        self.assertTrue(validator.validate_record([], self.base)['errors'])

    def test_ready_state_enforces_checks_without_flag(self):
        self.data['report_status'] = 'ready_for_review'
        self.data['requirements'][0]['execution_status'] = 'failed'
        self.assertTrue(self.check()['errors'])

    def test_malformed_requirement_enums_fail_cleanly(self):
        self.data['requirements'][0].update(execution_status=[], evidence_status={})
        self.assertTrue(self.check()['errors'])

    def test_malformed_evidence_enums_fail_cleanly(self):
        self.data['evidence'][0].update(kind=[], verification={})
        self.assertTrue(self.check()['errors'])

    def test_malformed_report_status_fails_cleanly(self):
        self.data['report_status'] = []
        self.assertTrue(self.check()['errors'])

    def test_package_links_and_metadata(self):
        self.assertEqual(validator.validate_package(ROOT)['errors'], [])


if __name__ == '__main__':
    unittest.main()
