# Data sources (Blue group)

Participants: put data files in the Drive folder **Projects/BlueTeam/Data**, not here. They get copied into this folder so the notebooks can read them.

| File | Drive file | Drive ID | Drive modified | Copied on | Original source |
|---|---|---|---|---|---|
| `pharmit_hits_molport.csv` | provisional_pharmit_results/pharmit_hits_molport_nonredundant.csv | `19k3hXJoaT2U1iAO_HYFFqYyEcuFu1237` | 2026-09-24T13:37:55Z | 2026-09-24 | The 28,732 non-redundant hits of the [Pharmit](https://pharmit.csb.pitt.edu) screen of the MolPort purchasable library against the CpABC1 pharmacophore, with their MolPort catalogue numbers |
| `eos1klk_pharmit_hits.csv` | eos1klk_pharmit_hits.csv | `1n4kw025Lm1ZJ-NxUHB0A1Q9giQ8qV7-Z` | 2026-09-24T15:30:47Z | 2026-09-24 | Those same 28,732 molecules run through the Ersilia model [eos1klk](https://github.com/ersilia-os/eos1klk), which returns PCA, t-SNE, UMAP and TMAP coordinates on a map of 1.3M reference compounds |
| `eos1klk_silymarin.csv` | _not yet in Drive_ | — | — | — | Silymarin, the seed the pharmacophore was built from, run through the same model so it can be drawn on the same maps. Written without stereochemistry as `COc1cc(C2Oc3cc(C4Oc5cc(O)cc(O)c5C(=O)C4O)ccc3OC2CO)ccc1O` |

`notebooks/blue_chemical_space.ipynb` reads all three files.

The pharmacophore itself came from the CpABC1–silymarin complex in
**Projects/BlueTeam/Data/Preliminary_data** (`CpABC1-Silymarin.pdb`, `Sil.sdf`) by way of
PharmacoNet and PharmacoForge; the Pharmit sessions and the minimised poses are in
**Pharmit_Pharmacoforge_&_outputs**. None of that is copied here, because the notebooks
only need the hit list and its coordinates.

The seed's stereocentres in `Sil.sdf` are inferred from the docked 3D pose and match
neither silybin A nor silybin B, so the flat SMILES above is what goes through the model.

To add a new `eos1klk` file: run the SMILES through the model in Ersilia, upload the
output to **Projects/BlueTeam/Data** as `eos1klk_<what the molecules are>.csv`, and ask
for it to be copied here.
