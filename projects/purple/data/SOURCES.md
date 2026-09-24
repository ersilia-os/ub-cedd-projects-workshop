# Data sources (Purple group)

Participants: put data files in the Drive folder **Projects/PurpleTeam/Data**, not here. They get copied into this folder so the notebooks can read them.

| File | Drive file | Drive ID | Drive modified | Copied on | Original source |
|---|---|---|---|---|---|
| `chembl378_ec50.csv` | chembl378_ec50.csv | `16rKoCtdTWWb3XYshADsP2Em3coflrDsP` | 2026-09-23T12:32:45Z | 2026-09-24 | ChEMBL website export, EC50 activities for target CHEMBL378 (Human immunodeficiency virus 1) |
| `chembl378_ic50.csv` | chembl378_ic50.csv | `1t72ghL8brmopl_bL2ydWNNu_Wwm55Cti` | 2026-09-23T12:32:09Z | 2026-09-24 | ChEMBL website export, IC50 activities for target CHEMBL378 (Human immunodeficiency virus 1) |
| `hiv1_curated.csv` | hiv1_curated.csv | `1Xln7r-peoog_uVhM4IOYXb_9hT-tzrY2` | 2026-09-24T13:25:08Z | 2026-09-24 | Output of `notebooks/purple_data_curation.ipynb` (classification set, 1 uM cutoff), uploaded by the group |
| `hiv1_regression.csv` | hiv1_regression.csv | `1yDbL8PzmGLSyk6TJcwfnazab9ATbo85G` | 2026-09-24T13:25:12Z | 2026-09-24 | Output of `notebooks/purple_data_curation.ipynb` (measured pActivity only), uploaded by the group |

`notebooks/purple_data_curation.ipynb` reads the two ChEMBL files and produces
`hiv1_curated.csv` and `hiv1_regression.csv`. Colab loses anything written to disk
when the runtime disconnects, so the notebook downloads them to the participant's
computer. The group uploaded them to **Projects/PurpleTeam/Data**, and they were
copied here so that `notebooks/purple_baseline_models.ipynb` can read them.
