"""Helper functions for the purple group's chemical space notebook.

The coordinates the notebook plots come from the Ersilia model `eos1klk`, which places
a molecule on a map drawn from 1.3 million reference compounds. This module joins those
coordinates to the curated activity table, searches for ring systems, and keeps the
repetitive parts of the plots out of the notebook cells. Scaffolds come from
`modelling.murcko_scaffolds`, which the modelling notebook already uses.
"""

import numpy as np
import pandas as pd
import stylia
from rdkit import Chem, RDLogger
from rdkit.Chem import Draw

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


def plot_points(ax, frame, projection, color, label=None, alpha=0.3):
    """Draw a set of molecules on a map. `color` is one colour, or one per molecule.

    The default `alpha` is low because this dataset has more than twenty thousand
    molecules: without it the crowded regions turn into one solid block.
    """
    x, y = coordinates(frame, projection)
    ax.scatter(x, y, color=color, alpha=alpha, label=label)


def plot_backdrop(ax, frame, projection):
    """Draw every molecule as a faint grey point, so a highlighted subset has context."""
    plot_points(ax, frame, projection, color=stylia.NamedColors().gray, alpha=0.1)


def label_space(ax, projection, title, abc=None):
    """Name the axes of a map after the projection drawn on it."""
    name = PROJECTIONS[projection]
    stylia.label(ax, xlabel=f"{name} 1", ylabel=f"{name} 2", title=title, abc=abc)


def find_drugs(frame, drugs_path):
    """Return the rows of `frame` that are approved drugs, with the drug's name added.

    The drug list carries the InChIKey that ChEMBL holds for each molecule, and the
    curated table was standardised the same way, so the two match directly. How many
    were found is printed, because a drug missing from the dataset is worth knowing
    about rather than passing over in silence.
    """
    drugs = pd.read_csv(drugs_path)
    found = frame.merge(drugs[["drug", "inchikey"]], on="inchikey", how="inner")
    print(f"{len(found)} of the {len(drugs)} approved drugs are in this dataset")
    return found


def neighbour_counts(frame, projection, radius=0.05, points=None):
    """Count how many of `frame`'s molecules sit within `radius` of each point.

    This is a plain measure of how crowded a part of the map is. By default every
    molecule in `frame` is measured; pass `points` to measure a subset of them instead,
    such as the approved drugs. A molecule never counts itself as its own neighbour.
    """
    from scipy.spatial import cKDTree

    tree = cKDTree(np.column_stack(coordinates(frame, projection)))
    target = frame if points is None else points
    counts = tree.query_ball_point(np.column_stack(coordinates(target, projection)),
                                   radius, return_length=True)
    return counts - 1


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
