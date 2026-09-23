# ub-cedd-projects-workshop
Project-driven workshop at the UB-CeDD centre in Buea, Cameroon.

Four groups work on four projects over four days: **Purple** (HIV), **Yellow** (Hypertension), **Orange** (Tuberculosis) and **Blue** (Cryptosporidiosis). New notebooks are added each day.

## How to run a notebook

1. Click the **Open in Colab** badge next to the notebook you want to run. You need a Google account.
2. Run the first code cell (**Setup**). In Colab it downloads this repository, including the data, and installs what the project needs.
3. Run the rest of the cells from top to bottom.
4. To keep your changes, use **File → Save a copy in Drive**. Your copy won't change, so click the badge here again to get the latest version.

## Notebooks

<!-- notebooks:start -->
| Group | Disease | Notebooks |
|---|---|---|
| [Purple](projects/purple/) | HIV | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/purple/notebooks/day1_00_hiv.ipynb) Day 1 |
| [Yellow](projects/yellow/) | Hypertension | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/yellow/notebooks/day1_00_hypertension.ipynb) Day 1 |
| [Orange](projects/orange/) | Tuberculosis | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/orange/notebooks/day1_00_tuberculosis.ipynb) Day 1 |
| [Blue](projects/blue/) | Cryptosporidiosis | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/blue/notebooks/day1_00_cryptosporidiosis.ipynb) Day 1 |
<!-- notebooks:end -->

## Repository layout

```
projects/<color>/
├── notebooks/        # Colab notebooks, named dayN_XX_title.ipynb
├── data/             # data used by the notebooks
└── requirements.txt  # extra pip packages installed by the setup cell
```
