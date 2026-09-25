"""The CpABC1 decoy panel, and the pass criterion any scoring tool has to meet.

Why this exists: PSICHIC was tried against CpABC1 first with only two groups, the blue
group's silymarin flavonoids and three reference P-glycoprotein inhibitors. The inhibitors
ranked above the flavonoids and it looked like a clean success. It was not. Adding decoys
with no ABC-transporter pharmacology put trilaurin, a triglyceride, top of all fourteen
compounds. Any ranking where the actives happen to be bigger than the compounds of interest
will look like success, so the decoys are what make the test mean anything.

The criterion below is fixed in advance, deliberately, so that a tool's result is not
argued about after the fact.

Panel: `cpabc1_decoy_panel.csv`, three groups.

  * `reference P-gp inhibitor` (7) - established inhibitors of human P-glycoprotein
    (ABCB1), the best-studied relative of CpABC1. These are proxy actives: nobody has
    shown any of them inhibits CpABC1, so they test family plausibility, not ground truth.
    quinidine is included precisely because it is small (324 Da), so a tool that only
    rewards bulk cannot score it highly.
  * `size-matched decoy` (8) - no ABC-transporter pharmacology, chosen to bracket the
    inhibitors on both molecular weight (473-1449 vs 324-1203) and lipophilicity
    (cLogP -7.6 to 14.0 vs 3.2 to 6.4). Sucrose diacetate hexaisobutyrate is the sharpest
    of them: a food additive whose cLogP of 3.0 sits inside the inhibitors' own band.
  * `silymarin family` (5) - what the blue group actually cares about. Not used to score
    the tool, except for silybin, the one compound with measured CpABC1 activity.

Known gap, stated rather than hidden: no decoy lands in the MW 500-650 / cLogP 4-6 corner,
which is where elacridar and zosuquidar sit. Non-pharmacological chemistry is scarce there,
because that region is drug-like space and drug-like space is full of pharmacology.

Usage from a tool script:

    from scoring_panel import load_panel, evaluate, report
    panel = load_panel()
    scores = {name: my_tool_score(smiles) for name, smiles in
              zip(panel["name"], panel["smiles"])}
    report("SPRINT", evaluate(scores))
"""

import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PANEL_CSV = os.path.join(HERE, "cpabc1_decoy_panel.csv")

ACTIVE = "reference P-gp inhibitor"
DECOY = "size-matched decoy"
FAMILY = "silymarin family"

# A tool must clear this to be worth carrying forward on CpABC1.
MIN_AUC = 0.80
# Trilaurin and cholesteryl oleate are near-identical by bulk properties (MW 639 vs 651,
# cLogP 11.8 vs 14.0). A tool that separates them widely is not measuring anything
# physical. Expressed as a fraction of the panel's own score range, so it works whatever
# scale the tool reports on.
MAX_TWIN_GAP_FRAC = 0.10
TWINS = ("trilaurin", "cholesteryl oleate")


def load_panel():
    """The panel with RDKit molecular weight and cLogP added."""
    from rdkit import Chem
    from rdkit.Chem import Crippen, Descriptors

    panel = pd.read_csv(PANEL_CSV)
    mols = [Chem.MolFromSmiles(s) for s in panel["smiles"]]
    missing = [n for n, m in zip(panel["name"], mols) if m is None]
    if missing:
        raise ValueError(f"RDKit could not parse: {missing}")
    panel["MW"] = [round(Descriptors.MolWt(m), 1) for m in mols]
    panel["cLogP"] = [round(Crippen.MolLogP(m), 2) for m in mols]
    return panel


