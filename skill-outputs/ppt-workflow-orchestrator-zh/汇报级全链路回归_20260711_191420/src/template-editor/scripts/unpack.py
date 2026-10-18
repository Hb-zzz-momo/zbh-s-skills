"""Safely unpack a PPTX package."""
from __future__ import annotations
import argparse
from pathlib import Path
import zipfile

REQUIRED = {"[Content_Types].xml", "_rels/.rels", "ppt/presentation.xml"}

def main() -> int:
    parser = argparse.ArgumentParser(description="Safely unpack a PPTX without overwriting an existing non-empty directory.")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    source = args.pptx.resolve()
    output = args.output_dir.resolve()
    if not source.is_file(): raise SystemExit(f"Input PPTX not found: {source}")
    if output.exists() and any(output.iterdir()): raise SystemExit(f"Output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as archive:
        names = set(archive.namelist())
        missing = REQUIRED - names
        if missing: raise SystemExit(f"Not a valid PPTX package; missing: {sorted(missing)}")
        for info in archive.infolist():
            target = (output / info.filename).resolve()
            if output != target and output not in target.parents: raise SystemExit(f"Unsafe ZIP member: {info.filename}")
            if info.is_dir(): target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as src, target.open("wb") as dst: dst.write(src.read())
    print(f"Unpacked {source} -> {output}")
    return 0

if __name__ == "__main__": raise SystemExit(main())

