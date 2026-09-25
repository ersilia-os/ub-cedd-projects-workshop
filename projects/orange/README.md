# 🟠 Orange group · Tuberculosis

<!-- description:start -->
**Finding new drug targets in *Mycobacterium tuberculosis*.** Starting from a proteome of around 5,000 proteins, the group reviews the literature on essentiality to shortlist up to 500 candidates, then assesses computationally which of them are druggable, selective and novel: each target gets a 3D structure (PDB or AlphaFold) and its pockets are scored with P2Rank, with an interest in allosteric sites for inhibition.
<!-- description:end -->

- **Shared Drive folder:** [OrangeTeam](https://drive.google.com/drive/folders/1L452i_YdUzQCUQwIBlvSCHG5Rn95qJId). Data, publications and presentations for this group go here.
- **Project plan:** [Orange: Tuberculosis](https://docs.google.com/document/d/16Vh6i2dz49U-ZaYU2FctAxNXr9Lkg0iuWVfqCFikjCw)

## Notebooks

Click a button to open the notebook in Google Colab, then run the first code cell (Setup) before anything else.

<!-- notebooks:start -->
1. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/orange/notebooks/orange_target_selection.ipynb) &nbsp;**Selecting essential targets in M. tuberculosis** · _CPU_
2. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/orange/notebooks/orange_protein_structures.ipynb) &nbsp;**Finding a 3D structure for every target** · _CPU_
3. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/orange/notebooks/orange_pocket_detection.ipynb) &nbsp;**Finding binding pockets with P2Rank** · _CPU_
4. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/orange/notebooks/orange_mtb_proteome_embeddings.ipynb) &nbsp;**Compute ESM-C embeddings for the Mtb proteome** · _T4 GPU_
5. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/orange/notebooks/orange_essential_proteins_projections.ipynb) &nbsp;**Map essential proteins with UMAP and t-SNE** · _CPU_
6. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ersilia-os/ub-cedd-projects-workshop/blob/main/projects/orange/notebooks/orange_chembl_precedent.ipynb) &nbsp;**How much chemistry already exists for each target** · _CPU_
<!-- notebooks:end -->

## Data

Data files for this group live in [`data/`](data/), copied from the Drive `Data` folder. Where each file came from is recorded in [`data/SOURCES.md`](data/SOURCES.md).
