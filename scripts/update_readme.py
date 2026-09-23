"""Regenerate the Open-in-Colab notebook tables in the root and project READMEs.

Rewrites the text between `<!-- notebooks:start -->` and `<!-- notebooks:end -->`.
"""

import json
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


def description(project):
    """Return the hand-written description between the markers in a project README."""
    text = (ROOT / "projects" / project / "README.md").read_text()
    match = re.search(r"<!-- description:start -->\n(.*?)\n<!-- description:end -->", text, re.DOTALL)
    return match.group(1).strip() if match else ""


def notebook_list(project):
    """Return a markdown list of a project's notebooks: Colab button, title, runtime."""
    items = [
        f"{order}. {badge(path.relative_to(ROOT))} **{title}** · {runtime}"
        for order, path, title, runtime in notebooks(project)
    ]
    return "\n".join(items) or "_No notebooks yet._"


def groups_sections():
    """Return the root README section for each group: description, links and notebooks."""
    drive = json.loads((ROOT / "drive.json").read_text())["groups"]
    sections = []
    for project, disease in PROJECTS.items():
        g = drive[project]
        links = (
            f"[Project folder](projects/{project}/) · "
            f"[Shared Drive folder](https://drive.google.com/drive/folders/{g['team']}) · "
            f"[Project plan](https://docs.google.com/presentation/d/{g['plan']})"
        )
        sections.append(f"### {project.capitalize()} · {disease}\n\n{description(project)}\n\n{links}\n\n{notebook_list(project)}")
    return "\n\n".join(sections)


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
        replace_block(ROOT / "projects" / project / "README.md", notebook_list(project))
    replace_block(ROOT / "README.md", groups_sections())
    print("READMEs updated")


if __name__ == "__main__":
    main()
