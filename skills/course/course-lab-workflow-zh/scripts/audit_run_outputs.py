"""Read-only runtime diagnostic and completion-evidence gate (stdlib only).

Scans full files, never executes or edits experiment code. This checks common
diagnostics and evidence consistency, not correctness or requirement coverage.
"""
from __future__ import annotations
import argparse
import codecs
import hashlib
from html.parser import HTMLParser
import json
import re
import sys
import zipfile
from pathlib import Path

MARKER = re.compile(
    r'\b(?P<python>[A-Za-z_]\w*(?:Warning|Error|Exception))\s*:'
    r'|(?P<traceback>Traceback \(most recent call last\))'
    r'|^(?:\s*(?:\[[^\n\]]+\]|\d{4}-\d{2}-\d{2}[^\n]*?)\s*)?'
    r'(?:(?P<label>WARNING|WARN|ERROR|FATAL)(?=\s|[:：|])'
    r'|(?P<title>Warning|warning|Error|error|警告|错误|异常)\s*(?=[:：|]))',
    re.M)
ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
RANK = {'PASS': 0, 'CAUTION': 1, 'BLOCK': 2}


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_text(path):
    data = Path(path).read_bytes()
    if data.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
        return data.decode('utf-32')
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode('utf-16')
    return data.decode('utf-8-sig')


def string(value):
    return ''.join(value) if isinstance(value, list) else str(value or '')


def visible_html(value):
    class TextOnly(HTMLParser):
        def __init__(self):
            super().__init__(); self.parts = []; self.skipped = 0

        def handle_starttag(self, tag, attrs):
            if tag in {'script', 'style'}:
                self.skipped += 1

        def handle_endtag(self, tag):
            if tag in {'script', 'style'} and self.skipped:
                self.skipped -= 1

        def handle_data(self, data):
            if not self.skipped:
                self.parts.append(data)
    parser = TextOnly(); parser.feed(string(value))
    return '\n'.join(parser.parts)


def verify_refs(refs, base):
    errors = []
    if not isinstance(refs, list) or not refs:
        return ['missing hashed evidence references']
    for ref in refs:
        if not isinstance(ref, dict) or not isinstance(ref.get('path'), str) or not ref['path'].strip():
            errors.append('invalid evidence path'); continue
        expected = ref.get('sha256')
        if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', expected):
            errors.append(f'{ref["path"]}: missing valid SHA256'); continue
        path = (base / ref['path']).resolve()
        try:
            if 'member' in ref:
                with zipfile.ZipFile(path) as archive:
                    payload = archive.read(ref['member'])
                actual = hashlib.sha256(payload).hexdigest()
            else:
                actual = file_hash(path)
            if actual.lower() != expected.lower():
                errors.append(f'{ref["path"]}/{ref.get("member", "")}: stale evidence hash')
        except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, RuntimeError) as exc:
            errors.append(f'{ref["path"]}: evidence unreadable: {exc}')
    return errors


