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

**Machine learning for the discovery of anti-HIV and HDAC1 inhibitors from African natural products.** The group curates HIV-1 whole-cell assay data from ChEMBL, improves the activity model currently in use (better featurisation, handling of class imbalance, interpretable descriptors), and then reuses the same pipeline on a second target, HDAC1, as a proof of concept.

[Project folder](projects/purple/) · [Shared Drive folder](https://drive.google.com/drive/folders/1ym6spmjfJze60G52v7rUjbwQ4L_bqik5) · [Project plan](https://docs.google.com/document/d/1XGHnfHVm5Lmtz0epk3pzXoguQIZq3U25Cz2QOOsyjZE)

**Notebooks**

1. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/purple/notebooks/purple_getting_started.ipynb) &nbsp;**Getting started** · _CPU_

### 🟡 Yellow group · Hypertension

**AI-driven discovery of new inhibitors of angiotensin-converting enzyme (ACE1) for hypertension**, a disease affecting around a third of Cameroonian adults aged 30–79. The group curates ACE1 inhibition data from ChEMBL, builds a classifier and a regressor, and uses them to predict the activity of selected natural products such as indoles and xanthones, checking first whether those compounds fall inside the models' applicability domain.

[Project folder](projects/yellow/) · [Shared Drive folder](https://drive.google.com/drive/folders/19Xg8Fu8_78R4QFjPXPotB91XCHpTy40h) · [Project plan](https://docs.google.com/document/d/1kr3k6K3SqIL37-VISkkjuPPYTb0QrlQ7s7ry-bMaqKc)

**Notebooks**

1. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/yellow/notebooks/yellow_getting_started.ipynb) &nbsp;**Getting started** · _CPU_

### 🟠 Orange group · Tuberculosis

**Finding new drug targets in *Mycobacterium tuberculosis*.** Starting from a proteome of around 5,000 proteins, the group reviews the literature on essentiality to shortlist up to 500 candidates, then assesses computationally which of them are druggable, selective and novel, with an interest in allosteric sites for inhibition.

[Project folder](projects/orange/) · [Shared Drive folder](https://drive.google.com/drive/folders/1L452i_YdUzQCUQwIBlvSCHG5Rn95qJId) · [Project plan](https://docs.google.com/document/d/16Vh6i2dz49U-ZaYU2FctAxNXr9Lkg0iuWVfqCFikjCw)

**Notebooks**

1. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/orange/notebooks/orange_getting_started.ipynb) &nbsp;**Getting started** · _CPU_

### 🔵 Blue group · Cryptosporidiosis

***In silico* generation and validation of silymarin analogues against CpABC1**, an ABC transporter of *Cryptosporidium parvum* sitting at the host–parasite interface. Silymarin inhibits parasite growth, but only at high concentrations, so the group compares AlphaFold and I-TASSER models of the target, derives a pharmacophore from the CpABC1–silymarin complex, and uses it to screen and rank better candidates.

[Project folder](projects/blue/) · [Shared Drive folder](https://drive.google.com/drive/folders/1r2LlyX3ezVJBYe7iv2XHrf9mXQemMNw6) · [Project plan](https://docs.google.com/document/d/1fkpgSYlQGA0GsVnExQSWIfpCbuVIzpoS_DjwCDoBC28)

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
