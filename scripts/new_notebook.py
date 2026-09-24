"""Create a Colab-ready notebook with the standard workshop structure.

Usage
-----
    python scripts/new_notebook.py <project> "<Title>" [--slug short_name] [--runtime cpu|t4|l4|a100]

The title says what the notebook does. The file is named <project>_<slug>.ipynb, and the
order participants should follow is stored in the notebook metadata (workshop.order).

Example
-------
    python scripts/new_notebook.py purple "Data curation" --runtime t4
    -> projects/purple/notebooks/purple_data_curation.ipynb
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
RUNTIMES = {"cpu": "CPU", "t4": "T4 GPU", "l4": "L4 GPU (Colab Pro)", "a100": "A100 GPU (Colab Pro)"}

SETUP_INTRO = """## Setup

Run the cell below first. In Colab it downloads the workshop repository (including the data) and installs the packages this project needs. It takes about a minute. **Don't change it.**"""

SETUP_CELL = '''PROJECT = "{project}"
NEEDS_GPU = {gpu}
import os, sys, shutil, subprocess
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
for _cached in [m for m in sys.modules if m == "scripts" or m.startswith("scripts.")]:
    del sys.modules[_cached]  # forget helper modules imported before the pull above
has_gpu = shutil.which("nvidia-smi") is not None and subprocess.run(["nvidia-smi"], capture_output=True).returncode == 0
print(f"Python {{sys.version.split()[0]}} | GPU: {{'yes' if has_gpu else 'no'}} | Folder: {{os.getcwd()}}")
if NEEDS_GPU and not has_gpu:
    print("WARNING: this notebook needs a GPU. Go to Runtime > Change runtime type, choose {runtime_label}, and run this cell again.")'''


def colab_url(path):
    """Return the Open-in-Colab URL for a notebook path relative to the repo root."""
    return f"https://colab.research.google.com/github/{REPO}/blob/{BRANCH}/{path.as_posix()}"


def badge(path):
    """Return a markdown Open-in-Colab badge for a notebook path relative to the repo root."""
    return f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({colab_url(path)})"


def slugify(text):
    """Turn a title into a lowercase, underscore-separated file name fragment."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def header_line(project):
    """Return the group and disease line shown under the notebook title."""
    return f"**{project.capitalize()} group · {PROJECTS[project]}**"


def get_runtime(nb):
    """Return the runtime key (cpu, t4, l4, a100) stored in a notebook's metadata."""
    return nb.metadata.get("colab", {}).get("gpuType", "cpu").lower()


def setup_source(project, runtime):
    """Return the exact source of the setup cell for a project and runtime."""
    return SETUP_CELL.format(project=project, gpu=runtime != "cpu", runtime_label=RUNTIMES[runtime], repo=REPO)


def get_order(nb):
    """Return the position of a notebook in its group's sequence, or None."""
    return nb.metadata.get("workshop", {}).get("order")


def build_notebook(rel, project, title, runtime, order):
    """Return a new notebook with the standard structure (see CLAUDE.md)."""
    nb = nbformat.v4.new_notebook()
    nb.metadata["workshop"] = {"order": order}
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.metadata["colab"] = {"provenance": []}
    if runtime != "cpu":
        nb.metadata["accelerator"] = "GPU"
        nb.metadata["colab"]["gpuType"] = runtime.upper()
    md, code = nbformat.v4.new_markdown_cell, nbformat.v4.new_code_cell
    nb.cells = [
        md(f"{badge(rel)}\n\n# {title}\n\n{header_line(project)}\n\n_One or two sentences on what this notebook is about and why it matters for the project._"),
        md("## What you will do\n\n- _First objective_\n- _Second objective_"),
        md(SETUP_INTRO),
        code(setup_source(project, runtime)),
        md("## 1. First section\n\n_Explain what this section does before the code._"),
        code(""),
        md("## Summary\n\n- _What we did and the key result_\n\n**Next:** _the next notebook, or what to try next._"),
    ]
    return nb


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", choices=list(PROJECTS))
    parser.add_argument("title")
    parser.add_argument("--slug", default=None)
    parser.add_argument("--runtime", choices=list(RUNTIMES), default="cpu", help="Colab runtime the notebook needs")
    args = parser.parse_args()

    nb_dir = ROOT / "projects" / args.project / "notebooks"
    nb_dir.mkdir(parents=True, exist_ok=True)
    orders = [get_order(nbformat.read(p, as_version=4)) or 0 for p in nb_dir.glob("*.ipynb")]
    path = nb_dir / f"{args.project}_{args.slug or slugify(args.title)}.ipynb"
    if path.exists():
        raise SystemExit(f"{path} already exists")
    rel = path.relative_to(ROOT)
    nbformat.write(build_notebook(rel, args.project, args.title, args.runtime, max(orders, default=0) + 1), path)
    print(rel)


if __name__ == "__main__":
    main()
