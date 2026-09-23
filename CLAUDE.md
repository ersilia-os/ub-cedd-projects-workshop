# CLAUDE.md

This is the 4-day UB-CeDD workshop in Buea, Cameroon. Four projects: purple (HIV), yellow (Hypertension), orange (Tuberculosis), blue (Cryptosporidiosis). The list lives in `PROJECTS` in `scripts/new_notebook.py`. Participants run the notebooks in **Google Colab** by clicking badges in the READMEs. Anything pushed to `main` goes live for them right away.

## Conventions

- One folder per project: `projects/<color>/{notebooks,data}/`, `requirements.txt`, `README.md`.
- Always create notebooks with `python scripts/new_notebook.py <color> <day> "<Title>"`. It gives each one the name `dayN_XX_slug.ipynb`, a markdown cell with the Colab badge first, and then the **setup cell**. Don't edit or remove the setup cell. It clones the repo in Colab, `cd`s into `projects/<color>/` and pip-installs `requirements.txt`. Locally it `cd`s from `notebooks/` up to the project folder.
- Paths in notebooks are relative to the project folder, e.g. `pd.read_csv("data/sample.csv")`. Never use absolute paths or `/content/...`.
- If a notebook needs a package that Colab doesn't have (e.g. `rdkit`), add it to that project's `requirements.txt`. Don't use `!pip install` inside notebooks.
- Helper code shared by a project's notebooks goes in `projects/<color>/*.py` (it's importable because the setup cell adds the project folder to `sys.path`).
- Participants are workshop attendees. Keep notebooks linear and runnable top to bottom, with short markdown explanations between steps.

## Data

- Data files under 50 MB are committed in `projects/<color>/data/`. GitHub rejects files over 100 MB.
- Larger files get uploaded as a GitHub Release asset (`gh release upload`) and downloaded in the notebook into `data/downloads/` (git-ignored) with `urllib.request.urlretrieve`, but only when the file isn't already there.
- The repo is public, so only public, non-sensitive data goes in it.

## Before committing

Use the `ubcedd` conda env (`~/miniconda3/envs/ubcedd/bin/python`).

1. Execute each new or changed notebook locally from its `notebooks/` folder and make sure it runs without errors.
2. `python scripts/check_notebooks.py --clear` clears outputs and checks the badge, setup cell and file sizes.
3. `python scripts/update_readme.py` regenerates the badge tables in the root and project READMEs.
4. Commit and push to `main`.
