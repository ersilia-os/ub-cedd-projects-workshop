"""Figures for the blue group, drawn from the files committed in `data/`.

The notebook `blue_plots.ipynb` collects the group's figures in one place. This module
keeps the repetitive parts out of the notebook cells: reading the funnel back together,
and drawing the four sets of molecules on one map.

The funnel has three stages, each one a subset of the one before it:

    28,732  hits of the Pharmit pharmacophore screen   (blue_pharmit_hits.ipynb)
     1,887  of those that match silymarin's 3D shape   (blue_sand_shape_similarity.ipynb)
     1,000  of those that look least cytotoxic         (blue_cytotoxicity_filter.ipynb)

The map coordinates are not computed here. They come from the Ersilia model `eos1klk`,
which places a molecule on a map drawn from 1.3 million reference compounds, so every
notebook in this project draws molecules on the same map.
"""

import math

import numpy as np
import pandas as pd
import stylia

from . import chemspace, shape

# Where each stage of the funnel comes from. Only files committed to the repository are
# listed: `outputs/` and `data/downloads/` are git-ignored, so in Colab they do not exist.
HITS = "data/pharmit_hits_molport.csv"
COORDINATES = "data/eos1klk_pharmit_hits.csv"
CYTOTOXICITY = "data/eos42ez_sand_hits.csv"
SEED = "data/eos1klk_silymarin.csv"
SHAPE = "data/sand_shape_similarity.csv"
SEED_SMILES = "data/silymarin.csv"

# The cytotoxicity shortlist is rebuilt rather than read, using the same rule as
# `blue_cytotoxicity_filter.ipynb`: sort on predicted toxicity to liver cells, keep the
# lowest thousand. Change either of these and the shortlist stops matching that notebook.
KEEP = 1000
TOXICITY = "cytotoxicity_hepg2"

# How many molecules each stage should end up with. Checked on load, because a merge that
# quietly drops rows would just draw fewer points and look perfectly fine.
EXPECTED = {"space": 28732, "hits": 1887, "kept": KEEP}


def load_funnel():
    """Read the three stages of the funnel, and silymarin, with their map coordinates.

    Returns `(space, hits, kept, seed)`: every Pharmit hit, the shape hits, the shape hits
    that survived the toxicity filter, and the one row for silymarin. All four carry the
    `eos1klk` coordinate columns (`tsne_x`, `umap_x` and so on), so any of them can be
    drawn on any of the four maps.
    """
    space = chemspace.load_space(HITS, COORDINATES)
    toxicity = pd.read_csv(CYTOTOXICITY).drop(columns=["key"], errors="ignore")
    hits = space.merge(toxicity, left_on="smiles", right_on="input").drop(columns=["input"])
    kept = hits.sort_values(TOXICITY).head(KEEP).reset_index(drop=True)
    seed = pd.read_csv(SEED).drop(columns=["key"], errors="ignore")

    found = {"space": len(space), "hits": len(hits), "kept": len(kept)}
    if found != EXPECTED:
        raise ValueError(f"expected {EXPECTED} molecules but found {found}. "
                         f"Did a data file change, or did a merge on SMILES lose rows?")
    return space, hits, kept, seed


def plot_funnel(ax, space, hits, kept, seed, projection="tsne"):
    """Draw the whole funnel on one map, faintest and largest set first.

    The three sets are nested, so they are drawn on top of each other from big to small:
    a molecule kept after the toxicity filter shows as a small coloured dot inside a
    larger one. A plain large dot is a shape hit that the toxicity filter dropped.
    """
    nc = stylia.NamedColors()
    ax.scatter(*chemspace.coordinates(space, projection), color=nc.silver, s=4, alpha=0.35,
               linewidths=0, zorder=1, label=f"Pharmit hits ({len(space):,})")
    ax.scatter(*chemspace.coordinates(hits, projection), color=nc.turquoise, s=26, alpha=0.9,
               linewidths=0, zorder=2, label=f"Shape hits ({len(hits):,})")
    ax.scatter(*chemspace.coordinates(kept, projection), color=nc.fuchsia, s=9, alpha=1.0,
               linewidths=0, zorder=3, label=f"Kept on toxicity ({len(kept):,})")
    chemspace.plot_seed(ax, seed, projection, color=nc.amber)
    ax.set_box_aspect(1)  # a square panel, whatever range the coordinates cover


