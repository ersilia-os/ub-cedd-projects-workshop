"""Helper functions for the yellow group's chemical space notebook.

The coordinates the notebook plots come from the Ersilia model `eos1klk`, which places
a molecule on a map drawn from 1.3 million reference compounds. This module joins those
coordinates to the curated activity table, works out scaffolds and substructures, and
keeps the repetitive parts of the plots out of the notebook cells.
"""

import numpy as np
import pandas as pd
import stylia
from rdkit import Chem, RDLogger
from rdkit.Chem import Draw
from rdkit.Chem.Scaffolds import MurckoScaffold

# RDKit prints a warning for every molecule it cannot read. We count them instead.
RDLogger.DisableLog("rdApp.*")

# The four maps eos1klk returns, and the name to write on a plot.
PROJECTIONS = {"pca": "PCA", "tsne": "t-SNE", "umap": "UMAP", "tmap": "TMAP"}


def load_space(curated_path, projection_path):
    """Join a curated activity table and an eos1klk output file, molecule by molecule.

    eos1klk writes one row per input molecule, with the molecule in an `input` column
    and its coordinates in `pca_x`, `pca_y`, `tsne_x` and so on. Rows are matched on
    the SMILES, so the two files do not have to be in the same order.
    """
    curated = pd.read_csv(curated_path)
    projection = pd.read_csv(projection_path).drop(columns=["key"], errors="ignore")
    frame = curated.merge(projection, left_on="smiles", right_on="input", how="inner")
    if len(frame) < len(curated):
        print(f"WARNING: {len(curated) - len(frame)} molecules of {len(curated)} have no "
              f"coordinates. Did every molecule go through the model?")
    return frame.drop(columns=["input"]).reset_index(drop=True)


def coordinates(frame, projection):
    """Return the x and y columns of one of the four eos1klk projections."""
    if projection not in PROJECTIONS:
        raise ValueError(f"{projection!r} is not one of {list(PROJECTIONS)}")
    return frame[f"{projection}_x"].to_numpy(), frame[f"{projection}_y"].to_numpy()


def plot_points(ax, frame, projection, color, label=None, alpha=0.6):
    """Draw a set of molecules on a map. `color` is one colour, or one per molecule."""
    x, y = coordinates(frame, projection)
    ax.scatter(x, y, color=color, alpha=alpha, label=label)


def plot_backdrop(ax, frame, projection):
    """Draw every molecule as a faint grey point, so a highlighted subset has context."""
    plot_points(ax, frame, projection, color=stylia.NamedColors().gray, alpha=0.2)


def label_space(ax, projection, title, abc=None):
    """Name the axes of a map after the projection drawn on it."""
    name = PROJECTIONS[projection]
    stylia.label(ax, xlabel=f"{name} 1", ylabel=f"{name} 2", title=title, abc=abc)


def murcko_scaffolds(smiles):
    """Return the Bemis-Murcko scaffold of every molecule, as a SMILES string.

    The scaffold is what is left of a molecule once every side chain is removed: its
    rings and the links between them. Molecules with no rings at all, and molecules
    RDKit cannot read, get `None`.
    """
    scaffolds = []
    for text in smiles:
        molecule = Chem.MolFromSmiles(text)
        scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=molecule) if molecule else ""
        scaffolds.append(scaffold or None)
    return np.array(scaffolds, dtype=object)


def has_substructure(smiles, smarts):
    """Return True for every molecule that contains the given SMARTS pattern.

    A SMARTS pattern is a way of writing a partial molecule, such as a ring system,
    that can be searched for inside a bigger one.
    """
    pattern = Chem.MolFromSmarts(smarts)
    if pattern is None:
        raise ValueError(f"{smarts!r} is not a valid SMARTS pattern")
    found = []
    for text in smiles:
        molecule = Chem.MolFromSmiles(text)
        found.append(bool(molecule) and molecule.HasSubstructMatch(pattern))
    return np.array(found)


def label_substructures(smiles, patterns):
    """Label each molecule with the first pattern in `patterns` that it contains.

    `patterns` is a dictionary of name -> SMARTS. Molecules matching none of them are
    labelled `other`, so every molecule ends up with exactly one label.
    """
    labels = np.full(len(smiles), "other", dtype=object)
    for name, smarts in patterns.items():
        unlabelled = labels == "other"
        labels[unlabelled & has_substructure(smiles, smarts)] = name
    return labels


def draw_molecules(smiles, legends, per_row=4):
    """Draw molecules side by side, with a caption under each one."""
    molecules = [Chem.MolFromSmiles(text) for text in smiles]
    return Draw.MolsToGridImage(molecules, legends=[str(x) for x in legends],
                                molsPerRow=per_row, subImgSize=(260, 200))
