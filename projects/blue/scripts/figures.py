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

from rdkit import Chem

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


# Silymarin in 3D: the pose docked into the CpABC1 pocket, so the overlays below compare
# against the form the molecule actually binds in rather than an idealised one.
OVERLAY_REFERENCE = "data/silymarin_ligand.sdf"


def _positions(molecule, conformer):
    """Return the 3D coordinates of every atom of one conformer, as an array."""
    geometry = molecule.GetConformer(conformer)
    return np.array([list(geometry.GetAtomPosition(i)) for i in range(molecule.GetNumAtoms())])


def _bonds(molecule):
    """Return each bond as the pair of atoms it joins."""
    return [(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()) for bond in molecule.GetBonds()]


def build_overlays(how_many=4):
    """Lay the best-scoring shortlisted molecules over silymarin in 3D.

    For each one, `shape.overlay_on` builds the shapes it can fold into, fits each over
    silymarin, and keeps the best. That is the real 3D comparison SAND only predicts, so
    each entry carries both numbers: SAND's score and the overlap actually achieved.

    The pair of molecules is then flattened for drawing, onto the plane they jointly spread
    out in most, which is the view that shows the most of the overlap. Coordinates are
    centred on the pair, in angstroms.

    This is the slow step, a second or two per molecule.
    """
    reference = Chem.MolFromMolFile(OVERLAY_REFERENCE)
    scored = pd.read_csv(SHAPE)
    shortlisted = set(pd.read_csv(CYTOTOXICITY)["input"])
    best = scored[scored["smiles"].isin(shortlisted)].nlargest(how_many, "shape")

    seed_positions = _positions(reference, 0)
    entries = []
    for row in best.itertuples():
        molecule, conformer, overlap = shape.overlay_on(row.smiles, reference)
        hit_positions = _positions(molecule, conformer)

        both = np.vstack([seed_positions, hit_positions])
        centre = both.mean(axis=0)
        plane = np.linalg.svd(both - centre)[2][:2].T  # the two directions they spread in most
        entries.append({
            "molport_id": row.molport_id, "sand": row.shape, "overlap": overlap,
            "seed_xy": (seed_positions - centre) @ plane,
            "hit_xy": (hit_positions - centre) @ plane,
            "seed_bonds": _bonds(reference), "hit_bonds": _bonds(molecule),
        })
    return entries


def overlay_extent(entries):
    """Return the half-width and half-height that fit every overlay, so panels share a scale.

    Without this each panel is scaled to its own molecule, and a small molecule is drawn just
    as large as a big one, which makes the sizes impossible to compare. The two directions are
    measured separately, because a molecule laid out flat is much wider than it is tall and a
    square frame would be mostly empty. The panels stay undistorted either way.
    """
    corners = np.vstack([np.vstack([e["seed_xy"], e["hit_xy"]]) for e in entries])
    return tuple(np.abs(corners).max(axis=0) * 1.08)


def plot_overlay(ax, entry, extent, legend=False):
    """Draw one molecule laid over silymarin, silymarin in grey behind it."""
    nc = stylia.NamedColors()
    for xy, bonds, color, width, z, name in (
        (entry["seed_xy"], entry["seed_bonds"], nc.silver, 4.0, 1, "silymarin"),
        (entry["hit_xy"], entry["hit_bonds"], nc.turquoise, 2.6, 2, "hit"),
    ):
        for first, second in bonds:
            ax.plot(xy[[first, second], 0], xy[[first, second], 1], color=color,
                    linewidth=width, solid_capstyle="round", zorder=z, label=name)
            name = None  # only the first bond of each molecule goes in the legend

    half_width, half_height = extent
    ax.set_xlim(-half_width, half_width)
    ax.set_ylim(-half_height, half_height)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title(f"{entry['molport_id']}\nSAND {entry['sand']:.2f} · "
                 f"real overlap {entry['overlap']:.2f}", fontsize=9)
    if legend:
        ax.legend(fontsize=7, frameon=False, loc="lower left")