def audit_outputs(notebooks, logs, stderr_logs, *, expected_code_cells=None,
                  reviews=None, checklist=None, base=None, review_base=None, checklist_base=None):
    base = Path(base or Path.cwd()).resolve()
    review_base = Path(review_base or base).resolve()
    checklist_base = Path(checklist_base or base).resolve()
    findings = []; inputs = []; stderr_count = 0

    def add(path, digest, location, severity, category, message):
        identity = json.dumps([str(path), digest, location, severity, category, message], ensure_ascii=False)
        fid = hashlib.sha256(identity.encode('utf-8')).hexdigest()
        findings.append({'id': fid, 'path': str(path), 'source_sha256': digest,
            'location': location, 'severity': severity, 'category': category,
            'message': message, 'decision': 'unreviewed'})

    def scan(path, digest, location, message, is_stderr=False):
        nonlocal stderr_count
        if is_stderr and message.strip():
            stderr_count += 1
        cleaned = ANSI.sub('', message)
        markers = list(MARKER.finditer(cleaned))
        for marker in markers:
            category = next(value for value in marker.groupdict().values() if value)
            severity = 'warning' if category.endswith('Warning') or category in {'WARNING', 'WARN', 'Warning', 'warning', '警告'} else 'error'
            add(path, digest, f'{location}:line-{cleaned[:marker.start()].count(chr(10)) + 1}:offset-{marker.start()}', severity, category, message)
        if is_stderr and message.strip() and not markers:
            add(path, digest, location, 'stderr', 'unclassified_stderr', message)

    for supplied in notebooks:
        path = Path(supplied).resolve(); digest = 'unreadable'
        try:
            digest = file_hash(path)
            notebook = json.loads(read_text(path))
            if not isinstance(notebook, dict) or notebook.get('nbformat') != 4 or not isinstance(notebook.get('cells'), list):
                raise ValueError('expected a Notebook v4 cells array')
            codes = []
            for index, cell in enumerate(notebook['cells']):
                if not isinstance(cell, dict):
                    raise ValueError('malformed notebook cell')
                if cell.get('cell_type') != 'code':
                    continue
                codes.append(cell)
                count = cell.get('execution_count')
                if string(cell.get('source')).strip() and (type(count) is not int or count != len([c for c in codes if string(c.get('source')).strip()])):
                    add(path, digest, f'cell-{index}', 'integrity', 'incomplete_execution', f'Nonempty code cell execution count is {count!r}; clean sequential execution is not established.')
                outputs = cell.get('outputs', [])
                if not isinstance(outputs, list):
                    raise ValueError('outputs must be an array')
                for oi, output in enumerate(outputs):
                    if not isinstance(output, dict):
                        raise ValueError('malformed notebook output')
                    location = f'cell-{index}:In[{count}]:output-{oi}'
                    kind = output.get('output_type')
                    if kind == 'error':
                        message = string(output.get('traceback')) or f'{output.get("ename", "Error")}: {output.get("evalue", "")}'
                        add(path, digest, location, 'error', str(output.get('ename', 'Error')), message)
                    elif kind == 'stream':
                        scan(path, digest, location, string(output.get('text')), output.get('name') == 'stderr')
                    elif kind in {'execute_result', 'display_data'}:
                        data = output.get('data', {})
                        if not isinstance(data, dict):
                            raise ValueError('MIME data must be an object')
                        if 'text/plain' in data:
                            scan(path, digest, location, string(data['text/plain']))
                        if 'text/html' in data:
                            scan(path, digest, location + ':MIME-text/html', visible_html(data['text/html']))
                    else:
                        raise ValueError(f'unsupported notebook output type: {kind!r}')
            if expected_code_cells is not None and len(codes) != expected_code_cells:
                add(path, digest, 'notebook', 'integrity', 'code_cell_count_mismatch', f'Expected {expected_code_cells} code cells, found {len(codes)}.')
            inputs.append({'path': str(path), 'sha256': digest, 'kind': 'notebook', 'code_cells': len(codes),
                           'executed_code_cells': sum(type(c.get('execution_count')) is int for c in codes)})
        except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
            add(path, digest, 'file', 'integrity', 'unreadable_notebook', str(exc))

    for supplied, is_stderr in [(p, False) for p in logs] + [(p, True) for p in stderr_logs]:
        path = Path(supplied).resolve(); digest = 'unreadable'
        try:
            digest = file_hash(path)
            scan(path, digest, 'complete-log', read_text(path), is_stderr)
            inputs.append({'path': str(path), 'sha256': digest, 'kind': 'stderr-log' if is_stderr else 'log'})
        except (OSError, UnicodeError, ValueError) as exc:
            add(path, digest, 'file', 'integrity', 'unreadable_log', str(exc))
    if not notebooks and not logs and not stderr_logs:
        add(base, '', 'inputs', 'integrity', 'missing_runtime_inputs', 'No runtime output files supplied.')

    review_errors = []; by_id = {finding['id']: finding for finding in findings}
    if reviews is not None:
        entries = reviews.get('reviews') if isinstance(reviews, dict) else None
        if not isinstance(entries, list):
            review_errors.append('reviews must be an array')
            entries = []
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get('finding_id'), str):
                review_errors.append('invalid review finding_id'); continue
            fid = entry['finding_id']; finding = by_id.get(fid)
            if fid in seen or finding is None:
                review_errors.append(f'{fid}: duplicate or stale review'); continue
            seen.add(fid)
            decision = entry.get('decision')
            if not isinstance(decision, str) or decision not in {'expected', 'nonblocking'} or finding['severity'] == 'integrity':
                review_errors.append(f'{fid}: unsupported review decision'); continue
            if decision == 'nonblocking' and finding['severity'] == 'error':
                review_errors.append(f'{fid}: exception cannot be accepted as a nonblocking warning'); continue
            if not all(isinstance(entry.get(key), str) and entry[key].strip() for key in ['reason', 'impact', 'basis']):
                review_errors.append(f'{fid}: review needs reason, impact and basis'); continue
            invalid = verify_refs(entry.get('evidence'), review_base)
            if invalid:
                review_errors.extend(f'{fid}: {error}' for error in invalid); continue
            finding.update({'decision': decision, 'review': entry})
    diagnostics_status = 'BLOCK' if review_errors or any(f['decision'] == 'unreviewed' for f in findings) else (
        'CAUTION' if any(f['decision'] == 'nonblocking' for f in findings) else 'PASS')

    acceptance_errors = []
    if not isinstance(checklist, dict):
        acceptance_errors.append('Completion checklist not supplied; diagnostics-only success is not full acceptance.')
    else:
        acceptance_errors.extend(verify_refs(checklist.get('requirements_basis'), checklist_base))
        checks = checklist.get('checks')
        if not isinstance(checks, list) or not checks:
            acceptance_errors.append('checks must be a nonempty array'); checks = []
        ids = set(); required_count = 0
        for check in checks:
            if not isinstance(check, dict) or not isinstance(check.get('id'), str) or not check['id'].strip():
                acceptance_errors.append('invalid acceptance check'); continue
            cid = check['id']
            if cid in ids:
                acceptance_errors.append(f'{cid}: duplicate acceptance check')
            ids.add(cid)
            if type(check.get('required')) is not bool:
                acceptance_errors.append(f'{cid}: required must be boolean'); continue
            if not check['required']:
                continue
            required_count += 1
            if check.get('status') != 'passed':
                acceptance_errors.append(f'{cid}: required check is not passed')
            acceptance_errors.extend(f'{cid}: {error}' for error in verify_refs(check.get('evidence'), checklist_base))
        if not required_count:
            acceptance_errors.append('No required acceptance checks declared.')
    completion_status = 'BLOCK' if acceptance_errors else diagnostics_status
    return {'diagnostics_status': diagnostics_status, 'completion_status': completion_status,
        'can_claim_full_completion': completion_status == 'PASS',
        'warning_count': sum(f['severity'] == 'warning' for f in findings),
        'error_count': sum(f['severity'] == 'error' for f in findings),
        'integrity_issue_count': sum(f['severity'] == 'integrity' for f in findings),
        'stderr_count': stderr_count, 'inputs': inputs, 'findings': findings,
        'review_errors': review_errors, 'acceptance_errors': acceptance_errors,
        'limits': 'Checks common runtime diagnostics and declared evidence hashes only; does not establish correctness, complete requirement coverage, GUI review or official grading.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--notebook', type=Path, action='append', default=[])
    parser.add_argument('--log', type=Path, action='append', default=[])
    parser.add_argument('--stderr-log', type=Path, action='append', default=[])
    parser.add_argument('--expected-code-cells', type=int)
    parser.add_argument('--reviews', type=Path)
    parser.add_argument('--checklist', type=Path)
    parser.add_argument('--diagnostics-only', action='store_true')
    args = parser.parse_args()
    try:
        reviews = json.loads(read_text(args.reviews)) if args.reviews else None
        checklist = json.loads(read_text(args.checklist)) if args.checklist else None
        result = audit_outputs(args.notebook, args.log, args.stderr_log,
            expected_code_cells=args.expected_code_cells, reviews=reviews, checklist=checklist,
            review_base=args.reviews.resolve().parent if args.reviews else None,
            checklist_base=args.checklist.resolve().parent if args.checklist else None)
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        result = {'diagnostics_status': 'BLOCK', 'completion_status': 'BLOCK',
                  'can_claim_full_completion': False, 'input_error': str(exc)}
    if args.diagnostics_only:
        result['can_claim_full_completion'] = False
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return RANK[result['diagnostics_status'] if args.diagnostics_only else result['completion_status']]


if __name__ == '__main__':
    sys.exit(main())
