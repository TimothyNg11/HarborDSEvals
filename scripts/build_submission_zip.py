"""Build the final submission.zip with the exact layout the brief requires:

    submission.zip
    +-- samples/
    +-- logs/
    +-- report/

scripts/, README.md, _data_cache/, and jobs/ are intentionally excluded —
they bloat the zip and are only useful for re-running the eval.
"""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "submission.zip"

INCLUDE_DIRS = ["samples", "logs", "report"]
INCLUDE_FILES = []

EXCLUDE_GLOBS = [
    "__pycache__",
    ".pytest_cache",
    "*.pyc",
    ".DS_Store",
    "*.egg-info",
    "_archive",
    "_archive_dabstep_unselected",
]


def should_include(p: Path) -> bool:
    for pat in EXCLUDE_GLOBS:
        if p.match(pat) or any(part == pat for part in p.parts):
            return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default=str(ZIP_PATH))
    args = ap.parse_args()
    out = Path(args.output)
    if out.exists():
        out.unlink()

    n = 0
    total_bytes = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for d in INCLUDE_DIRS:
            base = ROOT / d
            if not base.exists():
                print(f"skip missing {d}/")
                continue
            for f in sorted(base.rglob("*")):
                if not f.is_file():
                    continue
                if not should_include(f):
                    continue
                arcname = f.relative_to(ROOT).as_posix()
                z.write(f, arcname)
                n += 1
                total_bytes += f.stat().st_size

        for fname in INCLUDE_FILES:
            p = ROOT / fname
            if p.exists():
                z.write(p, fname)
                n += 1
                total_bytes += p.stat().st_size

    print(f"Built {out}  ({n} files, {total_bytes / 1e6:.1f} MB raw)")
    print(f"  compressed size: {out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
