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
from rdkit.Chem import AllChem, Draw, rdFingerprintGenerator, rdMolAlign, rdShapeHelpers

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


def view_overlay(reference, molecule, conformer, width=260, height=220):
    """Show one molecule laid over the reference, the reference in grey."""
    import py3Dmol

    view = py3Dmol.view(width=width, height=height)
    view.addModel(Chem.MolToMolBlock(reference), "sdf")
    view.setStyle({"model": 0}, {"stick": {"colorscheme": "greyCarbon", "radius": 0.12}})
    view.addModel(Chem.MolToMolBlock(molecule, confId=conformer), "sdf")
    view.setStyle({"model": 1}, {"stick": {"colorscheme": "cyanCarbon", "radius": 0.12}})
    view.zoomTo()
    return view


def draw_molecules(smiles_list, legends, per_row=4, size=(260, 220)):
    """Draw molecules in a grid, with a caption under each one."""
    molecules = [Chem.MolFromSmiles(s) for s in smiles_list]
    return Draw.MolsToGridImage(molecules, molsPerRow=per_row, subImgSize=size,
                                legends=legends)
