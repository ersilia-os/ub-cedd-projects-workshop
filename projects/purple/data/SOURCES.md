# Data sources (Purple group)

Participants: put data files in the Drive folder **Projects/PurpleTeam/Data**, not here. They get copied into this folder so the notebooks can read them.

| File | Drive file | Drive ID | Drive modified | Copied on | Original source |
|---|---|---|---|---|---|
| `chembl378_ec50.csv` | chembl378_ec50.csv | `16rKoCtdTWWb3XYshADsP2Em3coflrDsP` | 2026-09-23T12:32:45Z | 2026-09-24 | ChEMBL website export, EC50 activities for target CHEMBL378 (Human immunodeficiency virus 1) |
| `chembl378_ic50.csv` | chembl378_ic50.csv | `1t72ghL8brmopl_bL2ydWNNu_Wwm55Cti` | 2026-09-23T12:32:09Z | 2026-09-24 | ChEMBL website export, IC50 activities for target CHEMBL378 (Human immunodeficiency virus 1) |

`notebooks/purple_data_curation.ipynb` reads both files.

The notebook's own output, `hiv1_curated.csv`, is not saved here. Colab loses anything
written to disk when the runtime disconnects, so the notebook downloads it to the
participant's computer instead. If the group uploads it to
**Projects/PurpleTeam/Data**, it can then be copied into this folder like any other
participant file, with a row added to the table above.
