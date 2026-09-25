# Data sources (Purple group)

Participants: put data files in the Drive folder **Projects/PurpleTeam/Data**, not here. They get copied into this folder so the notebooks can read them.

| File | Drive file | Drive ID | Drive modified | Copied on | Original source |
|---|---|---|---|---|---|
| `chembl378_ec50.csv` | chembl378_ec50.csv | `16rKoCtdTWWb3XYshADsP2Em3coflrDsP` | 2026-09-23T12:32:45Z | 2026-09-24 | ChEMBL website export, EC50 activities for target CHEMBL378 (Human immunodeficiency virus 1) |
| `chembl378_ic50.csv` | chembl378_ic50.csv | `1t72ghL8brmopl_bL2ydWNNu_Wwm55Cti` | 2026-09-23T12:32:09Z | 2026-09-24 | ChEMBL website export, IC50 activities for target CHEMBL378 (Human immunodeficiency virus 1) |
| `hiv1_curated.csv` | hiv1_curated.csv | `1Xln7r-peoog_uVhM4IOYXb_9hT-tzrY2` | 2026-09-24T13:25:08Z | 2026-09-24 | Output of `notebooks/purple_data_curation.ipynb` (classification set, 1 uM cutoff), uploaded by the group |
| `hiv1_regression.csv` | hiv1_regression.csv | `1yDbL8PzmGLSyk6TJcwfnazab9ATbo85G` | 2026-09-24T13:25:12Z | 2026-09-24 | Output of `notebooks/purple_data_curation.ipynb` (measured pActivity only), uploaded by the group |
| `eos1klk_hiv1_curated.csv` | eos1klk_hiv1_curated.csv | `141Id890dAhzRrb_qkfGmMW3UWDjPVPRk` | 2026-09-24T15:10:22Z | 2026-09-24 | The 21,387 curated molecules run through the Ersilia model [eos1klk](https://github.com/ersilia-os/eos1klk), which returns PCA, t-SNE, UMAP and TMAP coordinates on a map of 1.3M reference compounds |
| `hiv_drugs_approved.csv` | — (not from Drive) | — | — | 2026-09-24 | The 26 approved anti-HIV medicines, fetched from the ChEMBL API (`/data/molecule.json?pref_name__iexact=<name>`, keeping the records with `max_phase` 4) so that no structure was typed by hand. Columns: `drug`, `chembl_id`, `inchikey`, `smiles` |
| `chembl325_hdac1.csv` | — (not from Drive) | — | — | 2026-09-25 | ChEMBL API export, all 19,200 activity records for target CHEMBL325 (Histone deacetylase 1, *Homo sapiens*), keeping the columns `notebooks/purple_hdac1_feasibility.ipynb` needs |

`notebooks/purple_chemical_space.ipynb` reads `hiv1_curated.csv`, its `eos1klk`
coordinates and the approved drug list. `hiv_drugs_approved.csv` is a reference list, not
participant data: it came from ChEMBL rather than from Drive, and every drug in it matches
the curated table exactly on its InChIKey.

To add a new `eos1klk` file: run the SMILES through the model in Ersilia, upload the
output to **Projects/PurpleTeam/Data** as `eos1klk_<what the molecules are>.csv`, and ask
for it to be copied here.

`notebooks/purple_data_curation.ipynb` reads the two ChEMBL files and produces
`hiv1_curated.csv` and `hiv1_regression.csv`. Colab loses anything written to disk
when the runtime disconnects, so the notebook downloads them to the participant's
computer. The group uploaded them to **Projects/PurpleTeam/Data**, and they were
copied here so that `notebooks/purple_baseline_models.ipynb` can read them.

`notebooks/purple_hdac1_feasibility.ipynb` reads `chembl325_hdac1.csv`. Like
`hiv_drugs_approved.csv`, it came from the ChEMBL API rather than from Drive: the notebook
searches ChEMBL live for every target named HDAC1, but downloading the nineteen thousand
activity records each run would take several minutes in Colab, so they are stored here instead.
Re-create the file by paging through
`/data/activity.json?target_chembl_id=CHEMBL325` and keeping the columns the notebook uses.
