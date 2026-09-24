"""Helper functions for the purple group's data curation notebook.

These are the steps that are too long to read comfortably inside a notebook cell.
The decisions (which records to keep, which cutoff to use, how to merge the two
endpoints) are deliberately left in the notebook, not hidden in here.
"""

import os
import sys

import numpy as np
import pandas as pd

# ChEMBL writes the same idea in several ways. A missing relation means the value is
# an exact measurement.
RELATIONS = {
    "=": "=", "~": "=", "": "=",
    ">": ">", ">=": ">", ">>": ">",
    "<": "<", "<=": "<", "<<": "<",
}

# How many nanomolar one unit of each kind is worth.
UNIT_TO_NM = {"nM": 1.0, "pM": 1e-3, "uM": 1e3, "mM": 1e6, "M": 1e9}

# Micrograms per millilitre is a mass, not a concentration of molecules, so it can
# only be converted once we know how heavy the molecule is.
MASS_UNITS = {"ug.mL-1", "ug ml-1"}

# Different ChEMBL exports name the same column differently.
COLUMN_ALIASES = {"smiles": "canonical_smiles", "molecule_smiles": "canonical_smiles"}

# Without these the notebook cannot run at all.
REQUIRED_COLUMNS = ["canonical_smiles", "standard_type", "standard_relation",
                    "standard_value", "standard_units"]

# These are used if present, and filled with blanks if the export left them out.
OPTIONAL_COLUMNS = ["molecule_chembl_id", "pchembl_value", "data_validity_comment"]


def load_downloads(paths):
    """Read the ChEMBL download files and stack them into one table.

    ChEMBL can be exported in more than one way, and the exports do not all use the
    same separator or the same column headings: the website writes `Smiles` where the
    programming interface writes `canonical_smiles`. This function accepts either, so
    it does not matter which route was used to get the data.

    Parameters
    ----------
    paths : dict
        Endpoint name (for example "EC50") mapped to the path of its CSV file.

    Returns
    -------
    pandas.DataFrame
        All records, with an `endpoint` column saying which file each row came from.

    Raises
    ------
    ValueError
        If a file is missing a column the rest of the notebook cannot do without.
    """
    frames = []
    for endpoint, path in paths.items():
        with open(path) as handle:
            header = handle.readline()
        separator = ";" if header.count(";") > header.count(",") else ","
        frame = pd.read_csv(path, sep=separator, low_memory=False)
        frame.columns = [
            column.strip().lstrip("#").lower().replace(" ", "_")
            for column in frame.columns
        ]
        frame = frame.rename(columns=COLUMN_ALIASES)

        absent = [column for column in REQUIRED_COLUMNS if column not in frame]
        if absent:
            raise ValueError(
                f"{path} has no column called {' or '.join(absent)}. "
                f"It has: {', '.join(sorted(frame.columns))}"
            )
        # The website export writes the relation in quotes ('=', '>').
        frame["standard_relation"] = frame["standard_relation"].str.strip("'\" ")
        for column in OPTIONAL_COLUMNS:
            if column not in frame:
                frame[column] = pd.Series(np.nan, index=frame.index, dtype=object)
        frame["endpoint"] = endpoint
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def standardize_smiles(smiles_list):
    """Clean up a list of SMILES strings and give each molecule an identity code.

    A SMILES string is a way of writing a molecule as text. The same molecule can be
    written in several different SMILES, and ChEMBL often stores it as a salt (the
    molecule plus a counter-ion such as chloride). This function removes the salt,
    rewrites the molecule in one agreed form, and computes its InChIKey: a 27
    character code that is the same for any two identical molecules.

    Parameters
    ----------
    smiles_list : iterable of str
        The SMILES strings to clean up.

    Returns
    -------
    pandas.DataFrame
        One row per input SMILES, with columns `canonical_smiles` (the input),
        `smiles` (cleaned), `inchikey` (the identity code) and `mw` (molecular
        weight in g/mol). Molecules that cannot be read are left out.
    """
    # RDKit chatters as it works. The logging has to be switched off before
    # chembl_structure_pipeline is imported, otherwise it still prints.
    from rdkit import Chem, RDLogger, rdBase
    from rdkit.Chem import Descriptors

    RDLogger.DisableLog("rdApp.*")
    rdBase.DisableLog("rdApp.info")

    from chembl_structure_pipeline import standardizer
    rows = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue
        try:
            mol, _ = standardizer.get_parent_mol(mol)  # drops salts and solvents
            mol = standardizer.standardize_mol(mol)
        except Exception:
            continue
        if mol is None or mol.GetNumAtoms() == 0:
            continue
        rows.append({
            "canonical_smiles": smiles,
            "smiles": Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True),
            "inchikey": Chem.MolToInchiKey(mol),
            "mw": round(Descriptors.MolWt(mol), 3),
        })
    return pd.DataFrame(rows)


