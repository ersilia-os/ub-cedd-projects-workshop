# 🔵 Blue group · Cryptosporidiosis

<!-- description:start -->
***In silico* generation and validation of silymarin analogues against CpABC1**, an ABC transporter of *Cryptosporidium parvum* sitting at the host–parasite interface. Silymarin inhibits parasite growth, but only at high concentrations, so the group compares AlphaFold and I-TASSER models of the target, derives a pharmacophore from the CpABC1–silymarin complex, and uses it to screen and rank better candidates.
<!-- description:end -->

- **Shared Drive folder:** [BlueTeam](https://drive.google.com/drive/folders/1r2LlyX3ezVJBYe7iv2XHrf9mXQemMNw6). Data, publications and presentations for this group go here.
- **Project plan:** [Blue: Cryptosporidiosis](https://docs.google.com/document/d/1fkpgSYlQGA0GsVnExQSWIfpCbuVIzpoS_DjwCDoBC28)

## Notebooks

Click a button to open the notebook in Google Colab, then run the first code cell (Setup) before anything else.

<!-- notebooks:start -->
1. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/blue/notebooks/blue_getting_started.ipynb) &nbsp;**Getting started** · _CPU_
2. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/blue/notebooks/blue_pharmacophore.ipynb) &nbsp;**Deriving a pharmacophore for the CpABC1 pocket** · _CPU_
3. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/blue/notebooks/blue_pharmit_hits.ipynb) &nbsp;**From Pharmit hits to a list of compounds to order** · _CPU_
4. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/blue/notebooks/blue_chemical_space.ipynb) &nbsp;**Exploring the chemical space of the CpABC1 pharmacophore hits** · _CPU_
5. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/blue/notebooks/blue_sand_shape_similarity.ipynb) &nbsp;**Shape similarity to silymarin** · _CPU_
6. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/blue/notebooks/blue_sprint_filter.ipynb) &nbsp;**Filter the shape hits with SPRINT** · _CPU_
7. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/blue/notebooks/blue_cytotoxicity_filter.ipynb) &nbsp;**Filter the shape hits by predicted toxicity** · _CPU_
<!-- notebooks:end -->

## Data

Data files for this group live in [`data/`](data/), copied from the Drive `Data` folder. Where each file came from is recorded in [`data/SOURCES.md`](data/SOURCES.md).

> **Note:** the SAND shape descriptors (`eos5mnx_*.csv`), for the 28,732 Pharmit hits and for silymarin, were calculated beforehand with the [Ersilia CLI](https://github.com/ersilia-os/ersilia), running the model [eos5mnx](https://github.com/ersilia-os/eos5mnx) locally. The notebooks don't run the model; they read its output files. To calculate them again: `ersilia fetch eos5mnx`, `ersilia serve eos5mnx`, then `ersilia run -i <molecules>.csv -o eos5mnx_<molecules>.csv`.
