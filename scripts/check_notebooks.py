"""Check notebooks and data before committing.

Checks that every notebook follows the standard structure described in CLAUDE.md,
that the setup cell matches the template, that outputs are cleared, and that no file
in the repository exceeds 50 MB. Pass `--clear` to clear outputs in place.
"""

import re
import sys

import nbformat

from new_notebook import ROOT, RUNTIMES, SETUP_INTRO, get_order, get_runtime, header_line, setup_source

MAX_MB = 50


def check_structure(nb, rel, project):
    """Return a list of problems with the standard notebook structure."""
    problems = []
    cells = nb.cells
    if len(cells) < 6:
        return ["too few cells for the standard structure"]
    head = cells[0].source
    if cells[0].cell_type != "markdown" or "colab-badge.svg" not in head:
        problems.append("cell 1 must be markdown starting with the Open-in-Colab badge")
    elif rel.as_posix() not in head:
        problems.append("Colab badge points to a different path (was the file renamed?)")
    if not re.search(r"^# \S", head, re.MULTILINE):
        problems.append("cell 1 must contain the '# Title'")
    if header_line(project) not in head:
        problems.append(f"cell 1 must contain the line {header_line(project)}")
    if not re.match(rf"{project}_[a-z0-9_]+\.ipynb$", rel.name):
        problems.append(f"file name must be {project}_what_it_does.ipynb")
    if not isinstance(get_order(nb), int):
        problems.append("metadata.workshop.order is missing (create notebooks with new_notebook.py)")
    if cells[1].cell_type != "markdown" or not cells[1].source.startswith("## What you will do"):
        problems.append("cell 2 must be the '## What you will do' markdown cell")
    if cells[2].cell_type != "markdown" or cells[2].source != SETUP_INTRO:
        problems.append("cell 3 must be the standard '## Setup' markdown cell")
    runtime = get_runtime(nb)
    if runtime not in RUNTIMES:
        return problems + [f"unknown runtime {runtime!r} in metadata"]
    if cells[3].cell_type != "code" or cells[3].source != setup_source(project, runtime):
        problems.append("cell 4 must be the unmodified setup cell (regenerate it from new_notebook.py)")
    body = cells[4:-1]
    if not body or body[0].cell_type != "markdown" or not body[0].source.startswith("## 1. "):
        problems.append("content must start with a '## 1. ...' section after the setup cell")
    sections = [c.source.splitlines()[0] for c in body if c.cell_type == "markdown" and c.source.startswith("## ")]
    numbers = [int(m.group(1)) for s in sections if (m := re.match(r"## (\d+)\. \S", s))]
    if len(numbers) != len(sections) or numbers != list(range(1, len(numbers) + 1)):
        problems.append("main sections must be numbered in order: '## 1. ...', '## 2. ...'")
    for c in body:
        if c.cell_type == "markdown" and re.search(r"^# ", c.source, re.MULTILINE):
            problems.append("only cell 1 may use a '# ' heading")
            break
    for a, b in zip(body, body[1:]):
        if a.cell_type == "code" and b.cell_type == "code" and a.source.strip() and b.source.strip():
            problems.append("two code cells in a row: add a markdown cell explaining the second one")
            break
    if cells[-1].cell_type != "markdown" or not cells[-1].source.startswith("## Summary"):
        problems.append("the last cell must be the '## Summary' markdown cell")
    return problems


def check_notebook(path, clear):
    """Return a list of problems found in one notebook."""
    nb = nbformat.read(path, as_version=4)
    rel = path.relative_to(ROOT)
    problems = check_structure(nb, rel, path.parts[-3])
    dirty = [c for c in nb.cells if c.cell_type == "code" and (c.outputs or c.execution_count)]
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
    for group in sorted(ROOT.glob("projects/*/notebooks")):
        orders = [get_order(nbformat.read(p, as_version=4)) for p in group.glob("*.ipynb")]
        if len(orders) != len(set(orders)):
            print(f"{group.relative_to(ROOT)}: two notebooks share the same metadata.workshop.order")
            failed = True
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
