"""Helper functions for the blue group's shape similarity notebook.

The embeddings the notebook compares come from the Ersilia model `eos5mnx` (SAND), which
turns a molecule into 512 numbers describing its 3D shape. The vectors are already
L2-normalised, so the cosine similarity between two molecules is a plain dot product.

This module loads those files, measures similarity in two ways (shape and 2D
fingerprints), builds the background distributions the notebook compares against, and
keeps the repetitive parts of the plots out of the notebook cells.
"""

import numpy as np
import pandas as pd
import stylia
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import (QED, AllChem, Draw, rdFingerprintGenerator, rdMolAlign,
                        rdShapeHelpers)
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams

from .chemspace import DESCRIPTORS

# RDKit prints a warning for every molecule it cannot read. We count them instead.
RDLogger.DisableLog("rdApp.*")

# ECFP4 in RDKit's own words: circular fingerprints of radius 2, folded to 2048 bits.
_FINGERPRINTS = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def load_embeddings(path):
    """Read an eos5mnx output file into a SMILES list and a matrix of 512 numbers.

    The model writes one row per molecule, with the molecule in an `input` column and
    the embedding in `feat_000` to `feat_511`. The matrix is read as float32, which
    halves the memory the hits file needs.
    """
    frame = pd.read_csv(path)
    vectors = frame.filter(like="feat_").values.astype("float32")
    return frame["input"].tolist(), vectors


def check_normalised(vectors):
    """Return the length of the vectors, which should be 1 for cosine to be a dot product."""
    return np.linalg.norm(vectors, axis=1)


def _unit(vectors):
    """Return the vectors scaled to length 1, which is what makes a dot product a cosine."""
    lengths = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors / np.where(lengths == 0, 1, lengths)


def shape_similarity(vectors, seed_vector):
    """Return the cosine similarity of every molecule to the seed.

    The model already returns vectors of length 1, but we divide by the lengths anyway so
    that this is a cosine whatever comes in.
    """
    return _unit(vectors) @ _unit(seed_vector)


def shape_background(vectors, sample=4000, seed=42):
    """Return the cosine similarity of random pairs of molecules, for comparison.

    A similarity is only meaningful next to the similarities you would get anyway. This
    takes a random sample of the molecules and returns every pair within it.
    """
    rng = np.random.default_rng(seed)
    picked = _unit(vectors[rng.choice(len(vectors), min(sample, len(vectors)), replace=False)])
    pairs = picked @ picked.T
    return pairs[np.triu_indices(len(picked), k=1)]


def fingerprints(smiles_list):
    """Return one Morgan fingerprint per molecule."""
    return [_FINGERPRINTS.GetFingerprint(Chem.MolFromSmiles(s)) for s in smiles_list]


def tanimoto_similarity(fps, seed_fp):
    """Return the Tanimoto similarity of every fingerprint to the seed."""
    return np.array(DataStructs.BulkTanimotoSimilarity(seed_fp, fps))


def tanimoto_background(fps, sample=2000, seed=42):
    """Return the Tanimoto similarity of random pairs, the 2D version of the background."""
    rng = np.random.default_rng(seed)
    picked = [fps[i] for i in rng.choice(len(fps), min(sample, len(fps)), replace=False)]
    values = []
    for position, one in enumerate(picked[:-1]):
        values.extend(DataStructs.BulkTanimotoSimilarity(one, picked[position + 1:]))
    return np.array(values)


def drug_likeness(smiles_list):
    """Return the QED of every molecule, a single number for how drug-like it looks.

    QED runs from 0 to 1 and combines the properties in `DESCRIPTORS` with a few others,
    each scored against the range seen in approved oral drugs. It is a rough guide, not a
    verdict: plenty of real drugs, silymarin among them, score in the middle.
    """
    return np.array([QED.qed(Chem.MolFromSmiles(text)) for text in smiles_list])


