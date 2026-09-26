# Data sources (Yellow group)

Participants: put data files in the Drive folder **Projects/YellowTeam/Data**, not here. They get copied into this folder so the notebooks can read them.

| File | Drive file | Drive ID | Drive modified | Copied on | Original source |
|---|---|---|---|---|---|
| `chembl_ace_human.csv` | chembl_ace_human.csv | `1wPty3kyQFTfIGeEozko047nHpfOh-11z` | 2026-09-24T09:41:12Z | 2026-09-24 | ChEMBL website export, all activities for target CHEMBL1808 (human ACE) |
| `chembl_ace_rabbit.csv` | chembl_ace_rabbit.csv | `1_GvtiSVc5cwWnXAK4-9gKOECI6vwp0E-` | 1979-12-31T23:00:00Z (as reported by Drive) | 2026-09-24 | ChEMBL website export, all activities for target CHEMBL4074 (rabbit ACE) |
| `bindingdb_ace_human.tsv` | bindingdb_ace_human.tsv | `16--BdYrTO7l3nblcxSIhKdhQHllVnRrr` | 2026-09-24T09:35:09Z | 2026-09-24 | BindingDB target download `BDBpoly_2161.tsv` (human ACE, UniProt P12821). This copy keeps only the 11 rows not curated from ChEMBL; the full download has 1,002 |
| `bindingdb_ace_rabbit.tsv` | bindingdb_ace_rabbit.tsv | `1T9EiqZhWWV7TKfsZWREm9Tn4oWdEsZiu` | 2026-09-24T09:42:03Z | 2026-09-24 | BindingDB target download `BDBpoly_50000035.tsv` (rabbit ACE, UniProt P12822) |
| `pubchem_ace_human.csv` | pubchem_ace_human.csv | `1AZ55rUeGlqafCNyBxEWURPVWTh8Lejnn` | 2026-09-24T09:35:41Z | 2026-09-24 | PubChem bioactivity table for protein P12821 (PUG-REST `concise/CSV`) |
| `pubchem_ace_rabbit.csv` | pubchem_ace_rabbit.csv | `1yqd6xrrCvqmCsI0GvuimGmEFwkXquQJO` | 2026-09-24T09:43:03Z | 2026-09-24 | PubChem bioactivity table for protein P12822 (PUG-REST `concise/CSV`) |
| `manual_ace_human.csv` | manual_ace_human.csv | `1VF9V1gi9EZArUPIQRu-nZboHgVq5snij` | 2026-09-24T09:36:17Z | 2026-09-24 | The group's own table (also in Drive as the sheet *ace_data_new*): rows taken from BindingDB and ChEMBL, plus rows curated by hand from published papers (`source` = `m_curated`) |
| `ace_human_curated.csv` | ace_human_curated.csv | `1ZEVgN5_j2zLzoh4hqhtXdR2O3Kp4dqKG` | 2026-09-24T11:38:15Z | 2026-09-24 | The 1,018 molecules `notebooks/yellow_data_curation.ipynb` produced, uploaded to Drive by the group |
| `eos1klk_ace_human.csv` | eos1klk_ace_human_1018.csv | `1vQN1lTXX_L_6Y5u9ELgSbr2zZnxbFUfS` | 2026-09-24T14:07:02Z | 2026-09-24 | Those same 1,018 molecules run through the Ersilia model [eos1klk](https://github.com/ersilia-os/eos1klk), which returns PCA, t-SNE, UMAP and TMAP coordinates on a map of 1.3M reference compounds |
| `reinvent_mols_41k.csv` | reinvent_mols_41k.csv | `1WURK9lmCzMCrUM_fw7RZlbo5ZvT8ZvZ0` | 2026-09-26T07:37:17Z | 2026-09-26 | 41,374 molecules (SMILES and ID) generated with REINVENT by the group, plus captopril and lisinopril as references |

`notebooks/yellow_data_curation.ipynb` reads the seven source files. It also fetches
compound structures and assay depositors from PubChem the first time it runs, and keeps
them in `data/downloads/` (git-ignored).

`notebooks/yellow_chemical_space.ipynb` reads the last two files: the curated table and
its `eos1klk` coordinates. Colab deletes anything a notebook writes when the runtime
disconnects, so the curation notebook downloads its result to the participant's computer
and the group uploads it to Drive; the copy here is what the later notebooks read.

To add a new `eos1klk` file: run the SMILES through the model in Ersilia, upload the
output to **Projects/YellowTeam/Data** as `eos1klk_<what the molecules are>.csv`, and ask
for it to be copied here.
