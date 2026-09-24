"""Helper functions for the orange group's protein structures notebook.

These are the parts that would clutter a notebook cell: asking two web services about
several hundred proteins at once, and cutting one protein chain out of a PDB entry
that may hold many.

The decision of when an experimental structure is good enough, and when to use an
AlphaFold model instead, is deliberately left in the notebook.
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor

import gemmi
import pandas as pd
import requests

# PDBe ranks every PDB chain that maps to a UniProt accession, best first: the ones
# that cover most of the protein, then the ones with the best resolution.
PDBE_BEST = "https://www.ebi.ac.uk/pdbe/api/mappings/best_structures/{}"
ALPHAFOLD_API = "https://alphafold.ebi.ac.uk/api/prediction/{}"
# RCSB's ModelServer returns a single chain of an entry. That matters for cryo-EM
# structures of the ribosome, where the whole entry is tens of megabytes.
RCSB_CHAIN = "https://models.rcsb.org/v1/{}/atoms?auth_asym_id={}&encoding=cif"

STRUCTURE_FOLDER = "data/downloads/structures"


def _get(url, attempts=3):
    """GET a URL, trying again if the connection drops.

    With eight requests in flight, a public server occasionally closes one of them.
    A 404 is returned as it is: it means "nothing here", which callers handle.
    """
    for attempt in range(attempts):
        try:
            response = requests.get(url, timeout=120)
            if response.status_code == 404 or response.ok:
                return response
        except requests.ConnectionError:
            if attempt == attempts - 1:
                raise
        time.sleep(2 ** attempt)
    response.raise_for_status()


def pdb_best_structures(accession):
    """List the PDB chains that contain one protein, best first.

    Parameters
    ----------
    accession : str
        UniProt accession, e.g. `P9WGR1`.

    Returns
    -------
    pandas.DataFrame
        One row per PDB chain, in PDBe's order, with columns `pdb_id`, `chain_id`,
        `experimental_method`, `resolution`, `unp_start`, `unp_end` and `coverage`
        (the fraction of the UniProt sequence the chain contains). Empty if the
        protein has no experimental structure.
    """
    response = _get(PDBE_BEST.format(accession))
    columns = ["pdb_id", "chain_id", "experimental_method", "resolution",
               "unp_start", "unp_end", "coverage"]
    # PDBe answers 404 when there is no structure, which is a result, not an error.
    if response.status_code == 404:
        return pd.DataFrame(columns=columns)
    response.raise_for_status()
    return pd.DataFrame(response.json()[accession])[columns]


def alphafold_entry(accession):
    """Describe the AlphaFold model of one protein.

    Parameters
    ----------
    accession : str
        UniProt accession, e.g. `P9WGR1`.

    Returns
    -------
    dict
        `af_url` (the model as a PDB file), `af_version` and `af_plddt` (the model's
        mean confidence, 0 to 100). All three are None if AlphaFold has no model.
    """
    response = _get(ALPHAFOLD_API.format(accession))
    if response.status_code == 404:
        return {"af_url": None, "af_version": None, "af_plddt": None}
    response.raise_for_status()
    # Some proteins are split into fragments (F1, F2, ...); F1 is listed first.
    model = response.json()[0]
    return {"af_url": model["pdbUrl"], "af_version": model["latestVersion"],
            "af_plddt": model["globalMetricValue"]}


def best_pdb_chain(accession):
    """Summarise the single best PDB chain for one protein.

    Parameters
    ----------
    accession : str
        UniProt accession.

    Returns
    -------
    dict
        `n_pdb_chains` and, for the best chain, `pdb_id`, `chain`, `coverage`,
        `resolution` and `method`. The last five are None if there is no chain.
    """
    chains = pdb_best_structures(accession)
    best = {"n_pdb_chains": len(chains), "pdb_id": None, "chain": None,
            "coverage": None, "resolution": None, "method": None}
    if len(chains):
        top = chains.iloc[0]
        best.update(pdb_id=top["pdb_id"], chain=top["chain_id"],
                    coverage=top["coverage"], resolution=top["resolution"],
                    method=top["experimental_method"])
    return best


def fetch_all(accessions, func, workers=8):
    """Call `func` on every accession, several at a time.

    One request per protein, one after the other, would take several minutes for a
    few hundred proteins. Running eight at once brings that down to under a minute
    without overloading the services.

    Parameters
    ----------
    accessions : list of str
        UniProt accessions.
    func : callable
        Takes one accession and returns a dict, e.g. `best_pdb_chain`.
    workers : int, optional
        How many requests to have in flight at once.

    Returns
    -------
    pandas.DataFrame
        One row per accession, in the same order, with a `uniprot_ac` column and one
        column per key of the dicts `func` returns.
    """
    accessions = list(accessions)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(func, accessions))
    table = pd.DataFrame(results)
    table.insert(0, "uniprot_ac", accessions)
    return table


def structure_path(row, folder=STRUCTURE_FOLDER):
    """Where the structure file for one target is kept.

    Parameters
    ----------
    row : pandas.Series or dict
        Needs `uniprot_ac` and `structure_source` (`PDB` or `AlphaFold`).
    folder : str, optional
        Folder the structure files go in.

    Returns
    -------
    str
        e.g. `data/downloads/structures/P9WGR1_PDB.pdb`.
    """
    return os.path.join(folder, f"{row['uniprot_ac']}_{row['structure_source']}.pdb")


def download_structure(row, folder=STRUCTURE_FOLDER):
    """Download the structure chosen for one target, unless it is already there.

    A PDB entry can hold many chains (several copies of the protein, partners in a
    complex), plus water and bound molecules. Only the chosen chain is downloaded, and
    only its protein atoms are kept, so every file holds exactly one copy of one
    protein. AlphaFold models
    already are a single chain and are saved unchanged.

    Parameters
    ----------
    row : pandas.Series or dict
        Needs `uniprot_ac` and `structure_source`, plus `pdb_id` and `chain` for PDB
        structures or `af_url` for AlphaFold models.
    folder : str, optional
        Folder the structure files go in.

    Returns
    -------
    str
        Path to the saved file.
    """
    path = structure_path(row, folder)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    os.makedirs(folder, exist_ok=True)
    if row["structure_source"] == "AlphaFold":
        response = _get(row["af_url"])
        response.raise_for_status()
        with open(path, "w") as f:
            f.write(response.text)
        return path

    response = _get(RCSB_CHAIN.format(row["pdb_id"], row["chain"]))
    response.raise_for_status()
    block = gemmi.cif.read_string(response.text).sole_block()
    structure = gemmi.make_structure_from_block(block)
    structure.setup_entities()
    structure.remove_ligands_and_waters()
    structure.remove_hydrogens()
    model = structure[0]
    structure.remove_empty_chains()
    if len(model) == 0:
        raise ValueError(f"no protein atoms in chain {row['chain']} of {row['pdb_id']}")
    # Large cryo-EM entries use chain names like `AAA`, which the PDB format cannot
    # hold. The file has one chain only, so it can simply be called A.
    model[0].name = "A"
    structure.write_pdb(path)
    return path


def download_all(table, folder=STRUCTURE_FOLDER, workers=8):
    """Download the structure of every target in a table, several at a time.

    Parameters
    ----------
    table : pandas.DataFrame
        One row per target, with the columns `download_structure` needs.
    folder : str, optional
        Folder the structure files go in.
    workers : int, optional
        How many downloads to run at once.

    Returns
    -------
    list of str
        The path of each target's file, in the same order as `table`.
    """
    rows = [row for _, row in table.iterrows()]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda row: download_structure(row, folder), rows))
