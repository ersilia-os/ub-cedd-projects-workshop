"""Does PSICHIC run locally on CpABC1, and how long does each SMILES take?

PSICHIC (Koh et al., Nat Mach Intell 2024, https://github.com/huankoh/PSICHIC) scores a
protein sequence against a ligand SMILES with no structure and no docking. This script
answers the only two questions that matter before we consider it for the blue project:
does it run on a laptop with the full 1,431-residue CpABC1 model, and what does it cost
per compound.

The cost splits in two, and the split is the whole point:

  * protein setup, paid ONCE per target. ESM-2 650M embeds the sequence and predicts a
    contact map. This is the expensive part and it scales with sequence length.
  * ligand scoring, paid per compound, reusing the protein graph.

So "seconds per SMILES" only means something once the protein is already encoded. Both
numbers are reported separately below.

Not workshop material: this is a sandbox feasibility test. Run it from the repo root with
the `psichic` conda env:

    conda run -n psichic python sandbox/psichic_smoke_test.py
"""

import os
import resource
import sys
import time

import pandas as pd
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PSICHIC_DIR = os.path.join(REPO, "tools", "PSICHIC")
# PSICHIC_XL, the version the authors say is usable as-is on a target it was not trained
# on. CpABC1 is exactly that case.
WEIGHTS = os.path.join(PSICHIC_DIR, "trained_weights", "multitask_PSICHIC")
RECEPTOR = os.path.join(REPO, "projects", "blue", "data", "cpabc1_receptor.pdb")
WORK = os.path.join(REPO, "sandbox", "work")
DEVICE = "cpu"
SEED = 42