def to_nanomolar(values, units, weights):
    """Convert measured concentrations to nanomolar.

    Parameters
    ----------
    values : pandas.Series
        The measured numbers.
    units : pandas.Series
        The unit each number was measured in.
    weights : pandas.Series
        Molecular weight in g/mol, needed for the mass units.

    Returns
    -------
    pandas.Series
        The same measurements in nanomolar. Units that cannot be converted give NaN.
    """
    factor = units.map(UNIT_TO_NM)
    # ug/mL is the same as mg/L. Dividing by the molecular weight in mg/mmol gives
    # mmol/L, and one mmol/L is a million nanomolar.
    by_mass = values / weights * 1e6
    return pd.Series(
        np.where(units.isin(MASS_UNITS), by_mass, values * factor), index=values.index
    )


def pactivity(value_nm):
    """Turn a concentration in nanomolar into a pActivity value.

    pActivity is minus the base-10 logarithm of the concentration in molar. It turns
    a number where small means potent into one where large means potent, and it
    spreads the values out evenly: 1 nM is 9, 1 uM is 6, 100 uM is 4.
    """
    return -np.log10(value_nm * 1e-9)


def summarise_replicates(df, key):
    """Collapse repeated measurements of the same molecule into a single row.

    Only exact measurements ("=") are averaged. The median is used rather than the
    mean because one badly wrong number cannot drag it far.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain `relation`, `pactivity` and the columns named in `key`.
    key : list of str
        The columns that identify one molecule, for example
        ``["inchikey", "endpoint"]``.

    Returns
    -------
    pandas.DataFrame
        One row per key, with the median pActivity, how many measurements went into
        it, and the lowest and highest of them.
    """
    exact = df[df["relation"] == "="].groupby(key)["pactivity"]
    summary = pd.DataFrame({
        "n_exact": exact.size(),
        "pactivity": exact.median(),
        "pactivity_min": exact.min(),
        "pactivity_max": exact.max(),
    })
    summary["spread"] = summary["pactivity_max"] - summary["pactivity_min"]
    return summary


def decisive_bounds(df, key, cutoff_nm, keep_inactive=True, keep_active=True):
    """Rescue molecules that only have a "greater than" or "less than" record.

    A bound is only worth keeping when it already falls on the decided side of the
    cutoff. With a cutoff of 1 uM, "greater than 50 uM" proves the molecule is
    inactive and "less than 5 nM" proves it is active, but "greater than 100 nM"
    proves nothing either way.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain `relation`, `value_nm` and the columns named in `key`.
    key : list of str
        The columns that identify one molecule.
    cutoff_nm : float
        The activity cutoff, in nanomolar.
    keep_inactive, keep_active : bool
        Whether to rescue the ">" and the "<" records respectively.

    Returns
    -------
    pandas.DataFrame
        One row per key, with `pactivity`, a `source` column saying which kind of
        bound it came from, and `n_exact` set to zero. Molecules bounded from both
        sides at once are dropped, because the two bounds contradict each other.
    """
    lower = df[df["relation"] == ">"].groupby(key)["value_nm"].min()
    upper = df[df["relation"] == "<"].groupby(key)["value_nm"].max()
    proven_inactive = lower[lower >= cutoff_nm]
    proven_active = upper[upper <= cutoff_nm]
    contradictory = proven_inactive.index.intersection(proven_active.index)

    pieces = []
    if keep_inactive:
        kept = proven_inactive[~proven_inactive.index.isin(contradictory)]
        pieces.append(pd.DataFrame({"pactivity": pactivity(kept),
                                    "source": "bounded inactive"}))
    if keep_active:
        kept = proven_active[~proven_active.index.isin(contradictory)]
        pieces.append(pd.DataFrame({"pactivity": pactivity(kept),
                                    "source": "bounded active"}))
    if not pieces:
        return pd.DataFrame(columns=["pactivity", "source", "n_exact"])
    bounded = pd.concat(pieces)
    bounded["n_exact"] = 0
    return bounded


def smiles_for_ersilia(smiles):
    """Return a one-column table, headed `smiles`, ready to use as Ersilia input."""
    smiles = pd.Series(smiles).dropna().drop_duplicates()
    return pd.DataFrame({"smiles": smiles.to_numpy()})


def save_output(table, filename, index=True):
    """Write a table to `outputs/` and, in Colab, download it to your computer.

    Colab deletes its files when it disconnects, so the download is the copy that
    lasts. Upload it to the group's Drive folder afterwards.
    """
    os.makedirs("outputs", exist_ok=True)
    path = os.path.join("outputs", filename)
    table.to_csv(path, index=index)
    if "google.colab" in sys.modules:
        from google.colab import files
        files.download(path)
    print(f"{len(table):,} rows written to {path} ({os.path.getsize(path) / 1e6:.1f} MB)")
    return path
