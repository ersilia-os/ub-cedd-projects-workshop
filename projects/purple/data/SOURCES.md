# Data sources (Purple group)

Participants: put data files in the Drive folder **Projects/PurpleTeam/Data**, not here. They get copied into this folder so the notebooks can read them.

| File | Drive file | Drive ID | Drive modified | Copied on | Original source |
|---|---|---|---|---|---|

Nothing has been copied from the Drive yet.

`notebooks/purple_data_curation.ipynb` does not read anything from this folder that is
kept in the repository. It works on two ChEMBL exports that participants download
themselves, `chembl378_ec50.csv` and `chembl378_ic50.csv`: the activities recorded
against target `CHEMBL378` (Human immunodeficiency virus 1), one file per standard
type. In Colab the notebook asks for them to be uploaded at the start. They are
deliberately not committed, so `projects/*/data/chembl*.csv` is in `.gitignore`.

The notebook's own output, `hiv1_curated.csv`, is not saved here either. Colab loses
anything written to disk when the runtime disconnects, so the notebook downloads it to
the participant's computer instead. If the group uploads it to
**Projects/PurpleTeam/Data**, it can then be copied into this folder like any other
participant file, with a row added to the table above.
