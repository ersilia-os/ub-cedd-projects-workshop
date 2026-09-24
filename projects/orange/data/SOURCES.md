# Data sources (Orange group)

Participants: put data files in the Drive folder **Projects/OrangeTeam/Data**, not here. They get copied into this folder so the notebooks can read them.

| File | Drive file | Drive ID | Drive modified | Copied on | Original source |
|---|---|---|---|---|---|
| `mmc3.xlsx` | mmc3.xlsx | `1Zw6gwGY-wd252Iq4t9r48AvTdG7ezFDI` | 2026-09-24T09:53:02Z | 2026-09-24 | Supplementary Data S2 of Bosch B, DeJesus MA, Poulton NC, Zhang W, Engelhart CA, Zaveri A, et al. *Genome-wide gene expression tuning reveals diverse vulnerabilities of Mycobacterium tuberculosis*. Cell. 2021;184(17):4579-4592.e24. [doi:10.1016/j.cell.2021.06.033](https://doi.org/10.1016/j.cell.2021.06.033). CRISPRi essentiality calls and vulnerability index values for every gene in *M. tuberculosis* H37Rv, *M. tuberculosis* HN878 and *M. smegmatis* |
| `mtb_selected_targets.csv` | mtb_selected_targets.csv | `1tjgq4TEFjZ4TPhz2yFn2yAq-l1xRlqh2` | 2026-09-24T13:31:24Z | 2026-09-24 | Output of `notebooks/orange_target_selection.ipynb`, uploaded by the group. Derived from `mmc3.xlsx` above and UniProt. 348 protein targets |
| `mtb_targets_structures.csv` | (not yet in Drive) | | | 2026-09-24 | Output of `notebooks/orange_protein_structures.ipynb`, from a run of that notebook on 2026-09-24. Adds the chosen PDB chain (PDBe best structures) or AlphaFold model to each target in `mtb_selected_targets.csv` |

This is the group's own file from the Drive folder, with its original name. Its
SHA-256 is `9bfbee788668d8bb947b33724e94b3bd998b6a46e5e9e74b86b4a394fccccafa`, which
matches the publisher's open-access copy of the same supplementary file byte for byte,
so the group downloaded it from the paper unmodified.

It has five sheets: a `Legend` that describes every column, one sheet per screen
(`(1) Mtb H37Rv`, `(2) Mtb HN878`, `(3) Msmeg`) and `(4) Mtb diff vuln`, which
compares the two *M. tuberculosis* strains.

`notebooks/orange_target_selection.ipynb` reads the `Legend` and the three screen
sheets.

The outputs of the notebooks are not written here. Colab loses anything written to disk
when the runtime disconnects, so each notebook downloads its output to the
participant's computer, and the group uploads it to **Projects/OrangeTeam/Data**. From
there it is copied into this folder like any other participant file, with a row in the
table above, and the next notebook reads it:

- `mtb_selected_targets.csv` (from `orange_target_selection`) is read by
  `orange_protein_structures`. The Drive copy is byte-identical to a local run.
- `mtb_targets_structures.csv` (from `orange_protein_structures`) is read by
  `orange_pocket_detection`. It was copied from a local run so the pocket notebook could
  be built. If the group uploads its own copy to Drive, that copy replaces it here.

The structure files and P2Rank itself are downloaded at run time into
`data/downloads/`, which is not committed.