def add_legend(ax, loc="upper right"):
    """Add a legend whose markers are all one readable size.

    Left alone, the legend copies each set's own marker: the faint background dots come out
    too small to see a colour in, and silymarin's star comes out larger than a line of text.
    """
    legend = ax.legend(loc=loc, frameon=True, framealpha=0.9)
    for handle in legend.legend_handles:
        handle.set_alpha(1)
        handle.set_sizes([60])
    return legend


# The property filter of `blue_sand_shape_similarity.ipynb`, in the same order it applies it:
# first keep the best tenth of the shape ranking, then apply three rules of thumb to those.
# Change any of these and the shortlist stops matching that notebook.
TOP_FRACTION = 0.10
MW_RANGE = (250, 500)
MAX_LOGP = 5
MIN_QED = 0.35

# One entry per panel of the property figure: the column, the axis label, and the rule
# drawn on it as (low, high), where `None` means the rule does not close that side.
RULES = {
    "mw": ("Molecular weight", MW_RANGE),
    "logp": ("logP", (None, MAX_LOGP)),
    "qed": ("Drug-likeness (QED)", (MIN_QED, None)),
}


def load_property_filter():
    """Rebuild the property filter that turned the shape ranking into the shortlist.

    Returns `(top, seed)`. `top` is the best tenth of the shape ranking, 2,874 molecules,
    with `mw`, `logp` and `qed` computed for each and one boolean column per rule saying
    whether it passes that rule on its own. `seed` is the same properties for silymarin.

    The molecules that pass all three rules are checked against `eos42ez_sand_hits.csv`,
    the shortlist the filter notebook actually produced, so a change in RDKit or in the
    constants above shows up here as an error rather than as a quietly different figure.
    """
    scored = pd.read_csv(SHAPE)
    top = scored.nlargest(math.ceil(TOP_FRACTION * len(scored)), "shape").reset_index(drop=True)
    top = top.join(chemspace.describe(top["smiles"]))
    top["qed"] = shape.drug_likeness(top["smiles"])

    top["passes_mw"] = top["mw"].between(*MW_RANGE)
    top["passes_logp"] = top["logp"] <= MAX_LOGP
    top["passes_qed"] = top["qed"] >= MIN_QED
    top["passes"] = top["passes_mw"] & top["passes_logp"] & top["passes_qed"]

    expected = set(pd.read_csv(CYTOTOXICITY)["input"])
    if set(top.loc[top["passes"], "smiles"]) != expected:
        raise ValueError(f"the rebuilt shortlist has {int(top['passes'].sum())} molecules and does "
                         f"not match the {len(expected)} in {CYTOTOXICITY}. Have the rules or the "
                         f"property calculation changed since blue_sand_shape_similarity ran?")

    seed = chemspace.describe(pd.read_csv(SEED_SMILES)["smiles"])
    seed["qed"] = shape.drug_likeness(pd.read_csv(SEED_SMILES)["smiles"])
    return top, seed


def plot_rule(ax, top, seed, column):
    """Draw one property, coloured by the one rule that applies to it.

    Every panel of the property figure asks a single question, so a molecule is coloured
    here by whether it passes *this* rule, not by whether it survives all three. That keeps
    the boundary honest: everything on the kept side of the line is drawn as kept. A
    molecule can pass here and still be dropped by one of the other two panels.
    """
    nc = stylia.NamedColors()
    title, (low, high) = RULES[column]
    values = top[column]
    passes = top[f"passes_{column}"]

    edges = np.linspace(values.quantile(0.002), values.quantile(0.998), 45)
    ax.hist(values[~passes], bins=edges, color=nc.silver, label=f"removed ({int((~passes).sum()):,})")
    ax.hist(values[passes], bins=edges, color=nc.turquoise, label=f"kept ({int(passes.sum()):,})")
    for edge in (low, high):
        if edge is not None:
            ax.axvline(edge, color=nc.crimson, linewidth=1.4, linestyle="--")
    ax.axvline(seed[column].iloc[0], color=nc.amber, linewidth=1.6, label="silymarin")
    ax.legend(fontsize=7, frameon=False)
    stylia.label(ax, xlabel=title, ylabel="Number of hits", title=rule_text(column))


def rule_text(column):
    """Write a rule out the way it reads in the filter notebook, e.g. `250 to 500`."""
    low, high = RULES[column][1]
    if low is not None and high is not None:
        return f"keep {low} to {high}"
    return f"keep {high} or less" if low is None else f"keep {low} or more"
