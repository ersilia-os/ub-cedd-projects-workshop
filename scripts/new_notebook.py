"""Create a Colab-ready notebook skeleton for a workshop project.

Usage
-----
    python scripts/new_notebook.py <project> <day> "<Title>" [--slug short_name]

Example
-------
    python scripts/new_notebook.py purple 2 "Train a first model"
    -> projects/purple/notebooks/day2_01_train_a_first_model.ipynb
"""

import argparse
import re
from pathlib import Path

import nbformat

REPO = "ersilia-os/ub-cedd-projects-workshop"
BRANCH = "main"
ROOT = Path(__file__).resolve().parents[1]
PROJECTS = {
    "purple": "HIV",
    "yellow": "Hypertension",
    "orange": "Tuberculosis",
    "blue": "Cryptosporidiosis",
}

SETUP_CELL = '''# Setup: run this cell first. In Colab it downloads the workshop repository and installs requirements.
PROJECT = "{project}"
import os, sys, subprocess
if "google.colab" in sys.modules:
    repo_dir = "/content/ub-cedd-projects-workshop"
    if not os.path.exists(repo_dir):
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/{repo}.git", repo_dir], check=True)
    else:
        subprocess.run(["git", "-C", repo_dir, "pull", "--ff-only"], check=True)
    os.chdir(f"{{repo_dir}}/projects/{{PROJECT}}")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"], check=True)
elif os.path.basename(os.getcwd()) == "notebooks":
    os.chdir("..")
sys.path.insert(0, os.getcwd())
print("Working directory:", os.getcwd())'''


def colab_url(path):
    """Return the Open-in-Colab URL for a notebook path relative to the repo root."""
    return f"https://colab.research.google.com/github/{REPO}/blob/{BRANCH}/{path.as_posix()}"


def badge(path):
    """Return a markdown Open-in-Colab badge for a notebook path relative to the repo root."""
    return f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({colab_url(path)})"


def slugify(text):
    """Turn a title into a lowercase, underscore-separated file name fragment."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", choices=list(PROJECTS))
    parser.add_argument("day", type=int, choices=[1, 2, 3, 4])
    parser.add_argument("title")
    parser.add_argument("--slug", default=None)
    args = parser.parse_args()

    nb_dir = ROOT / "projects" / args.project / "notebooks"
    nb_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(nb_dir.glob(f"day{args.day}_*.ipynb"))
    index = len(existing)
    name = f"day{args.day}_{index:02d}_{args.slug or slugify(args.title)}.ipynb"
    path = nb_dir / name
    if path.exists():
        raise SystemExit(f"{path} already exists")

    rel = path.relative_to(ROOT)
    nb = nbformat.v4.new_notebook()
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.metadata["colab"] = {"provenance": []}
    nb.cells = [
        nbformat.v4.new_markdown_cell(f"{badge(rel)}\n\n# {args.title}\n\n**{args.project.capitalize()} group ({PROJECTS[args.project]}) · Day {args.day}**\n\n_Describe what this notebook does._"),
        nbformat.v4.new_code_cell(SETUP_CELL.format(project=args.project, repo=REPO)),
    ]
    nbformat.write(nb, path)
    print(rel)


if __name__ == "__main__":
    main()
