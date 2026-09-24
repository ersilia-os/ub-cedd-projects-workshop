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

`notebooks/yellow_data_curation.ipynb` reads all seven files. It also fetches compound
structures and assay depositors from PubChem the first time it runs, and keeps them in
`data/downloads/` (git-ignored).