def pains_alerts(smiles_list):
    """Return True for molecules containing a PAINS substructure.

    PAINS are pieces that turn up as hits against many unrelated proteins, usually
    because they interfere with the assay rather than bind anything. This uses RDKit's
    PAINS_A catalogue, the smallest and most confident of the three, so a True here is
    worth taking seriously. It is a reason to check a molecule, not to trust or reject it.
    """
    parameters = FilterCatalogParams()
    parameters.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_A)
    catalogue = FilterCatalog(parameters)
    return np.array([catalogue.HasMatch(Chem.MolFromSmiles(text)) for text in smiles_list])


def percentile_of(value, background):
    """Return where a similarity would sit in the background, as a percentage."""
    return float((background < value).mean() * 100)


def plot_distribution(ax, to_seed, background, xlabel, title=None):
    """Draw the similarities to the seed against the background of random pairs."""
    colors = stylia.NamedColors()
    edges = np.linspace(min(to_seed.min(), background.min()),
                        max(to_seed.max(), background.max()), 60)
    ax.hist(background, bins=edges, density=True, color=colors.silver,
            alpha=0.7, label="random pairs of hits")
    ax.hist(to_seed, bins=edges, density=True, color=colors.cobalt,
            alpha=0.7, label="hits vs silymarin")
    ax.axvline(to_seed.max(), color=colors.crimson, linewidth=1.2, label="closest hit")
    ax.legend(fontsize=6, frameon=False)
    stylia.label(ax, xlabel=xlabel, ylabel="Density", title=title)


def plot_agreement(ax, shape, tanimoto, title=None):
    """Draw shape similarity against 2D similarity, one point per molecule."""
    colors = stylia.NamedColors()
    ax.scatter(tanimoto, shape, s=2, alpha=0.15, color=colors.cobalt, linewidths=0)
    stylia.label(ax, xlabel="Tanimoto similarity (2D)",
                 ylabel="Shape similarity (SAND)", title=title)


def overlay_on(smiles, reference, conformers=20, seed=42):
    """Build 3D forms of a molecule and lay the best-fitting one over the reference.

    SAND predicts how well two molecules would overlap without ever building them in 3D.
    This does the real thing, so its prediction can be checked: generate conformers (the
    shapes the molecule can fold into), lay each over the reference with Open3DAlign, and
    keep whichever fits best.

    Returns the aligned molecule, the id of the best conformer, and the shape Tanimoto
    similarity, which runs from 0 to 1.
    """
    molecule = Chem.AddHs(Chem.MolFromSmiles(smiles))
    parameters = AllChem.ETKDGv3()
    parameters.randomSeed = seed
    AllChem.EmbedMultipleConfs(molecule, numConfs=conformers, params=parameters)
    AllChem.MMFFOptimizeMoleculeConfs(molecule)
    molecule = Chem.RemoveHs(molecule)

    best = (-1.0, None)
    for conformer in range(molecule.GetNumConformers()):
        rdMolAlign.GetCrippenO3A(molecule, reference, prbCid=conformer).Align()
        similarity = 1 - rdShapeHelpers.ShapeTanimotoDist(molecule, reference, confId1=conformer)
        best = max(best, (similarity, conformer))
    return molecule, best[1], best[0]


def _add_overlay(view, reference, molecule, conformer, **cell):
    """Add the reference (grey) and one aligned molecule (blue) to a py3Dmol view.

    `cell` is empty for a single view, or `viewer=(row, column)` for one cell of a grid.
    """
    view.addModel(Chem.MolToMolBlock(reference), "sdf", **cell)
    view.setStyle({"model": 0}, {"stick": {"colorscheme": "greyCarbon", "radius": 0.12}}, **cell)
    view.addModel(Chem.MolToMolBlock(molecule, confId=conformer), "sdf", **cell)
    view.setStyle({"model": 1}, {"stick": {"colorscheme": "cyanCarbon", "radius": 0.12}}, **cell)
    view.zoomTo(**cell)


def view_overlay(reference, molecule, conformer, width=260, height=220):
    """Show one molecule laid over the reference, the reference in grey."""
    import py3Dmol

    view = py3Dmol.view(width=width, height=height)
    _add_overlay(view, reference, molecule, conformer)
    return view


