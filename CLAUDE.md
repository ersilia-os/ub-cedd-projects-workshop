# CLAUDE.md

This is the 4-day UB-CeDD workshop in Buea, Cameroon. There are four groups: purple (HIV), yellow (Hypertension), orange (Tuberculosis) and blue (Cryptosporidiosis). The list lives in `PROJECTS` in `scripts/new_notebook.py`. Participants run the notebooks in **Google Colab** by clicking badges in the READMEs. Anything pushed to `main` goes live for them right away.

## Repository conventions

- One folder per group: `projects/<color>/{notebooks,data}/`, plus `requirements.txt` and `README.md`.
- Notebooks are named by **what they do**, not by day: `NN_what_it_does.ipynb` (e.g. `02_train_a_first_model.ipynb`). `NN` is the order participants should follow.
- Always create notebooks with `python scripts/new_notebook.py <color> "<Title>" [--runtime cpu|t4|l4|a100]`. Never create them by hand. The runtime is stored in the notebook metadata, so Colab opens it on that runtime, and the README tables show it. Participants only get `t4` on free Colab; use `l4`/`a100` only if they have Colab Pro.
- Paths in notebooks are relative to the project folder, e.g. `pd.read_csv("data/compounds.csv")`. Never use absolute paths or `/content/...`.
- If a package isn't preinstalled in Colab, add it to the project's `requirements.txt`. No `!pip install` in notebooks.
- Code shared between a group's notebooks goes in `projects/<color>/*.py` (the setup cell adds the project folder to `sys.path`).

## Notebook structure (mandatory for every notebook)

Every notebook has exactly this shape. `scripts/check_notebooks.py` enforces it.

1. **Header** (markdown): Open-in-Colab badge, `# Title` (what the notebook does, sentence case), the line `**<Color> group · <Disease>**`, then 1–2 sentences on what the notebook is about and why it matters for the project.
2. **`## What you will do`** (markdown): 2–5 bullets, each starting with a verb ("Load…", "Train…", "Compare…").
3. **`## Setup`** (markdown, standard text) followed by the **setup cell** (code). Both are generated; never edit them.
4. **Numbered sections**: `## 1. …`, `## 2. …`, in order, each named for its step (e.g. `## 2. Clean the data`). Use `### 2.1 …` subsections only when a section is long. No other `#` or `##` headings.
   - Each section opens with a markdown cell explaining what it does and why, in plain language, before any code.
   - Never put two code cells in a row. Every code cell is preceded by a short markdown cell (one or two sentences) saying what it does.
   - Code cells are short (roughly ≤ 15 lines) and do one thing. The last line shows the result (a table, a plot, a printed value).
   - Callouts are markdown blockquotes: `> **Note:** …` for tips, `> **Exercise:** …` for things participants should try themselves.
5. **`## Summary`** (markdown, always the last cell): 2–4 bullets with what was done and the key result, then `**Next:** …` naming the next notebook or what to try.

Style:
- Write for participants who are new to coding: short sentences, and explain any jargon the first time it appears. No emojis.
- Set random seeds so results are reproducible.
- Plots use `stylia` (add it to `requirements.txt`).

## Before committing

Use the `ubcedd` conda env (`~/miniconda3/envs/ubcedd/bin/python`).

1. Execute each new or changed notebook locally from its `notebooks/` folder and make sure it runs without errors.
2. `python scripts/check_notebooks.py --clear` clears outputs and checks the structure, the setup cell and file sizes.
3. `python scripts/update_readme.py` regenerates the tables in the root and project READMEs.
4. Commit and push to `main`, then test in Colab (below).

## Testing in Colab (Colab-MCP)

**Local git is the source of truth. Colab is only a test bench.**

- Notebooks are only ever edited locally. Never save from Colab (*File → Save* / *Save a copy in GitHub*). If something gets fixed or explored in Colab, read the cell sources back over MCP and write them into the local `.ipynb`.
- The loop:
  1. Push, then give Miquel the notebook's Colab URL (from its badge) to open in the browser.
  2. Call `open_colab_browser_connection` and run the cells in order, reading outputs and errors.
  3. On a failure, fix the file locally and push. Then re-run the setup cell in the same tab (it runs `git pull`), and re-run from the failing cell.
  4. For a final clean check, *Runtime → Disconnect and delete runtime*, then run every cell again.
  5. Report pass or fail, with the runtime the notebook was tested on (the setup cell prints the Python version and whether a GPU is present).
- Colab-MCP can't change the runtime. The runtime comes from the notebook metadata (`--runtime`) or from Miquel via *Runtime → Change runtime type*.
- `colab-environment.txt` records Colab's Python version and `pip freeze`. Refresh it over MCP when Colab updates, and keep local package versions close to it.
- Pushes go straight to `main`, so participants can open a notebook before it has passed in Colab. Announce new notebooks only after they pass.

## Data

- Data files under 50 MB are committed in `projects/<color>/data/`. GitHub rejects files over 100 MB.
- Larger files are uploaded as a GitHub Release asset (`gh release upload`). The notebook downloads them into `data/downloads/` (git-ignored) with `urllib.request.urlretrieve`, only if the file isn't already there.
- The repository is public, so only public, non-sensitive data goes in it.