# Two groups. The silymarin family is what the blue group cares about: silybin is the
# seed the pharmacophore was built from, and the four flavonoids are already used by the
# gnina sandbox notebook. The reference inhibitors are the control that makes the numbers
# interpretable -- all three are established inhibitors of human P-glycoprotein (ABCB1),
# the closest well-studied relative of CpABC1. If PSICHIC cannot rank these above the
# flavonoids, it has no signal on this target and the scores should not be used to rank
# a library. SMILES taken from PubChem by CID, not typed from memory.
SILYMARIN_FAMILY = [
    ("silybin", "COc1cc([C@@H]2Oc3cc([C@H]4Oc5cc(O)cc(O)c5C(=O)[C@@H]4O)ccc3O[C@@H]2CO)ccc1O"),
    ("taxifolin", "C1=CC(=C(C=C1[C@@H]2[C@H](C(=O)C3=C(C=C(C=C3O2)O)O)O)O)O"),
    ("quercetin", "C1=CC(=C(C=C1C2=C(C(=O)C3=C(C=C(C=C3O2)O)O)O)O)O"),
    ("luteolin", "C1=CC(=C(C=C1C2=CC(=O)C3=C(C=C(C=C3O2)O)O)O)O"),
    ("eriodictyol", "C1[C@H](OC2=CC(=CC(=C2C1=O)O)O)C3=CC(=C(C=C3)O)O"),
]
REFERENCE_INHIBITORS = [
    # verapamil, PubChem CID 2520
    ("verapamil", "CC(C)C(CCCN(C)CCC1=CC(=C(C=C1)OC)OC)(C#N)C2=CC(=C(C=C2)OC)OC"),
    # cyclosporin A, CID 5284373 -- a 1.2 kDa cyclic peptide, also a useful stress test
    # of the ligand graph builder
    ("cyclosporin A", "CC[C@H]1C(=O)N(CC(=O)N([C@H](C(=O)N[C@H](C(=O)N([C@H](C(=O)N[C@H](C(=O)N[C@@H](C(=O)N([C@H](C(=O)N([C@H](C(=O)N([C@H](C(=O)N([C@H](C(=O)N1)[C@@H]([C@H](C)C/C=C/C)O)C)C(C)C)C)CC(C)C)C)CC(C)C)C)C)C)CC(C)C)C)C(C)C)CC(C)C)C)C"),
    # tariquidar, CID 148201 -- a third-generation, highly specific P-gp inhibitor
    ("tariquidar", "COC1=C(C=C2CN(CCC2=C1)CCC3=CC=C(C=C3)NC(=O)C4=CC(=C(C=C4NC(=O)C5=CC6=CC=CC=C6N=C5)OC)OC)OC"),
]
# The decoy control. The reference inhibitors above are all much larger and more
# lipophilic than the flavonoids, so ranking them higher is equally consistent with
# "PSICHIC scores big greasy molecules highly" as with anything about CpABC1. These
# decoys are size-matched to the inhibitors but have no ABC-transporter pharmacology at
# all, and they deliberately span both polar (raffinose, vancomycin) and very lipophilic
# (tocopheryl acetate, trilaurin, cholesteryl oleate) chemistry so that molecular weight
# and lipophilicity can be told apart. If the decoys score with the inhibitors, the
# ranking is measuring bulk, not the target.
DECOYS = [
    # raffinose, CID 439242, 504 Da -- trisaccharide, very polar
    ("raffinose", "C([C@@H]1[C@@H]([C@@H]([C@H]([C@H](O1)OC[C@@H]2[C@H]([C@@H]([C@H]([C@H](O2)O[C@]3([C@H]([C@@H]([C@H](O3)CO)O)O)CO)O)O)O)O)O)O)O"),
    # sucrose octaacetate, CID 31340, 679 Da -- size-matched to tariquidar
    ("sucrose octaacetate", "CC(=O)OC[C@@H]1[C@H]([C@@H]([C@H]([C@H](O1)O[C@]2([C@H]([C@@H]([C@H](O2)COC(=O)C)OC(=O)C)OC(=O)C)COC(=O)C)OC(=O)C)OC(=O)C)OC(=O)C"),
    # alpha-tocopherol acetate, CID 86472, 473 Da -- size-matched to verapamil, lipophilic
    ("tocopheryl acetate", "CC1=C(C(=C(C2=C1O[C@](CC2)(C)CCC[C@H](C)CCC[C@H](C)CCCC(C)C)C)OC(=O)C)C"),
    # trilaurin, CID 10851, 639 Da -- triglyceride, very lipophilic
    ("trilaurin", "CCCCCCCCCCCC(=O)OCC(COC(=O)CCCCCCCCCCC)OC(=O)CCCCCCCCCCC"),
    # cholesteryl oleate, CID 5283632, 651 Da -- sterol ester, very lipophilic
    ("cholesteryl oleate", "CCCCCCCC/C=C\\CCCCCCCC(=O)O[C@H]1CC[C@@]2([C@H]3CC[C@]4([C@H]([C@@H]3CC=C2C1)CC[C@@H]4[C@H](C)CCCC(C)C)C)C"),
    # vancomycin, CID 14969, 1449 Da -- size-matched to cyclosporin A, polar glycopeptide
    ("vancomycin", "C[C@H]1[C@H]([C@@](C[C@@H](O1)O[C@@H]2[C@H]([C@@H]([C@H](O[C@H]2OC3=C4C=C5C=C3OC6=C(C=C(C=C6)[C@H]([C@H](C(=O)N[C@H](C(=O)N[C@H]5C(=O)N[C@@H]7C8=CC(=C(C=C8)O)C9=C(C=C(C=C9O)O)[C@H](NC(=O)[C@H]([C@@H](C1=CC(=C(O4)C=C1)Cl)O)NC7=O)C(=O)O)CC(=O)N)NC(=O)[C@@H](CC(C)C)NC)O)Cl)CO)O)O)(C)N)O"),
]
COMPOUNDS = ([(n, s, "silymarin family") for n, s in SILYMARIN_FAMILY]
             + [(n, s, "reference P-gp inhibitor") for n, s in REFERENCE_INHIBITORS]
             + [(n, s, "size-matched decoy") for n, s in DECOYS])

THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q", "GLU": "E",
    "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F",
    "PRO": "P", "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
    # protonation-state variants Maestro may leave in the file
    "HID": "H", "HIE": "H", "HIP": "H", "CYX": "C", "ASH": "D", "GLH": "E", "LYN": "K",
}


def sequence_from_pdb(path):
    """Read the one-letter sequence of chain A, in file order.

    PSICHIC wants a plain sequence, so the coordinates are irrelevant here. What does
    matter is that a gapped model silently drops residues, so the caller is told about
    any break in the residue numbering.
    """
    seen, seq, numbers = set(), [], []
    with open(path) as f:
        for line in f:
            if not line.startswith("ATOM"):
                continue
            chain, number, icode = line[21], int(line[22:26]), line[26]
            key = (chain, number, icode)
            if key in seen:
                continue
            seen.add(key)
            seq.append(THREE_TO_ONE.get(line[17:20].strip(), "X"))
            numbers.append(number)
    gaps = [(numbers[i], numbers[i + 1]) for i in range(len(numbers) - 1)
            if numbers[i + 1] != numbers[i] + 1]
    return "".join(seq), gaps


def peak_gb():
    """Peak resident memory of this process, in GB (ru_maxrss is bytes on macOS)."""
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / 1024**3 if sys.platform == "darwin" else peak / 1024**2


