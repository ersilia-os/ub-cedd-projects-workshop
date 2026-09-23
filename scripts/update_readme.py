"""Regenerate the Open-in-Colab notebook tables in the root and project READMEs.

Rewrites the text between `<!-- notebooks:start -->` and `<!-- notebooks:end -->`.
"""

import re

import nbformat

from new_notebook import PROJECTS, ROOT, RUNTIMES, badge, get_order, get_runtime

START, END = "<!-- notebooks:start -->", "<!-- notebooks:end -->"


def notebooks(project):
    """Return (order, path, title, runtime label) for each notebook of a project, sorted by order."""
    rows = []
    for path in (ROOT / "projects" / project / "notebooks").glob("*.ipynb"):
        nb = nbformat.read(path, as_version=4)
        match = re.search(r"^# (.+)$", nb.cells[0].source if nb.cells else "", re.MULTILINE)
        title = match.group(1).strip() if match else path.stem
        rows.append((get_order(nb) or 0, path, title, RUNTIMES.get(get_runtime(nb), "?")))
    return sorted(rows)


def table(project):
    """Return a project README table listing its notebooks with runtime and Colab badge."""
    rows = ["| # | Notebook | Runtime | Open |", "|---|---|---|---|"]
    for order, path, title, runtime in notebooks(project):
        rows.append(f"| {order} | {title} | {runtime} | {badge(path.relative_to(ROOT))} |")
    return "\n".join(rows) if len(rows) > 2 else "_No notebooks yet._"


def groups_table():
    """Return the root README table: one row per notebook across all groups."""
    rows = ["| Group | Disease | Notebook | Runtime | Open |", "|---|---|---|---|---|"]
    for project, disease in PROJECTS.items():
        folder = f"[{project.capitalize()}](projects/{project}/)"
        entries = notebooks(project) or [(0, None, "_No notebooks yet._", "")]
        for _, path, title, runtime in entries:
            open_cell = badge(path.relative_to(ROOT)) if path else ""
            rows.append(f"| {folder} | {disease} | {title} | {runtime} | {open_cell} |")
    return "\n".join(rows)


def replace_block(readme, content):
    """Replace the marked block in a README file with new content."""
    text = readme.read_text()
    if START not in text or END not in text:
        raise SystemExit(f"Markers missing in {readme}")
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    readme.write_text(f"{before}{START}\n{content}\n{END}{after}")


def main():
    for project in PROJECTS:
        replace_block(ROOT / "projects" / project / "README.md", table(project))
    replace_block(ROOT / "README.md", groups_table())
    print("READMEs updated")


if __name__ == "__main__":
    main()
