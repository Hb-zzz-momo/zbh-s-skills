"""Pack an unpacked OOXML presentation into a new PPTX."""
from __future__ import annotations
import argparse
from pathlib import Path
import zipfile

REQUIRED = ["[Content_Types].xml", "_rels/.rels", "ppt/presentation.xml"]

def main() -> int:
    parser = argparse.ArgumentParser(description="Pack an unpacked PPTX directory after validating required OOXML parts.")
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_pptx", type=Path)
    parser.add_argument("--force", action="store_true", help="Allow replacing the output file; never use for the original template.")
    args = parser.parse_args()
    root = args.input_dir.resolve(); output = args.output_pptx.resolve()
    if not root.is_dir(): raise SystemExit(f"Input directory not found: {root}")
    missing = [name for name in REQUIRED if not (root / name).is_file()]
    if missing: raise SystemExit(f"Missing required OOXML parts: {missing}")
    if output.exists() and not args.force: raise SystemExit(f"Output exists; choose a new filename or pass --force: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(p for p in root.rglob("*") if p.is_file()): archive.write(file, file.relative_to(root).as_posix())
    with zipfile.ZipFile(output) as archive:
        bad = archive.testzip()
        if bad: raise SystemExit(f"ZIP CRC verification failed at: {bad}")
    print(f"Packed {root} -> {output}")
    return 0

if __name__ == "__main__": raise SystemExit(main())