def main():
    torch.manual_seed(SEED)
    os.makedirs(WORK, exist_ok=True)
    sys.path.insert(0, PSICHIC_DIR)

    import json

    from models.net import net
    from utils import ligand_init, protein_init
    from utils.dataset import ProteinMoleculeDataset
    from utils.utils import DataLoader, virtual_screening

    sequence, gaps = sequence_from_pdb(RECEPTOR)
    print(f"CpABC1: {len(sequence)} residues from {os.path.relpath(RECEPTOR, REPO)}")
    print(f"  numbering gaps: {gaps if gaps else 'none, continuous'}")
    # PSICHIC embeds sequences over 700 residues in overlapping 350-residue windows
    # (utils/protein_init.py), so a target this size costs several ESM passes but does
    # not blow up quadratically.
    print(f"  over the 700-residue threshold, so ESM runs in windows\n")

    print("Loading the PSICHIC_XL model ...")
    t0 = time.perf_counter()
    with open(os.path.join(WEIGHTS, "config.json")) as f:
        config = json.load(f)
    degree_dict = torch.load(os.path.join(WEIGHTS, "degree.pt"), map_location=DEVICE)
    p = config["params"]
    model = net(
        degree_dict["ligand_deg"], degree_dict["protein_deg"],
        mol_in_channels=p["mol_in_channels"], prot_in_channels=p["prot_in_channels"],
        prot_evo_channels=p["prot_evo_channels"], hidden_channels=p["hidden_channels"],
        pre_layers=p["pre_layers"], post_layers=p["post_layers"],
        aggregators=p["aggregators"], scalers=p["scalers"],
        total_layer=p["total_layer"], K=p["K"], heads=p["heads"],
        dropout=p["dropout"], dropout_attn_score=p["dropout_attn_score"],
        regression_head=config["tasks"]["regression_task"],
        classification_head=config["tasks"]["classification_task"],
        multiclassification_head=config["tasks"]["mclassification_task"],
        device=DEVICE,
    ).to(DEVICE)
    model.reset_parameters()
    model.load_state_dict(torch.load(os.path.join(WEIGHTS, "model.pt"), map_location=DEVICE))
    t_model = time.perf_counter() - t0
    print(f"  model loaded in {t_model:.1f} s\n")

    # ---- the one-off cost: ESM-2 embedding + contact map for the target ----
    print("Encoding the protein (ESM-2 650M; downloads ~2.5 GB the first time) ...")
    t0 = time.perf_counter()
    protein_dict = protein_init([sequence])
    t_protein = time.perf_counter() - t0
    print(f"  protein encoded in {t_protein:.1f} s\n")

    # ---- the per-compound cost ----
    names = [n for n, _, _ in COMPOUNDS]
    smiles = [s for _, s, _ in COMPOUNDS]
    groups = [g for _, _, g in COMPOUNDS]
    print(f"Encoding {len(smiles)} ligands ...")
    t0 = time.perf_counter()
    ligand_dict = ligand_init(smiles)
    t_ligand = time.perf_counter() - t0
    print(f"  ligands encoded in {t_ligand:.1f} s\n")

    screen_df = pd.DataFrame({"Protein": sequence, "Ligand": smiles, "ID": names,
                              "Group": groups})
    dropped = screen_df[~screen_df["Ligand"].isin(ligand_dict)]["ID"].tolist()
    if dropped:
        print(f"  WARNING: RDKit rejected {dropped}")
    screen_df = screen_df[screen_df["Ligand"].isin(ligand_dict)].reset_index(drop=True)

    dataset = ProteinMoleculeDataset(screen_df, ligand_dict, protein_dict, device=DEVICE)
    loader = DataLoader(dataset, batch_size=4, shuffle=False,
                        follow_batch=["mol_x", "clique_x", "prot_node_aa"])

    print("Scoring ...")
    t0 = time.perf_counter()
    result = virtual_screening(
        screen_df, model, loader,
        result_path=os.path.join(WORK, "psichic_interpretation"),
        save_interpret=False, ligand_dict=ligand_dict, device=DEVICE,
    )
    t_score = time.perf_counter() - t0

    out = os.path.join(WORK, "psichic_cpabc1_scores.csv")
    result.to_csv(out, index=False)

    # Molecular weight and cLogP, so the size/lipophilicity confound can be tested
    # rather than argued about.
    from rdkit import Chem
    from rdkit.Chem import Crippen, Descriptors
    mols = [Chem.MolFromSmiles(x) for x in result["Ligand"]]
    result["MW"] = [round(Descriptors.MolWt(m), 1) for m in mols]
    result["cLogP"] = [round(Crippen.MolLogP(m), 2) for m in mols]

    affinity = "predicted_binding_affinity"
    result[affinity] = result[affinity].astype(float)
    result = result.sort_values(affinity, ascending=False)

    print("\n" + "=" * 88)
    print("CpABC1: silymarin family vs reference P-gp inhibitors vs size-matched decoys")
    print("=" * 88)
    cols = ["ID", "Group", "MW", "cLogP", affinity, "predicted_nonbinder"]
    print(result[cols].to_string(index=False))

    print("\n-- mean predicted affinity by group " + "-" * 51)
    print(result.groupby("Group")[affinity].agg(["mean", "min", "max", "count"])
          .sort_values("mean", ascending=False).round(3).to_string())

    # If affinity tracks MW or cLogP across all compounds, the ranking is measuring bulk.
    from scipy.stats import pearsonr, spearmanr
    print("\n-- is the score just tracking size or greasiness? " + "-" * 37)
    for prop in ("MW", "cLogP"):
        r, pr = pearsonr(result[prop], result[affinity])
        rho, ps = spearmanr(result[prop], result[affinity])
        print(f"  {affinity} vs {prop:6s}: Pearson r = {r:+.3f} (p={pr:.4f})   "
              f"Spearman rho = {rho:+.3f} (p={ps:.4f})")
    print("=" * 88)
    n = len(result)
    print(f"model load      {t_model:7.1f} s")
    print(f"protein setup   {t_protein:7.1f} s   (once per target, {len(sequence)} residues)")
    print(f"ligand encode   {t_ligand:7.1f} s   ({t_ligand / n:.2f} s/ligand)")
    print(f"scoring         {t_score:7.1f} s   ({t_score / n:.2f} s/ligand)")
    print(f"MARGINAL COST   {(t_ligand + t_score) / n:7.2f} s per SMILES "
          f"once the protein is encoded")
    print(f"peak memory     {peak_gb():7.1f} GB")
    print(f"\nwrote {os.path.relpath(out, REPO)}")


if __name__ == "__main__":
    main()
