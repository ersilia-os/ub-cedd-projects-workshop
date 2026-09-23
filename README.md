# UB-CeDD Projects Workshop

**AI for drug discovery** · UB-CeDD, University of Buea, Cameroon · September 2026

Hands-on material for participants of a four-day, project-driven workshop. Four groups each tackle one disease, building up a set of Google Colab notebooks over the week. Everything runs in the browser: you only need a Google account.

## Getting started

1. Find your group below and click **Open in Colab** next to a notebook.
2. Run the first code cell, **Setup**. It downloads this repository (including the data) and installs what the project needs.
3. Run the remaining cells from top to bottom.
4. To keep your own changes, use **File → Save a copy in Drive**. Come back here for the latest version of each notebook.

## Projects

<!-- notebooks:start -->
### 🟣 Purple group · HIV

Using AI to support drug discovery for HIV, the virus that causes AIDS. _Project details will be added from the project plan in the shared Drive._

[Project folder](projects/purple/) · [Shared Drive folder](https://drive.google.com/drive/folders/1ym6spmjfJze60G52v7rUjbwQ4L_bqik5) · [Project plan](https://docs.google.com/presentation/d/1Igq5d_gt5hVbe3X-u8Fw8M6JOBXO3HqjGpTdlTzHKig)

**Notebooks**

1. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/purple/notebooks/purple_getting_started.ipynb) &nbsp;**Getting started** · _CPU_

### 🟡 Yellow group · Hypertension

Using AI to support drug discovery for hypertension (high blood pressure), a major risk factor for heart disease and stroke. _Project details will be added from the project plan in the shared Drive._

[Project folder](projects/yellow/) · [Shared Drive folder](https://drive.google.com/drive/folders/19Xg8Fu8_78R4QFjPXPotB91XCHpTy40h) · [Project plan](https://docs.google.com/presentation/d/17CRZ0wjGJrxvKFwZ9VDbXCRiNY_D0HLW05a0xYRgerQ)

**Notebooks**

1. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/yellow/notebooks/yellow_getting_started.ipynb) &nbsp;**Getting started** · _CPU_

### 🟠 Orange group · Tuberculosis

Using AI to support drug discovery for tuberculosis, caused by *Mycobacterium tuberculosis*. _Project details will be added from the project plan in the shared Drive._

[Project folder](projects/orange/) · [Shared Drive folder](https://drive.google.com/drive/folders/1L452i_YdUzQCUQwIBlvSCHG5Rn95qJId) · [Project plan](https://docs.google.com/presentation/d/1Ffp0yiNLy6vAM3VXu3Kcp2QfgG_x8P9Ot9Ioqu4yRns)

**Notebooks**

1. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/orange/notebooks/orange_getting_started.ipynb) &nbsp;**Getting started** · _CPU_

### 🔵 Blue group · Cryptosporidiosis

Structure-based drug discovery for cryptosporidiosis, a diarrhoeal disease caused by the parasite *Cryptosporidium parvum*. The group starts from an AlphaFold 3 model of the parasite's ABC1 transporter protein.

[Project folder](projects/blue/) · [Shared Drive folder](https://drive.google.com/drive/folders/1r2LlyX3ezVJBYe7iv2XHrf9mXQemMNw6) · [Project plan](https://docs.google.com/presentation/d/1ykMahn_C9_3RZzKUbI7cQLzNg6ptHl4Us1Qoqzc9vGU)

**Notebooks**

1. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/blue/notebooks/blue_getting_started.ipynb) &nbsp;**Getting started** · _CPU_
<!-- notebooks:end -->

## Shared Google Drive

You don't need GitHub to contribute. Each group has a folder in the [shared workshop Drive](https://drive.google.com/drive/folders/1V2IHpFEsjSbLgixtLpiKpFQKMAg6VSTg), under `Projects/<Color>Team/`:

- **`Data/`**: put your data files here. The organisers copy them into this repository so the notebooks can use them.
- **`Publications/`** and **`Presentations/`**: papers and slides for the group.
- **Project plan**: the group's working document.

## Repository layout

```
projects/<color>/
├── notebooks/        # Colab notebooks, named <color>_<what_it_does>.ipynb
├── data/             # data used by the notebooks (sources in data/SOURCES.md)
└── requirements.txt  # extra packages installed by the setup cell
```

## Reusing this material

The notebooks are released under the [GPL-3.0 licence](LICENSE). You're welcome to reuse and adapt them for your own teaching or research.

## About the Ersilia Open Source Initiative

The [Ersilia Open Source Initiative](https://ersilia.io) is a tech-nonprofit organization fueling sustainable research in the Global South. Ersilia's main asset is the [Ersilia Model Hub](https://github.com/ersilia-os/ersilia), an open-source repository of AI/ML models for antimicrobial drug discovery.

![Ersilia Logo](assets/Ersilia_Brand.png)
