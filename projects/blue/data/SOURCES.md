# Data sources (Blue group)

Participants: put data files in the Drive folder **Projects/BlueTeam/Data**, not here. They get copied into this folder so the notebooks can read them.

| File | Drive file | Drive ID | Drive modified | Copied on | Original source |
|---|---|---|---|---|---|
| `pharmit_hits_molport.csv` | provisional_pharmit_results/pharmit_hits_molport_nonredundant.csv | `19k3hXJoaT2U1iAO_HYFFqYyEcuFu1237` | 2026-09-24T13:37:55Z | 2026-09-24 | The 28,732 non-redundant hits of the [Pharmit](https://pharmit.csb.pitt.edu) screen of the MolPort purchasable library against the CpABC1 pharmacophore, with their MolPort catalogue numbers |
| `eos1klk_pharmit_hits.csv` | eos1klk_pharmit_hits.csv | `1n4kw025Lm1ZJ-NxUHB0A1Q9giQ8qV7-Z` | 2026-09-24T15:30:47Z | 2026-09-24 | Those same 28,732 molecules run through the Ersilia model [eos1klk](https://github.com/ersilia-os/eos1klk), which returns PCA, t-SNE, UMAP and TMAP coordinates on a map of 1.3M reference compounds |
| `eos1klk_silymarin.csv` | eos1klk_silymarin.csv | `1gh1jGrluSvocB3VgJRCkD5k_tvYbKlSD` | 2026-09-24T16:23:12Z | 2026-09-24 | Silymarin, the seed the pharmacophore was built from, run through the same model so it can be drawn on the same maps. Written without stereochemistry as `COc1cc(C2Oc3cc(C4Oc5cc(O)cc(O)c5C(=O)C4O)ccc3OC2CO)ccc1O` |
| `eos5mnx_silymarin.csv` | eos5mnx_silymarin.csv | `1a2BSR8mVqWnjXBfNpj1zSHqJlaJRAy8m` | 2026-09-24T17:43:21Z | 2026-09-24 | Silymarin run through the Ersilia model [eos5mnx](https://github.com/ersilia-os/eos5mnx) (SAND), which returns 512 numbers describing the molecule's 3D shape. Run on the stereochemical SMILES in `silymarin.csv`, not the flat one used for `eos1klk_silymarin.csv` |
| `cpabc1_silymarin.pdb` | Preliminary_data/CpABC1-Silymarin.pdb | `1X7UzFXG6p1fGxg2ekxqkLYP9eTYLVxNW` | 2025-05-21T07:48:58Z | 2026-09-24 | The blue group's CpABC1–silymarin complex (a CpABC1 model with docked silybin, minimised in Schrödinger Maestro), copied unchanged |
| `silymarin.csv` | (derived, not in Drive) | | | 2026-09-24 | Silybin as a single SMILES, with the stereochemistry of the docked pose. Written from `silymarin_ligand.sdf`, whose canonical SMILES it matches exactly |
| `cpabc1_receptor.pdb` | (derived, not in Drive) | | | 2026-09-24 | The protein heavy atoms of `cpabc1_silymarin.pdb` (11,435 atoms, chain A), same coordinates. Residues 1-1431 of UniProt **Q9XYH6**, numbered continuously with no gaps |
| `eos42ez_sand_hits.csv` | (derived, not in Drive) | | | 2026-09-25 | The 1,887 shape-similarity hits run through the Ersilia model [eos42ez](https://github.com/ersilia-os/eos42ez) (antibiotics-ai-cytotox, from [Wong et al., Nature 2023](https://doi.org/10.1038/s41586-023-06887-8)), computed offline by the developer. Columns `cytotoxicity_hepg2`, `cytotoxicity_hskmc` and `cytotoxicity_imr90` are liver, skeletal muscle and lung cells, each 0 to 1 where **higher means more likely to be toxic** - the opposite direction to the other scores here. The model was trained on 39,312 compounds screened at 10 uM against a 90%-viability threshold |
| `sand_shape_similarity.csv` | (derived, not in Drive) | | | 2026-09-26 | All 28,732 Pharmit hits scored for 3D shape similarity to silymarin, as `notebooks/blue_sand_shape_similarity.ipynb` computes it: the cosine between each molecule's 512-number [eos5mnx](https://github.com/ersilia-os/eos5mnx) (SAND) shape descriptor and silymarin's. `tanimoto` is the ordinary 2D fingerprint similarity, for comparison. Written from that notebook's own output so the figures in `notebooks/blue_plots.ipynb` can redraw its shortlist without the 183 MB descriptor file |
| `sprint_drug_projector.pt` | (derived, not in Drive) | | | 2026-09-25 | The molecule half of the trained SPRINT model (23 tensors, 22.8 MB), taken out of the authors' Lit-PCBA checkpoint. SPRINT is MIT-licensed; the checkpoint is linked from [its repository](https://github.com/abhinadduri/panspecies-dti/blob/main/checkpoints/README.md). Extracted so `notebooks/blue_sprint_filter.ipynb` does not have to install SPRINT or download the full 191 MB checkpoint |
| `cpabc1_sprint_embedding.npy` | (derived, not in Drive) | | | 2026-09-25 | CpABC1 as the 1024 numbers SPRINT describes a protein with. Computed from `cpabc1_receptor.pdb`: foldseek structure tokens for all 1,431 residues, cut to residues 214-1235 (a 1,022-residue window centred on the silybin site, which is SaProt's limit), then through SaProt-650M and SPRINT's protein network. Stored because it never changes, so the notebook avoids a 2.43 GB model download |
| `silymarin_ligand.sdf` | (derived, not in Drive) | | | 2026-09-24 | The silybin heavy atoms of `cpabc1_silymarin.pdb` (35 atoms), written with RDKit, same coordinates |

`notebooks/blue_chemical_space.ipynb` reads the first three files. `cpabc1_receptor.pdb` and
`silymarin_ligand.sdf` are read by `notebooks/blue_pharmacophore.ipynb`, and the complex by the
sandbox notebook `sandbox/gnina_docking_screen.ipynb` when it runs locally.

## The target

CpABC1 is UniProt **[Q9XYH6](https://www.uniprot.org/uniprotkb/Q9XYH6)**
(`Q9XYH6_CRYPV`, "ATP-binding cassette protein", *Cryptosporidium parvum*, `GN=CpABC`),
1,431 residues. Use this accession for anything that needs the sequence rather than the
structure.

The group's AlphaFold 3 model is in **Projects/BlueTeam/Data/fold_q9xyh6_cpabc1**, Drive ID
`1Uy0SxhkhN7j6s36gBHLsIYLvdy8b9MXY`: five models from the AlphaFold Server, run on seed 42
with structure templates enabled. Not copied here: the five per-residue confidence files are
about 17.5 MB each, so the folder is over 90 MB before counting the MSAs. Its
`fold_q9xyh6_cpabc1_job_request.json` records the exact input sequence, and that sequence is
identical to both Q9XYH6 and the sequence read out of `cpabc1_receptor.pdb` above — checked
character by character on 2026-09-25, so the Maestro-minimised complex, the AlphaFold model
and the database entry all cover the same full-length protein.

`notebooks/blue_sprint_filter.ipynb` reads the two SPRINT files above, plus
`sand_filtered_hits.csv`, which is not in this folder: the shape-similarity notebook writes
it to `data/downloads/` and participants upload their own copy. The notebook is a ranking
step, not a binding prediction - scoring the same 20-compound control panel against human
carbonic anhydrase II, an enzyme unrelated to ABC transporters, separated known transporter
inhibitors from matched decoys as well as CpABC1 did (+0.369 against +0.340), so the score
responds mostly to the molecule rather than to the target.

`notebooks/blue_cytotoxicity_filter.ipynb` reads `eos42ez_sand_hits.csv` above and joins it
on SMILES to `sand_filtered_hits.csv`, which participants upload, to pick up the MolPort
catalogue numbers. It ranks on the liver-cell column alone. Liver and muscle predictions
correlate at 0.945, so one stands in for the other, but lung predictions correlate at only
0.658 and therefore carry information the filter does not use - a limitation the notebook
states, with an exercise that reruns the selection on the lung column.

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

`eos5mnx_pharmit_hits.csv`, the same model run on all 28,732 hits, is 183 MB and too large for the
repository. It is in **Projects/BlueTeam/Data**, Drive ID `13NsF7-vsmqgOIToiJFOHgDAe55VdHLVd`,
modified 2026-09-24T17:30:28Z. `notebooks/blue_sand_shape_similarity.ipynb` asks you to upload it,
or reads it from `data/downloads/` when it runs locally.

That same notebook writes `data/downloads/sand_filtered_hits.csv`, the 1,887 hits that pass both its
shape ranking and its property rules, as two columns (`molport_id`, `smiles`) ready to feed to
another model. Like everything in `data/downloads/`, it is not in the repository: run the notebook
again to recreate it.

The seed's stereocentres in `Sil.sdf` are inferred from the docked 3D pose and match
neither silybin A nor silybin B, so the flat SMILES above is what goes through the model.

To add a new `eos1klk` file: run the SMILES through the model in Ersilia, upload the
output to **Projects/BlueTeam/Data** as `eos1klk_<what the molecules are>.csv`, and ask
for it to be copied here.