def view_overlay_grid(reference, entries, per_row=4, size=(220, 200)):
    """Show several molecules laid over the reference, one per cell of a grid.

    `entries` are dictionaries with the `molecule` and `conformer` that `overlay_on`
    returns, and a `caption` to write in the corner of the cell.
    """
    import py3Dmol

    rows = -(-len(entries) // per_row)
    view = py3Dmol.view(width=size[0] * per_row, height=size[1] * rows,
                        viewergrid=(rows, per_row), linked=False)
    for position, entry in enumerate(entries):
        cell = {"viewer": (position // per_row, position % per_row)}
        _add_overlay(view, reference, entry["molecule"], entry["conformer"], **cell)
        view.addLabel(entry["caption"], {"fontSize": 10, "fontColor": "black",
                                         "backgroundOpacity": 0, "useScreen": True,
                                         "position": {"x": 5, "y": 5}}, **cell)
    return view


def plot_cutoff(ax, scores, cutoff, xlabel="Shape similarity to silymarin"):
    """Draw every score, with the ones kept above the cutoff in a second colour."""
    colors = stylia.NamedColors()
    edges = np.linspace(scores.min(), scores.max(), 60)
    ax.hist(scores[scores < cutoff], bins=edges, color=colors.silver, label="left out")
    ax.hist(scores[scores >= cutoff], bins=edges, color=colors.cobalt, label="kept")
    ax.axvline(cutoff, color=colors.crimson, linewidth=1.2, label=f"cutoff {cutoff:.3f}")
    ax.legend(fontsize=6, frameon=False)
    stylia.label(ax, xlabel=xlabel, ylabel="Number of hits")


def plot_filters(axes, values, limits, kept):
    """Draw one panel per property, with the molecules the rules remove in grey.

    `values` is a table with one column per property, `limits` gives the lines to draw
    under the same names, and `kept` is the boolean mask of the molecules that pass
    every rule.
    """
    colors = stylia.NamedColors()
    for name, (title, lines) in limits.items():
        ax = axes.next()
        column = values[name]
        edges = np.linspace(column.quantile(0.002), column.quantile(0.998), 40)
        ax.hist(column[~kept], bins=edges, color=colors.silver, label="removed")
        ax.hist(column[kept], bins=edges, color=colors.cobalt, label="kept")
        for line in lines:
            ax.axvline(line, color=colors.crimson, linewidth=1.2)
        ax.legend(fontsize=6, frameon=False)
        stylia.label(ax, xlabel=title, ylabel="Number of hits")


def plot_properties(axes, top, rest, seed):
    """Draw one panel per property: the kept hits against the rest, silymarin as a line.

    `top`, `rest` and `seed` are tables with one column per property in `DESCRIPTORS`,
    as `chemspace.describe` returns them.
    """
    colors = stylia.NamedColors()
    for position, (name, (title, _)) in enumerate(DESCRIPTORS.items()):
        ax = axes.next()
        both = pd.concat([top[name], rest[name]]).dropna()
        low, high = both.quantile(0.005), both.quantile(0.995)
        edges = np.linspace(low, high, 30)
        if name in ("hbd", "hba", "rotatable_bonds"):
            edges = np.arange(low, high + 2) - 0.5
        ax.hist(rest[name], bins=edges, density=True, color=colors.silver,
                alpha=0.7, label="rest")
        ax.hist(top[name], bins=edges, density=True, color=colors.cobalt,
                alpha=0.7, label="top hits")
        ax.axvline(seed[name].iloc[0], color=colors.crimson, linewidth=1.2, label="silymarin")
        stylia.label(ax, xlabel=title, ylabel="Density")
        if position == 0:
            ax.legend(fontsize=6, frameon=False)


def draw_molecules(smiles_list, legends, per_row=4, size=(260, 220)):
    """Draw molecules in a grid, with a caption under each one."""
    molecules = [Chem.MolFromSmiles(s) for s in smiles_list]
    return Draw.MolsToGridImage(molecules, molsPerRow=per_row, subImgSize=size,
                                legends=legends)
