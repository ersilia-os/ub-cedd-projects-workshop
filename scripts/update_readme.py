"""Regenerate the Open-in-Colab notebook tables in the root and project READMEs.

Rewrites the text between `<!-- notebooks:start -->` and `<!-- notebooks:end -->`.
"""

import json
import re
from pathlib import Path

from new_notebook import PROJECTS, ROOT, badge

START, END = "<!-- notebooks:start -->", "<!-- notebooks:end -->"


def notebook_title(path):
    """Return the first markdown heading of a notebook, or its file name."""
    nb = json.loads(path.read_text())
    for cell in nb["cells"]:
        if cell["cell_type"] == "markdown":
            match = re.search(r"^#\s+(.+)$", "".join(cell["source"]), re.MULTILINE)
            if match:
                return match.group(1).strip()
    return path.stem


def table(project):
    """Return a markdown table listing a project's notebooks with Colab badges."""
    notebooks = sorted((ROOT / "projects" / project / "notebooks").glob("*.ipynb"))
    if not notebooks:
        return "_No notebooks yet._"
    rows = ["| Day | Notebook | Open |", "|---|---|---|"]
    for path in notebooks:
        day = path.name.split("_")[0].replace("day", "")
        rows.append(f"| {day} | {notebook_title(path)} | {badge(path.relative_to(ROOT))} |")
    return "\n".join(rows)


def groups_table():
    """Return the root README table: one row per group with a Colab button per notebook."""
    rows = ["| Group | Disease | Notebooks |", "|---|---|---|"]
    for project, disease in PROJECTS.items():
        notebooks = sorted((ROOT / "projects" / project / "notebooks").glob("*.ipynb"))
        links = "<br>".join(f"{badge(p.relative_to(ROOT))} Day {p.name.split('_')[0][3:]}" for p in notebooks)
        folder = f"[{project.capitalize()}](projects/{project}/)"
        rows.append(f"| {folder} | {disease} | {links or '_No notebooks yet._'} |")
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