def evaluate(scores, higher_is_better=True):
    """Score a tool against the panel. `scores` maps compound name to a number.

    Compounds the tool could not score are dropped and counted, so a tool that silently
    fails on, say, the macrocycles does not get credit for the ones it managed.
    """
    from scipy.stats import pearsonr, spearmanr
    from sklearn.metrics import roc_auc_score

    panel = load_panel()
    panel["score"] = panel["name"].map(scores).astype(float)
    dropped = panel[panel["score"].isna()]["name"].tolist()
    panel = panel.dropna(subset=["score"]).reset_index(drop=True)
    if not higher_is_better:
        panel["score"] = -panel["score"]

    panel = panel.sort_values("score", ascending=False).reset_index(drop=True)
    panel["rank"] = panel.index + 1

    ranked = panel[panel["group"].isin([ACTIVE, DECOY])]
    labels = (ranked["group"] == ACTIVE).astype(int)
    auc = (roc_auc_score(labels, ranked["score"])
           if labels.nunique() == 2 else float("nan"))

    lo, hi = panel["score"].min(), panel["score"].max()
    span = hi - lo
    twins = panel[panel["name"].isin(TWINS)]
    twin_gap = (abs(twins["score"].iloc[0] - twins["score"].iloc[1])
                if len(twins) == 2 else float("nan"))

    decoy_median_rank = panel[panel["group"] == DECOY]["rank"].median()
    silybin = panel[panel["name"] == "silybin"]
    trilaurin = panel[panel["name"] == "trilaurin"]

    checks = {
        f"AUC actives vs decoys >= {MIN_AUC}": auc >= MIN_AUC,
        "trilaurin outside the top 3": (trilaurin["rank"].iloc[0] > 3
                                        if len(trilaurin) else None),
        f"trilaurin/cholesteryl-oleate gap <= {MAX_TWIN_GAP_FRAC:.0%} of range":
            (twin_gap <= MAX_TWIN_GAP_FRAC * span if span > 0 else False),
        "silybin above the decoy median rank": (silybin["rank"].iloc[0] < decoy_median_rank
                                                if len(silybin) else None),
        "scores are not all identical": span > 0,
    }

    diagnostics = {}
    for prop in ("MW", "cLogP"):
        r, pr = pearsonr(panel[prop], panel["score"])
        rho, ps = spearmanr(panel[prop], panel["score"])
        diagnostics[prop] = (r, pr, rho, ps)

    return {
        "panel": panel,
        "auc": auc,
        "twin_gap": twin_gap,
        "score_span": span,
        "decoy_median_rank": decoy_median_rank,
        "checks": checks,
        "diagnostics": diagnostics,
        "dropped": dropped,
    }


def report(tool_name, result):
    """Print the ranking, the checks and the verdict."""
    panel, checks = result["panel"], result["checks"]
    w = 92
    print("\n" + "=" * w)
    print(f"{tool_name} on CpABC1 (UniProt Q9XYH6) - decoy-controlled panel")
    print("=" * w)
    cols = ["rank", "name", "group", "MW", "cLogP", "score"]
    print(panel[cols].to_string(index=False))

    if result["dropped"]:
        print(f"\n  NOT SCORED ({len(result['dropped'])}): {result['dropped']}")

    print("\n-- group means " + "-" * (w - 16))
    print(panel.groupby("group")["score"].agg(["mean", "min", "max", "count"])
          .sort_values("mean", ascending=False).round(3).to_string())

    print("\n-- is the score just tracking size or greasiness? " + "-" * (w - 50))
    for prop, (r, pr, rho, ps) in result["diagnostics"].items():
        print(f"   score vs {prop:6s}: Pearson r = {r:+.3f} (p={pr:.4f})   "
              f"Spearman rho = {rho:+.3f} (p={ps:.4f})")

    print("\n-- pass criterion, fixed before the run " + "-" * (w - 41))
    print(f"   AUC (actives vs decoys) = {result['auc']:.3f}")
    print(f"   trilaurin/cholesteryl-oleate gap = {result['twin_gap']:.3f} "
          f"of a {result['score_span']:.3f} range")
    for name, ok in checks.items():
        mark = "n/a " if ok is None else ("PASS" if ok else "FAIL")
        print(f"   [{mark}] {name}")

    decided = [ok for ok in checks.values() if ok is not None]
    verdict = all(decided)
    print("\n" + "=" * w)
    print(f"VERDICT: {tool_name} is "
          f"{'USABLE' if verdict else 'NOT usable'} for ranking compounds against CpABC1")
    if not verdict:
        # `ok is False` would miss these: pandas comparisons give numpy.bool_, which is
        # falsy but not the False singleton.
        failed = [n for n, ok in checks.items() if ok is not None and not ok]
        print(f"         failed: {'; '.join(failed)}")
    print("=" * w)
    return verdict
