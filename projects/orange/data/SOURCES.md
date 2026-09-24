# Data sources (Orange group)

Participants: put data files in the Drive folder **Projects/OrangeTeam/Data**, not here. They get copied into this folder so the notebooks can read them.

| File | Drive file | Drive ID | Drive modified | Copied on | Original source |
|---|---|---|---|---|---|
| `bosc2021_vulnerability.xlsx` | mmc3.xlsx | `1Zw6gwGY-wd252Iq4t9r48AvTdG7ezFDI` | 2026-09-24T09:53:02Z | 2026-09-24 | Supplementary Data S2 of Bosch B, DeJesus MA, Poulton NC, Zhang W, Engelhart CA, Zaveri A, et al. *Genome-wide gene expression tuning reveals diverse vulnerabilities of Mycobacterium tuberculosis*. Cell. 2021;184(17):4579-4592.e24. [doi:10.1016/j.cell.2021.06.033](https://doi.org/10.1016/j.cell.2021.06.033). CRISPRi essentiality calls and vulnerability index values for every gene in *M. tuberculosis* H37Rv, *M. tuberculosis* HN878 and *M. smegmatis* |

This copy was **not** downloaded from Drive. It is the same supplementary file,
`mmc3.xlsx`, fetched from the publisher's open-access copy of the paper via Europe PMC
(`PMC8382161`), because the Drive connector can only hand a file's contents back as
base64 inside the conversation and a 3 MB spreadsheet does not fit. What was checked is
that both files are called `mmc3.xlsx` and are exactly 3,088,676 bytes; the Drive copy's
bytes were never read, so the two are not proven identical. It was renamed here so the
file name says what is inside it.

If you want the repository to hold the group's own Drive bytes rather than the
publisher's, download the file from `Projects/OrangeTeam/Data` by hand and overwrite
`bosc2021_vulnerability.xlsx`.

It has five sheets: a `Legend`, one sheet per screen (`(1) Mtb H37Rv`,
`(2) Mtb HN878`, `(3) Msmeg`) and `(4) Mtb diff vuln`, which compares the two
*M. tuberculosis* strains.

`notebooks/orange_target_selection.ipynb` reads the three screen sheets.

The notebook's own output, `mtb_selected_targets.csv`, is not saved here. Colab loses
anything written to disk when the runtime disconnects, so the notebook downloads it to
the participant's computer instead. If the group uploads it to
**Projects/OrangeTeam/Data**, it can then be copied into this folder like any other
participant file, with a row added to the table above.
