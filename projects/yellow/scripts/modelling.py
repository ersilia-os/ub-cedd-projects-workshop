"""Helper functions for the yellow group's modelling notebooks.

These turn molecules into numbers, find their scaffolds and score a model. The
decisions (which model, which split, which cutoff) are deliberately left in the
notebook, not hidden in here.
"""

import os
import sys

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold
from scipy.stats import spearmanr
from sklearn.base import clone
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    root_mean_squared_error,
)

RDLogger.DisableLog("rdApp.*")


def morgan_fingerprints(smiles, radius=2, n_bits=2048):
    """Compute a Morgan (ECFP) fingerprint for each molecule.

    Each bit says whether a small circular fragment, up to `radius` bonds away from
    some atom, is present in the molecule. Radius 2 is the usual choice, and is also
    called ECFP4.

    Parameters
    ----------
    smiles : list of str
        The molecules, as SMILES.
    radius : int
        How many bonds out from each atom a fragment may reach.
    n_bits : int
        Length of the fingerprint.

    Returns
    -------
    numpy.ndarray
        One row per molecule and one column per bit, filled with 0 and 1.
    """
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=n_bits)
    matrix = np.zeros((len(smiles), n_bits), dtype=np.uint8)
    for i, smi in enumerate(smiles):
        mol = Chem.MolFromSmiles(smi)
        if mol is not None:
            matrix[i] = generator.GetFingerprintAsNumPy(mol)
    return matrix


def murcko_scaffolds(smiles):
    """Find the Bemis-Murcko scaffold of each molecule.

    The scaffold is what is left after stripping off every side chain: the rings and
    the chains that link them. Molecules with the same scaffold belong to the same
    chemical series.

    Parameters
    ----------
    smiles : list of str
        The molecules, as SMILES.

    Returns
    -------
    list of str
        One scaffold SMILES per molecule. Molecules without any ring have no scaffold,
        so they get their own SMILES instead and count as a series of one.
    """
    scaffolds = []
    for smi in smiles:
        mol = Chem.MolFromSmiles(smi)
        scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=mol) if mol is not None else ""
        scaffolds.append(scaffold or smi)
    return scaffolds


def classification_metrics(y_true, y_proba, threshold=0.5):
    """Score a classifier from its predicted probabilities of being active.

    Parameters
    ----------
    y_true : array-like
        The real labels, 1 for active and 0 for inactive.
    y_proba : array-like
        The predicted probability of being active.
    threshold : float
        Probability above which a molecule is called active.

    Returns
    -------
    dict
        ROC-AUC, PR-AUC, balanced accuracy, precision and recall.
    """
    y_pred = (np.asarray(y_proba) >= threshold).astype(int)
    return {
        "ROC-AUC": roc_auc_score(y_true, y_proba),
        "PR-AUC": average_precision_score(y_true, y_proba),
        "balanced accuracy": balanced_accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred),
    }


def plot_proba_by_class(ax, y_true, y_proba, colors, threshold=0.5, seed=42):
    """Draw the predicted probability of the inactive and the active molecules.

    One box per class, with every molecule drawn as a dot on top of it. The dots are
    spread sideways at random so they do not hide each other; their height is the
    only thing that matters.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The panel to draw in.
    y_true : array-like
        The real labels, 1 for active and 0 for inactive.
    y_proba : array-like
        The predicted probability of being active.
    colors : list
        Two colours, for the inactive and the active molecules.
    threshold : float
        Probability above which a molecule is called active, drawn as a dashed line.
    seed : int
        Seed for the sideways spread, so the plot looks the same every time.
    """
    y_true, y_proba = np.asarray(y_true), np.asarray(y_proba)
    groups = [y_proba[y_true == 0], y_proba[y_true == 1]]
    rng = np.random.default_rng(seed)
    for i, (values, color) in enumerate(zip(groups, colors)):
        spread = rng.uniform(-0.2, 0.2, len(values))
        ax.scatter(i + spread, values, color=color, alpha=0.25, linewidths=0)
    ax.boxplot(groups, positions=[0, 1], widths=0.6, showfliers=False,
               medianprops={"color": "black"})
    ax.axhline(threshold, color="black", alpha=0.5, linestyle="--")
    ax.set_xticks([0, 1], ["inactive", "active"])
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylim(-0.02, 1.02)


def regression_metrics(y_true, y_pred):
    """Score a regressor from its predicted values.

    Parameters
    ----------
    y_true : array-like
        The measured values.
    y_pred : array-like
        The predicted values.

    Returns
    -------
    dict
        R2, RMSE, MAE and the Spearman rank correlation.
    """
    return {
        "R2": r2_score(y_true, y_pred),
        "RMSE": root_mean_squared_error(y_true, y_pred),
        "MAE": mean_absolute_error(y_true, y_pred),
        "Spearman": spearmanr(y_true, y_pred).statistic,
    }


def cross_validate(model, X, y, splitter, groups=None):
    """Train and score a fresh copy of a model on every fold of a split.

    Classifiers are scored with `classification_metrics` and regressors with
    `regression_metrics`.

    Parameters
    ----------
    model : scikit-learn estimator
        The model to copy and train. It is not changed.
    X : numpy.ndarray
        The features, one row per molecule.
    y : array-like
        The labels or values to predict.
    splitter : scikit-learn splitter
        Decides which molecules go in each fold, for example `KFold` or `GroupKFold`.
    groups : array-like, optional
        The group of each molecule (its scaffold), for splitters that need one.

    Returns
    -------
    pandas.DataFrame
        One row per fold and one column per metric.
    """
    y = np.asarray(y)
    rows = []
    for train, test in splitter.split(X, y, groups):
        fitted = clone(model).fit(X[train], y[train])
        if hasattr(fitted, "predict_proba"):
            scores = classification_metrics(y[test], fitted.predict_proba(X[test])[:, 1])
        else:
            scores = regression_metrics(y[test], fitted.predict(X[test]))
        rows.append(scores)
    return pd.DataFrame(rows).rename_axis("fold")


def save_model(model, filename):
    """Write a fitted model to `outputs/` and, in Colab, download it to your computer.

    Colab deletes its files when it disconnects, so the download is the copy that
    lasts. A model trained on all the data has no test score of its own: the numbers
    to report with it are the cross-validation scores measured before it was trained.

    Parameters
    ----------
    model : fitted estimator
        Any scikit-learn model.
    filename : str
        Name of the file to write inside `outputs/`, ending in `.joblib`.

    Returns
    -------
    str
        The path the model was written to.
    """
    import joblib

    os.makedirs("outputs", exist_ok=True)
    path = os.path.join("outputs", filename)
    joblib.dump(model, path, compress=3)
    return download_file(path)


def download_file(path):
    """In Colab, send a file to your computer. Elsewhere, only report where it is.

    Parameters
    ----------
    path : str
        The file to download.

    Returns
    -------
    str
        The same path.
    """
    print(f"{path} ({os.path.getsize(path) / 1e6:.1f} MB)")
    if "google.colab" in sys.modules:
        from google.colab import files
        files.download(path)
    return path
