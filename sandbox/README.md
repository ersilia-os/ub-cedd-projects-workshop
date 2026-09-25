# Sandbox

Scratch notebooks for trying out tools before they are considered for a project.

Nothing here is workshop material. These notebooks are not linked from any project README,
they are not covered by the structure rules in `CLAUDE.md`, and unlike participant
notebooks they may clone repositories and run `pip install`. Anything that proves useful
gets rewritten as a proper notebook under `projects/<color>/notebooks/`.

Click a badge to open a notebook in Colab. Clicking the `.ipynb` file in GitHub only opens
GitHub's own viewer, which cannot run anything.

- [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/sandbox/run_ersilia_model_colab.ipynb) &nbsp;**Run an Ersilia model in Colab** · a tool, not an experiment. Three form cells: set up, pick a model and version, upload a CSV of SMILES and get predictions back. Built on the recipe the SIF feasibility test established.
- [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/sandbox/diffphore_smoke_test.ipynb) &nbsp;**DiffPhore smoke test** · does DiffPhore run in Colab?
- [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/sandbox/sif_feasibility_test.ipynb) &nbsp;**Ersilia SIF feasibility test** · can an Ersilia `.sif` run in Colab? Yes — serve it under `unshare -r` and POST to it; the image's own entrypoint is broken. ~4 min of setup per runtime, so not workshop material as it stands.
- [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/sandbox/pharmacoforge_smoke_test.ipynb) &nbsp;**PharmacoForge smoke test** · does PharmacoForge run in Colab?
- [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/sandbox/gnina_docking_screen.ipynb) &nbsp;**gnina docking screen** · redock a complex's own ligand, then screen a library in the same pocket. Uses gnina on a Colab GPU and smina on a laptop; the local run takes under two minutes.

`silymarin_analogues.csv` belongs to the gnina notebook: sixteen public silymarin-related
compounds with their PubChem CIDs, downloaded by the notebook over its raw GitHub URL.
