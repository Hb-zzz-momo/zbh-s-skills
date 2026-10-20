"""Copy the bundled learning-site example into a new directory. Python 3.10+."""
from __future__ import annotations
import argparse
import html
import shutil
import unicodedata
from pathlib import Path


def create_site(output: Path, title: str) -> Path:
    if any(unicodedata.category(c) in {"Cc", "Zl", "Zp"} for c in title):
        raise ValueError("Title must not contain control characters or line separators.")
    bidi_controls = {"LRE", "RLE", "LRO", "RLO", "PDF", "LRI", "RLI", "FSI", "PDI"}
    if any(unicodedata.bidirectional(c) in bidi_controls or c in "\u061c\u200e\u200f" for c in title):
        raise ValueError("Title must not contain bidirectional control characters.")
    title = title.strip()
    visible = any(not c.isspace() and unicodedata.category(c) not in {"Cf", "Mn", "Me"} for c in title)
    if not visible or len(title) > 80:
        raise ValueError("Title must contain 1-80 characters without control characters.")
    source = Path(__file__).resolve().parents[1] / "assets" / "starter"
    expected = ("index.html", "styles.css", "app.js")
    for name in expected:
        if not (source / name).is_file():
            raise ValueError("Starter is incomplete: " + name)
    # mkdir's exclusive create also rejects existing files, directories and symlinks.
    output.mkdir(parents=True, exist_ok=False)
    try:
        for name in expected:
            if name == "index.html":
                content = (source / name).read_text(encoding="utf-8")
                (output / name).write_text(content.replace("__SITE_TITLE__", html.escape(title, quote=True)), encoding="utf-8")
            else:
                shutil.copyfile(source / name, output / name)
    except Exception:
        # Only this newly created directory belongs to this operation.
        shutil.rmtree(output)
        raise
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--title", default="My learning site")
    args = parser.parse_args()
    try:
        output = create_site(args.out, args.title)
    except (OSError, ValueError) as exc:
        # ASCII-safe errors remain readable in CP936 terminals.
        print("Cannot create site:", str(exc).encode("ascii", "backslashreplace").decode("ascii"))
        return 2
    print("Site created. Open index.html in the output directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
