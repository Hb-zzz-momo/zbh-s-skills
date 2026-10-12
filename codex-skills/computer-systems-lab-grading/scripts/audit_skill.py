"""CLI adapter for the shared read-only skill auditor."""
from pathlib import Path
import sys

project_source = Path(__file__).resolve().parents[1] / 'src'
if project_source.is_dir():
    sys.path.insert(0, str(project_source))
from lab_grading.skill_audit import main

if __name__ == '__main__':
    raise SystemExit(main())
