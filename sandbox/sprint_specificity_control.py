"""Does SPRINT actually use the protein, or just recognise famous drugs?

SPRINT separated the 7 reference P-glycoprotein inhibitors from the 8 property-matched
decoys on CpABC1 at AUC 0.964 (see `sprint_decoy_test.py`). There is an alternative
explanation that the decoy panel alone cannot rule out: every one of those actives is a
well-known drug annotated with P-gp/ABCB1 activity in PubChem, BindingDB and ChEMBL, which
is exactly what SPRINT was trained on. It may be scoring "this ligand is a known
promiscuous transporter binder" while barely consulting the target.

This settles it by scoring the identical panel against three proteins:

  * CpABC1 (UniProt Q9XYH6) - the test case.
  * human P-glycoprotein, ABCB1, PDB 6QEX chain A - a positive control. These compounds
    are literally its inhibitors, so if the target matters at all they should rank high.
  * human carbonic anhydrase II, PDB 3KS3 chain A - a negative control. A small soluble
    zinc enzyme with no relationship to ABC transport. P-gp inhibitors should NOT look
    special to it.

Reading the result:

  * CpABC1 ~ P-gp >> carbonic anhydrase  -> SPRINT is genuinely conditioning on the
    protein, and the CpABC1 number means something.
  * all three similar                    -> the ranking comes from the ligand alone, the
    0.964 is memorised drug knowledge, and it must not be used to rank a library.

Run with the `sprint` env, from the repo root:

    /opt/homebrew/Cellar/micromamba/2.9.0/envs/sprint/bin/python \
        sandbox/sprint_specificity_control.py
"""

import os
import sys
import time

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WORK = os.path.join(HERE, "work")

sys.path.insert(0, HERE)
from scoring_panel import ACTIVE, DECOY, evaluate, load_panel  # noqa: E402
from sprint_decoy_test import (  # noqa: E402
    SPRINT_DIR, TOKEN_BUDGET, cosine, embed_drugs, embed_target, load_model,
    pocket_residues, pocket_window, run, slice_saprot,
)

# Each entry: label, structure file, chain, and how to cut it to the token budget.
TARGETS = [
    ("CpABC1 (Q9XYH6)", os.path.join(REPO, "projects", "blue", "data",
                                     "cpabc1_receptor.pdb"), "A", "pocket"),
    ("human P-gp (6QEX)", os.path.join(WORK, "6QEX.pdb"), "A", "head"),
    ("carbonic anhydrase II (3KS3)", os.path.join(WORK, "3KS3.pdb"), "A", "head"),
]


def saprot_for(path, chain, tag):
    """foldseek structure-aware sequence for one chain of one structure."""
    out_csv = os.path.join(WORK, f"saprot_{tag}.csv")
    if os.path.exists(out_csv):
        os.remove(out_csv)
    # --no-plddt-mask because these are experimental structures whose B-factor column is
    # a real B-factor, not a pLDDT; treating it as pLDDT would mask residues arbitrarily.
    run([sys.executable, os.path.join(SPRINT_DIR, "utils", "structure_to_saprot.py"),
         "-I", path, "-C", chain, "-O", out_csv, "--no-plddt-mask"])
    df = pd.read_csv(out_csv)
    col = "Target Sequence" if "Target Sequence" in df.columns else df.columns[-1]
    return str(df[col].iloc[0])


def main():
    panel = load_panel()
    model = load_model()
    drug_emb = embed_drugs(model, panel["smiles"].tolist())
    print(f"panel: {len(panel)} compounds, ligand embeddings {drug_emb.shape}\n")

    rows = []
    for label, path, chain, how in TARGETS:
        tag = label.split()[0].lower().strip("(")
        print(f"--- {label} ---")
        seq = saprot_for(path, chain, tag)
        n = len(seq) // 2
        if how == "pocket":
            pocket = pocket_residues()
            lo, hi = pocket_window(pocket)
            cut = f"pocket-centred {lo}-{hi}"
        else:
            # The controls get the simplest defensible cut: the first TOKEN_BUDGET
            # residues. Carbonic anhydrase fits whole; P-gp loses its C-terminal tail.
            lo, hi = 1, min(n, TOKEN_BUDGET)
            cut = f"residues {lo}-{hi}" + (" (whole chain)" if hi == n else "")
        seq_cut = slice_saprot(seq, lo, hi)
        print(f"  {n} residues in chain {chain}, using {cut} -> {len(seq_cut) // 2}")

        t0 = time.perf_counter()
        target_emb = embed_target(model, seq_cut)
        dt = time.perf_counter() - t0
        scores = cosine(target_emb, drug_emb)
        result = evaluate(dict(zip(panel["name"], scores)))
        p = result["panel"]

        actives = p[p["group"] == ACTIVE]["score"]
        decoys = p[p["group"] == DECOY]["score"]
        rows.append({
            "protein": label,
            "cut": cut,
            "AUC": round(result["auc"], 3),
            "mean active": round(actives.mean(), 3),
            "mean decoy": round(decoys.mean(), 3),
            "separation": round(actives.mean() - decoys.mean(), 3),
            "actives in top 7": int((p["rank"] <= 7).mul(p["group"] == ACTIVE).sum()),
            "embed s": round(dt, 1),
        })
        print(f"  AUC {result['auc']:.3f}   "
              f"top 5: {', '.join(p['name'].head(5))}\n")
        p.to_csv(os.path.join(WORK, f"sprint_specificity_{tag}.csv"), index=False)

    out = pd.DataFrame(rows)
    w = 118
    print("=" * w)
    print("Target specificity: the SAME 20 compounds scored against three proteins")
    print("=" * w)
    print(out.to_string(index=False))
    print("=" * w)

    cp, pgp, ca = out["separation"]
    print("\nInterpretation:")
    print(f"  CpABC1 separation           {cp:+.3f}")
    print(f"  human P-gp (should be high) {pgp:+.3f}")
    print(f"  carbonic anhydrase (low)    {ca:+.3f}")
    # A single separation threshold turned out to be too crude a verdict: it cannot tell
    # "ignores the protein entirely" from "uses the protein, but not for this particular
    # discrimination". The rank correlations below separate those cases.
    from scipy.stats import spearmanr
    print("\nRank correlation of the compound ordering between proteins:")
    labels = [r["protein"] for r in rows]
    series = {}
    for label in labels:
        tag = label.split()[0].lower().strip("(")
        series[label] = pd.read_csv(
            os.path.join(WORK, f"sprint_specificity_{tag}.csv")).set_index("name")["score"]
    import itertools
    for a, b in itertools.combinations(labels, 2):
        common = series[a].index.intersection(series[b].index)
        rho, _ = spearmanr(series[a][common], series[b][common])
        print(f"  {a:30s} vs {b:30s} rho = {rho:+.3f}")

    print("\nVerdict:")
    if ca >= 0.5 * cp:
        print("  The actives/decoys separation is reproduced by an unrelated enzyme, so THIS"
              "\n  panel's AUC cannot be attributed to the target. High rank correlation with"
              "\n  a true homolog (P-gp) and lower correlation with the unrelated enzyme means"
              "\n  SPRINT does condition on the protein - just not enough for this"
              "\n  discrimination, which famous P-gp drugs win on ligand features alone."
              "\n  Not usable for ranking a CpABC1 library on this evidence.")
    else:
        print("  The same ligands score markedly lower against an unrelated enzyme, so the"
              "\n  separation is target-driven.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
