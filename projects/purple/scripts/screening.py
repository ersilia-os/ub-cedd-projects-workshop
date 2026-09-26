"""Helper functions for screening a compound library with the group's HIV-1 models.

These prepare an outside library so it can be scored by a model trained on the curated
ChEMBL data, and measure how far each molecule sits from that training data. The
decisions (which library, which cutoff, what counts as too close) stay in the notebook.
"""

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")


def prepare_library(frame, smiles_column, id_column, name_column, label, mw_cap=1000.0):
    """Clean an outside library so it matches how the training data was prepared.

    A model can only be trusted on molecules that were prepared the same way as the
    ones it learned from. This drops rows with no structure, removes anything RDKit
    cannot read, removes molecules with no carbon atom (salts and simple inorganics),
    desalts and canonicalises the rest, and applies the same molecular weight limit
    the models were trained behind. Finally it keeps one row per InChIKey, so the same
    molecule listed twice is only scored once.

    Parameters
    ----------
    frame : pandas.DataFrame
        The library as read from its CSV file.
    smiles_column : str
        Name of the column holding the SMILES strings.
    id_column : str
        Name of the column holding the library's own identifier.
    name_column : str or None
        Name of the column holding a human-readable compound name, or None if the
        library has none.
    label : str
        A short name for the library, stored in the `library` column.
    mw_cap : float, optional
        Largest molecular weight to keep, in g/mol. The default, 1000, is the limit
        used when the models were trained.

    Returns
    -------
    pandas.DataFrame
        Columns `library`, `source_id`, `mol_name`, `smiles` (cleaned), `inchikey`
        and `mw`, with one row per unique molecule.
    """
    from . import curation

    frame = frame.dropna(subset=[smiles_column]).copy()
    molecules = [Chem.MolFromSmiles(smiles) for smiles in frame[smiles_column]]
    keep = [
        mol is not None and any(atom.GetSymbol() == "C" for atom in mol.GetAtoms())
        for mol in molecules
    ]
    frame = frame[keep].reset_index(drop=True)

    # `standardize_smiles` returns a column called `smiles` of its own, which would
    # collide with a library whose input column has the same name.
    standard = curation.standardize_smiles(frame[smiles_column])
    standard = standard.drop_duplicates("canonical_smiles").rename(
        columns={"smiles": "clean_smiles", "inchikey": "clean_inchikey", "mw": "clean_mw"}
    )
    merged = frame.merge(
        standard, left_on=smiles_column, right_on="canonical_smiles", how="inner"
    )
    merged = merged[merged["clean_mw"] <= mw_cap]
    merged = merged.drop_duplicates("clean_inchikey").reset_index(drop=True)

    return pd.DataFrame({
        "library": label,
        "source_id": merged[id_column].to_numpy(),
        "mol_name": merged[name_column].to_numpy() if name_column else "",
        "smiles": merged["clean_smiles"].to_numpy(),
        "inchikey": merged["clean_inchikey"].to_numpy(),
        "mw": merged["clean_mw"].to_numpy(),
    })


def max_similarity(query, reference, chunk=2000):
    """Find each query molecule's closest match among the reference molecules.

    The similarity is the Tanimoto coefficient: the number of fingerprint bits two
    molecules share, divided by the number either of them has. It runs from 0 (nothing
    in common) to 1 (identical fingerprints).

    On a fingerprint matrix of zeros and ones, the dot product of two rows counts the
    bits they share, so the whole comparison is one matrix multiplication. That is why
    this can compare twenty thousand molecules against twenty thousand others in about
    a second.

    Parameters
    ----------
    query : numpy.ndarray
        Fingerprints of the molecules to look up, shape (n_query, n_bits).
    reference : numpy.ndarray
        Fingerprints to search in, shape (n_reference, n_bits).
    chunk : int, optional
        How many query molecules to compare at once. Lower it if memory is short.

    Returns
    -------
    similarity : numpy.ndarray
        The highest Tanimoto similarity found for each query molecule.
    index : numpy.ndarray
        Row number in `reference` of that closest match.
    """
    reference = reference.astype(np.float32)
    reference_bits = reference.sum(1)
    query = query.astype(np.float32)
    query_bits = query.sum(1)
    similarity = np.empty(len(query), np.float32)
    index = np.empty(len(query), np.int64)
    for start in range(0, len(query), chunk):
        block = query[start:start + chunk]
        shared = block @ reference.T
        either = query_bits[start:start + chunk, None] + reference_bits[None, :] - shared
        scores = shared / np.maximum(either, 1.0)
        similarity[start:start + chunk] = scores.max(1)
        index[start:start + chunk] = scores.argmax(1)
    return similarity, index


def self_similarity(fingerprints):
    """Tanimoto similarity of every pair of molecules within one set.

    Used to ask whether a shortlist is a set of separate findings or one family of
    closely related molecules found many times over.

    Parameters
    ----------
    fingerprints : numpy.ndarray
        Fingerprints of the molecules, shape (n, n_bits).

    Returns
    -------
    numpy.ndarray
        The similarity of each pair, as a flat array of length n * (n - 1) / 2.
    """
    fingerprints = fingerprints.astype(np.float32)
    bits = fingerprints.sum(1)
    shared = fingerprints @ fingerprints.T
    scores = shared / (bits[:, None] + bits[None, :] - shared)
    rows, columns = np.triu_indices(len(fingerprints), k=1)
    return scores[rows, columns]
