"""Read-only skill distribution checks; never calls an API or grades students."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit


def audit(root):
    """Return evidence of package integrity, not a claim of grading accuracy."""
    root = Path(root).resolve()
    checks = []

    def record(name, failures, **detail):
        checks.append(dict(check=name, status='FAIL' if failures else 'PASS',
                           failures=failures, **detail))

    def local(relative):
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError('path escapes skill root')
        return path

    manifest = {}
    problems = []
    try:
        candidate = json.loads((root / 'bundle-manifest.json').read_text('utf-8'))
        if not isinstance(candidate, dict) or not isinstance(candidate.get('files'), dict) or not candidate['files']:
            raise ValueError('manifest files missing')
        manifest = candidate
        for relative, digest in manifest['files'].items():
            if not isinstance(relative, str) or not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
                raise ValueError('invalid manifest entry')
            path = local(relative)
            if not path.is_file():
                problems.append(f'missing: {relative}')
            elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                problems.append(f'hash mismatch: {relative}')
        actual = {p.relative_to(root).as_posix() for p in root.rglob('*')
                  if p.is_file() and '__pycache__' not in p.parts
                  and p.name != 'bundle-manifest.json'}
        problems.extend(f'unlisted: {p}' for p in sorted(actual - set(manifest['files'])))
    except (OSError, ValueError, TypeError) as exc:
        problems.append(f'invalid manifest: {type(exc).__name__}')
    record('manifest_integrity', problems, files=len(manifest.get('files', {})))

    required = ['SKILL.md', 'agents/openai.yaml', 'scripts/run.py', 'scripts/audit_skill.py',
                'references/requirements-and-status.md', 'references/scoring-calibration.md',
                'references/final-self-check.md', 'references/word-first-workflow.md']
    required += [f'scripts/lab_grading/rubrics/exp{n:02}.json' for n in range(1, 17)]
    required += [f'references/rubrics/exp{n:02}.md' for n in range(1, 17)]
    missing = []
    for relative in required:
        try:
            if not local(relative).is_file():
                missing.append(relative)
        except ValueError:
            missing.append(relative)
    record('required_resources', missing)

    broken = []
    link_count = 0
    for path in sorted(root.rglob('*.md')):
        # Inline file links only; code samples are not resource declarations.
        content = re.sub(r'```.*?```', '', path.read_text('utf-8'), flags=re.S)
        for match in re.finditer(r'\]\((<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\)', content):
            target = match.group(1).strip('<>')
            url = urlsplit(target)
            if url.scheme or url.netloc or not url.path:
                continue
            link_count += 1
            destination = (path.parent / unquote(url.path)).resolve()
            if not destination.is_relative_to(root) or not destination.is_file():
                broken.append(f'{path.relative_to(root).as_posix()}: {target}')
    record('local_reference_links', broken, links_checked=link_count,
           external_urls_checked=False, markdown_anchors_checked=False)

    # Do not launch a package whose tracked content failed integrity checks.
    if any(c['status'] == 'FAIL' for c in checks):
        checks.append(dict(check='standalone_rubric_validation', status='NOT_RUN',
                           reason='package checks failed'))
    else:
        try:
            completed = subprocess.run(
                [sys.executable, str(root / 'scripts/run.py'), 'validate'],
                cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=30)
            result = json.loads(completed.stdout)
            valid = completed.returncode == 0 and result.get('status') == 'PASS' and result.get('rubrics') == 16
            record('standalone_rubric_validation', [] if valid else ['validation failed'], result=result)
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            record('standalone_rubric_validation', [type(exc).__name__])
    return dict(status='FAIL' if any(c['status'] == 'FAIL' for c in checks) else 'PASS',
                root=str(root), checks=checks, api_called=False, student_grading_performed=False,
                limitation='Static integrity and rule validation only; no semantic grading or calibration proof.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    result = audit(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
