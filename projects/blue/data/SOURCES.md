# Data sources (Blue group)

Participants: put data files in the Drive folder **Projects/BlueTeam/Data**, not here. They get copied into this folder so the notebooks can read them.

| File | Drive file | Drive ID | Drive modified | Copied on | Original source |
|---|---|---|---|---|---|
| `pharmit_hits_molport.csv` | provisional_pharmit_results/pharmit_hits_molport_nonredundant.csv | `19k3hXJoaT2U1iAO_HYFFqYyEcuFu1237` | 2026-09-24T13:37:55Z | 2026-09-24 | The 28,732 non-redundant hits of the [Pharmit](https://pharmit.csb.pitt.edu) screen of the MolPort purchasable library against the CpABC1 pharmacophore, with their MolPort catalogue numbers |
| `eos1klk_pharmit_hits.csv` | eos1klk_pharmit_hits.csv | `1n4kw025Lm1ZJ-NxUHB0A1Q9giQ8qV7-Z` | 2026-09-24T15:30:47Z | 2026-09-24 | Those same 28,732 molecules run through the Ersilia model [eos1klk](https://github.com/ersilia-os/eos1klk), which returns PCA, t-SNE, UMAP and TMAP coordinates on a map of 1.3M reference compounds |
| `eos1klk_silymarin.csv` | eos1klk_silymarin.csv | `1gh1jGrluSvocB3VgJRCkD5k_tvYbKlSD` | 2026-09-24T16:23:12Z | 2026-09-24 | Silymarin, the seed the pharmacophore was built from, run through the same model so it can be drawn on the same maps. Written without stereochemistry as `COc1cc(C2Oc3cc(C4Oc5cc(O)cc(O)c5C(=O)C4O)ccc3OC2CO)ccc1O` |
| `cpabc1_silymarin.pdb` | Preliminary_data/CpABC1-Silymarin.pdb | `1X7UzFXG6p1fGxg2ekxqkLYP9eTYLVxNW` | 2025-05-21T07:48:58Z | 2026-09-24 | The blue group's CpABC1–silymarin complex (a CpABC1 model with docked silybin, minimised in Schrödinger Maestro), copied unchanged |
| `cpabc1_receptor.pdb` | (derived, not in Drive) | | | 2026-09-24 | The protein heavy atoms of `cpabc1_silymarin.pdb` (11,435 atoms, chain A), same coordinates |
| `silymarin_ligand.sdf` | (derived, not in Drive) | | | 2026-09-24 | The silybin heavy atoms of `cpabc1_silymarin.pdb` (35 atoms), written with RDKit, same coordinates |

`notebooks/blue_chemical_space.ipynb` reads the first three files. `cpabc1_receptor.pdb` and
`silymarin_ligand.sdf` are read by `notebooks/blue_pharmacophore.ipynb`, and the complex by the
sandbox notebook `sandbox/gnina_docking_screen.ipynb` when it runs locally.

The pharmacophore itself came from the CpABC1–silymarin complex in
**Projects/BlueTeam/Data/Preliminary_data** (`CpABC1-Silymarin.pdb`, `Sil.sdf`) by way of
PharmacoNet and PharmacoForge; the Pharmit sessions and the minimised poses are in
**Pharmit_Pharmacoforge_&_outputs**. Only the complex is copied here (above), plus the
receptor and ligand split out of it. `Sil.sdf`, the Pharmit sessions and the poses are not.

The two Pharmit result files (`provisional_pharmit_query_results_1.sdf`, 28 MB, Drive ID
`1X2HjfiGu5-f6VJrDHtgcEa6pCxB4yJRX`, and `..._2.sdf`, 140 MB, `19GBjbEhGeBhgPtOHRe0pdfT7ROm011O9`,
both in **Data/provisional_pharmit_results**) are too large for the repository.
`notebooks/blue_pharmit_hits.ipynb` asks you to upload them from Drive, or reads them from
`data/downloads/` when it runs locally.

The seed's stereocentres in `Sil.sdf` are inferred from the docked 3D pose and match
neither silybin A nor silybin B, so the flat SMILES above is what goes through the model.

To add a new `eos1klk` file: run the SMILES through the model in Ersilia, upload the
output to **Projects/BlueTeam/Data** as `eos1klk_<what the molecules are>.csv`, and ask
for it to be copied here.
