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
| Group | Disease | Notebook | Runtime | Open |
|---|---|---|---|---|
| [Purple](projects/purple/) | HIV | Getting started | CPU | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/purple/notebooks/01_getting_started.ipynb) |
| [Yellow](projects/yellow/) | Hypertension | Getting started | CPU | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/yellow/notebooks/01_getting_started.ipynb) |
| [Orange](projects/orange/) | Tuberculosis | Getting started | CPU | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/orange/notebooks/01_getting_started.ipynb) |
| [Blue](projects/blue/) | Cryptosporidiosis | Getting started | CPU | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/blue/notebooks/01_getting_started.ipynb) |
<!-- notebooks:end -->

## Repository layout

```
projects/<color>/
├── notebooks/        # Colab notebooks, named NN_what_it_does.ipynb
├── data/             # data used by the notebooks
└── requirements.txt  # extra pip packages installed by the setup cell
```
