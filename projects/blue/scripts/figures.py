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

import pandas as pd
import stylia

from . import chemspace

# Where each stage of the funnel comes from. Only files committed to the repository are
# listed: `outputs/` and `data/downloads/` are git-ignored, so in Colab they do not exist.
HITS = "data/pharmit_hits_molport.csv"
COORDINATES = "data/eos1klk_pharmit_hits.csv"
CYTOTOXICITY = "data/eos42ez_sand_hits.csv"
SEED = "data/eos1klk_silymarin.csv"

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
