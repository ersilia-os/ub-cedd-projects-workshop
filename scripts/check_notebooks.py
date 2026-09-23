"""Check notebooks and data before committing.

Checks that every notebook has a Colab badge and the setup cell with the right project,
that outputs are cleared, and that no file in the repository exceeds 50 MB.
Pass `--clear` to clear outputs in place instead of reporting them.
"""

import sys
from pathlib import Path

import nbformat

from new_notebook import ROOT

MAX_MB = 50


def check_notebook(path, clear):
    """Return a list of problems found in one notebook."""
    problems = []
    nb = nbformat.read(path, as_version=4)
    project = path.parts[-3]
    code = [c for c in nb.cells if c.cell_type == "code"]
    if not nb.cells or "colab-badge.svg" not in nb.cells[0].source:
        problems.append("first cell has no Open-in-Colab badge")
    elif path.relative_to(ROOT).as_posix() not in nb.cells[0].source:
        problems.append("Colab badge points to a different path (was the file renamed?)")
    if not code or f'PROJECT = "{project}"' not in code[0].source:
        problems.append(f'first code cell is not the setup cell for PROJECT = "{project}"')
    dirty = [c for c in code if c.outputs or c.execution_count]
    if dirty:
        if clear:
            for c in dirty:
                c.outputs, c.execution_count = [], None
            nbformat.write(nb, path)
        else:
            problems.append(f"{len(dirty)} cell(s) have outputs (run with --clear)")
    return problems


def main():
    clear = "--clear" in sys.argv
    failed = False
    for path in sorted(ROOT.glob("projects/*/notebooks/*.ipynb")):
        for problem in check_notebook(path, clear):
            print(f"{path.relative_to(ROOT)}: {problem}")
            failed = True
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        size_mb = path.stat().st_size / 1e6
        if size_mb > MAX_MB:
            print(f"{path.relative_to(ROOT)}: {size_mb:.0f} MB is too large for git; host it as a release asset")
            failed = True
    if failed:
        sys.exit(1)
    print("All checks passed")


if __name__ == "__main__":
    main()
