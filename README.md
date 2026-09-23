# ub-cedd-projects-workshop
Project-driven workshop at the UB-CeDD centre in Buea, Cameroon.

Four groups work on four projects over four days: **Purple** (HIV), **Yellow** (Hypertension), **Orange** (Tuberculosis) and **Blue** (Cryptosporidiosis). New notebooks are added each day.

## How to run a notebook

1. Click the **Open in Colab** badge next to the notebook you want to run. You need a Google account.
2. Run the first code cell (**Setup**). In Colab it downloads this repository, including the data, and installs what the project needs.
3. Run the rest of the cells from top to bottom.
4. To keep your changes, use **File → Save a copy in Drive**. Your copy won't change, so click the badge here again to get the latest version.

## Projects

<!-- notebooks:start -->
### Purple · HIV

Using AI to support drug discovery for HIV, the virus that causes AIDS. _Project details will be added from the project plan in the shared Drive._

[Project folder](projects/purple/) · [Shared Drive folder](https://drive.google.com/drive/folders/1ym6spmjfJze60G52v7rUjbwQ4L_bqik5) · [Project plan](https://docs.google.com/presentation/d/1Igq5d_gt5hVbe3X-u8Fw8M6JOBXO3HqjGpTdlTzHKig)

1. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/purple/notebooks/purple_getting_started.ipynb) **Getting started** · CPU

### Yellow · Hypertension

Using AI to support drug discovery for hypertension (high blood pressure), a major risk factor for heart disease and stroke. _Project details will be added from the project plan in the shared Drive._

[Project folder](projects/yellow/) · [Shared Drive folder](https://drive.google.com/drive/folders/19Xg8Fu8_78R4QFjPXPotB91XCHpTy40h) · [Project plan](https://docs.google.com/presentation/d/17CRZ0wjGJrxvKFwZ9VDbXCRiNY_D0HLW05a0xYRgerQ)

1. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/yellow/notebooks/yellow_getting_started.ipynb) **Getting started** · CPU

### Orange · Tuberculosis

Using AI to support drug discovery for tuberculosis, caused by *Mycobacterium tuberculosis*. _Project details will be added from the project plan in the shared Drive._

[Project folder](projects/orange/) · [Shared Drive folder](https://drive.google.com/drive/folders/1L452i_YdUzQCUQwIBlvSCHG5Rn95qJId) · [Project plan](https://docs.google.com/presentation/d/1Ffp0yiNLy6vAM3VXu3Kcp2QfgG_x8P9Ot9Ioqu4yRns)

1. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/orange/notebooks/orange_getting_started.ipynb) **Getting started** · CPU

### Blue · Cryptosporidiosis

Structure-based drug discovery for cryptosporidiosis, a diarrhoeal disease caused by the parasite *Cryptosporidium parvum*. The group starts from an AlphaFold 3 model of the parasite's ABC1 transporter protein.

[Project folder](projects/blue/) · [Shared Drive folder](https://drive.google.com/drive/folders/1r2LlyX3ezVJBYe7iv2XHrf9mXQemMNw6) · [Project plan](https://docs.google.com/presentation/d/1ykMahn_C9_3RZzKUbI7cQLzNg6ptHl4Us1Qoqzc9vGU)

1. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/blue/notebooks/blue_getting_started.ipynb) **Getting started** · CPU
<!-- notebooks:end -->

## Shared Google Drive

You don't need GitHub to contribute. Each group has a folder in the [shared workshop Drive](https://drive.google.com/drive/folders/1V2IHpFEsjSbLgixtLpiKpFQKMAg6VSTg) under `Projects/`, for example `Projects/PurpleTeam/`, with:

- `Data/`: put your data files here. The organisers copy them into this repository so the notebooks can use them.
- `Publications/` and `Presentations/`: papers and slides for the group.
- The project plan (e.g. *Purple: HIV*).

## Repository layout

```
projects/<color>/
├── notebooks/        # Colab notebooks, named <color>_what_it_does.ipynb
├── data/             # data used by the notebooks
└── requirements.txt  # extra pip packages installed by the setup cell
```
