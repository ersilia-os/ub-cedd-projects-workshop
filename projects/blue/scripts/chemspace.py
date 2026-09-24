"""Helper functions for the blue group's chemical space notebook.

The coordinates the notebook plots come from the Ersilia model `eos1klk`, which places
a molecule on a map drawn from 1.3 million reference compounds. This module joins those
coordinates to the Pharmit hit list, compares every hit with the silymarin seed, and
keeps the repetitive parts of the plots out of the notebook cells.
"""

import numpy as np
import pandas as pd
import stylia
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import Descriptors, Draw, rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.SimDivFilters import MaxMinPicker

# RDKit prints a warning for every molecule it cannot read. We count them instead.
RDLogger.DisableLog("rdApp.*")

# The four maps eos1klk returns, and the name to write on a plot.
PROJECTIONS = {"pca": "PCA", "tsne": "t-SNE", "umap": "UMAP", "tmap": "TMAP"}

# The properties the notebook describes the molecules with, and the name for an axis.
DESCRIPTORS = {
    "mw": ("Molecular weight", Descriptors.MolWt),
    "logp": ("logP", Descriptors.MolLogP),
    "tpsa": ("Polar surface area", Descriptors.TPSA),
    "hbd": ("Hydrogen bond donors", Descriptors.NumHDonors),
    "hba": ("Hydrogen bond acceptors", Descriptors.NumHAcceptors),
    "rotatable_bonds": ("Rotatable bonds", Descriptors.NumRotatableBonds),
}

# ECFP4 in RDKit's own words: circular fingerprints of radius 2, folded to 2048 bits.
_FINGERPRINTS = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def load_space(table_path, projection_path):
    """Join a molecule table and an eos1klk output file, molecule by molecule.

    eos1klk writes one row per input molecule, with the molecule in an `input` column
    and its coordinates in `pca_x`, `pca_y`, `tsne_x` and so on. Rows are matched on
    the SMILES, so the two files do not have to be in the same order.
    """
    table = pd.read_csv(table_path)
    projection = pd.read_csv(projection_path).drop(columns=["key"], errors="ignore")
    frame = table.merge(projection, left_on="smiles", right_on="input", how="inner")
    if len(frame) < len(table):
        print(f"WARNING: {len(table) - len(frame)} molecules of {len(table)} have no "
              f"coordinates. Did every molecule go through the model?")
    return frame.drop(columns=["input"]).reset_index(drop=True)


def check_seed(seed, smiles):
    """Stop if the coordinates in the seed file belong to a different molecule.

    The seed file is made by hand, outside this notebook, by running one SMILES through
    a model elsewhere. That makes it easy for the wrong molecule to end up in it, and the
    mistake is invisible on a plot. Comparing the two structures catches it straight away,
    instead of drawing one molecule and plotting the position of another.
    """
    if len(seed) != 1:
        raise ValueError(f"the seed file should have exactly one row, not {len(seed)}")
    found = Chem.CanonSmiles(seed["smiles"].iloc[0])
    wanted = Chem.CanonSmiles(smiles)
    if found != wanted:
        raise ValueError(f"the seed coordinates were computed for a different molecule.\n"
                         f"  the file has: {found}\n"
                         f"  expected:     {wanted}")
    print("Checked: the coordinates in the seed file belong to the molecule below.")


def coordinates(frame, projection):
    """Return the x and y columns of one of the four eos1klk projections."""
    if projection not in PROJECTIONS:
        raise ValueError(f"{projection!r} is not one of {list(PROJECTIONS)}")
    return frame[f"{projection}_x"].to_numpy(), frame[f"{projection}_y"].to_numpy()


def plot_points(ax, frame, projection, color, label=None, alpha=0.6, size=None):
    """Draw a set of molecules on a map. `color` is one colour, or one per molecule."""
    x, y = coordinates(frame, projection)
    ax.scatter(x, y, color=color, alpha=alpha, label=label, s=size)


def plot_backdrop(ax, frame, projection):
    """Draw every molecule as a faint grey point, so a highlighted subset has context."""
    plot_points(ax, frame, projection, color=stylia.NamedColors().silver, alpha=0.2)


def plot_seed(ax, seed, projection, color, label="silymarin"):
    """Mark the seed molecule on a map, as one large star that stands out."""
    x, y = coordinates(seed, projection)
    ax.scatter(x, y, color=color, marker="*", s=400, edgecolor="black",
               linewidth=0.6, zorder=5, label=label)


def label_space(ax, projection, title, abc=None):
    """Name the axes of a map after the projection drawn on it."""
    name = PROJECTIONS[projection]
    stylia.label(ax, xlabel=f"{name} 1", ylabel=f"{name} 2", title=title, abc=abc)


def describe(smiles):
    """Return a table of the properties in `DESCRIPTORS`, one row per molecule."""
    rows = []
    for text in smiles:
        molecule = Chem.MolFromSmiles(text)
        if molecule is None:
            rows.append({name: np.nan for name in DESCRIPTORS})
            continue
        rows.append({name: function(molecule) for name, (_, function) in DESCRIPTORS.items()})
    return pd.DataFrame(rows, index=pd.RangeIndex(len(rows)))


def fingerprints(smiles):
    """Return the ECFP4 fingerprint of every molecule.

    A fingerprint describes a molecule as a long list of yes/no answers, one per small
    fragment found in it. Two molecules built from the same fragments get similar
    fingerprints, which is what makes them comparable.
    """
    prints = []
    for text in smiles:
        molecule = Chem.MolFromSmiles(text)
        prints.append(_FINGERPRINTS.GetFingerprint(molecule) if molecule else None)
    return prints


def tanimoto(prints, reference):
    """Return how similar every fingerprint is to one reference fingerprint.

    The Tanimoto similarity runs from 0, nothing in common, to 1, identical sets of
    fragments. Above about 0.4 two molecules are usually recognisable as relatives.
    """
    scores = [DataStructs.TanimotoSimilarity(p, reference) if p else np.nan for p in prints]
    return np.array(scores)


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


def diverse_subset(prints, how_many, seed=42):
    """Pick molecules that are as unlike each other as possible, and return their rows.

    This is the MaxMin algorithm: start from one molecule, then repeatedly add whichever
    molecule is furthest from everything picked so far. It is the usual way to turn a
    long hit list into a short one that still covers the whole range of chemistry.
    """
    picker = MaxMinPicker()
    distance = lambda i, j: 1 - DataStructs.TanimotoSimilarity(prints[i], prints[j])
    return list(picker.LazyPick(distance, len(prints), how_many, seed=seed))


def draw_molecules(smiles, legends, per_row=4):
    """Draw molecules side by side, with a caption under each one."""
    molecules = [Chem.MolFromSmiles(text) for text in smiles]
    return Draw.MolsToGridImage(molecules, legends=[str(x) for x in legends],
                                molsPerRow=per_row, subImgSize=(260, 200))
