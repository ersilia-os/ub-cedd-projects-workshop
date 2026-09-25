"""Helper functions for the orange group's ChEMBL precedent notebook.

These are the parts that would clutter a notebook cell: asking a public database about
eleven thousand proteins, comparing 348 sequences against all of them, and collecting
the compounds that were ever tested on each of them.

The decisions - what counts as a good enough match, how potent a compound has to be,
and how the three tiers are defined - are deliberately left in the notebook.
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
from tqdm.auto import tqdm

CHEMBL_API = "https://www.ebi.ac.uk/chembl/api/data"
UNIPROT_STREAM = "https://rest.uniprot.org/uniprotkb/stream"
# A public service should be able to see who is calling and why.
HEADERS = {"User-Agent": "ub-cedd-workshop (miquel@ersilia.io)"}

# The API never returns more than a thousand rows per request, whatever we ask for.
PAGE = 1000
CACHE_FOLDER = "data/downloads/chembl"
# Files dropped here by hand are used instead of downloading them again.
INDEX_FOLDER = "../../bigfiles"


def _get(url, params=None, attempts=4):
    """GET a URL, trying again if the connection drops or the server asks us to wait.

    With several requests in flight, a public server occasionally closes one of them,
    answers too slowly, or replies 429 ("slow down"). A 404 is returned as it is: it
    means "nothing here", which callers handle.
    """
    for attempt in range(attempts):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=120)
            if response.status_code == 404 or response.ok:
                return response
            if response.status_code in (429, 503):
                time.sleep(float(response.headers.get("Retry-After", 2 ** attempt)))
                continue
        except (requests.ConnectionError, requests.Timeout):
            if attempt == attempts - 1:
                raise
        time.sleep(2 ** attempt)
    response.raise_for_status()


def chembl_version():
    """Return the ChEMBL release the API is serving, e.g. `ChEMBL_37`.

    ChEMBL grows with every release, so any count in the notebook only means
    something next to the release it came from.
    """
    return _get(f"{CHEMBL_API}/status.json").json()["chembl_db_version"]


def paged(endpoint, key, params=None, desc=None, limit=PAGE):
    """Yield every record of a ChEMBL endpoint, one page at a time.

    Parameters
    ----------
    endpoint : str
        Endpoint name, e.g. `target` or `activity`.
    key : str
        The name the endpoint gives its list of records, e.g. `targets`.
    params : dict, optional
        Query parameters, e.g. `{"target_type": "SINGLE PROTEIN"}`.
    desc : str, optional
        Label for the progress bar. No bar is shown if this is None.
    limit : int, optional
        Rows per request, at most 1000.

    Yields
    ------
    dict
        One record.
    """
    params = dict(params or {}, limit=limit, offset=0)
    bar = None
    while True:
        payload = _get(f"{CHEMBL_API}/{endpoint}.json", params).json()
        meta = payload["page_meta"]
        if bar is None and desc is not None:
            bar = tqdm(total=meta["total_count"], desc=desc, unit="row")
        yield from payload[key]
        if bar is not None:
            bar.update(len(payload[key]))
        if payload[key] == [] or meta["offset"] + limit >= meta["total_count"]:
            break
        params["offset"] = meta["offset"] + limit
    if bar is not None:
        bar.close()


def _cached(name, build, folder=CACHE_FOLDER):
    """Return a table, building it only the first time it is asked for.

    The file is written under a temporary name and renamed, so an interrupted run
    never leaves half a table behind.
    """
    for base in (INDEX_FOLDER, folder):
        path = os.path.join(base, name)
        if os.path.exists(path):
            return pd.read_csv(path)
    os.makedirs(folder, exist_ok=True)
    table = build()
    path = os.path.join(folder, name)
    table.to_csv(path + ".tmp", index=False)
    os.replace(path + ".tmp", path)
    return table


def single_protein_targets():
    """List every ChEMBL target that is one single protein.

    ChEMBL also has cell lines, tissues and protein complexes as targets. Only single
    proteins can be compared with our proteins by sequence.

    Returns
    -------
    pandas.DataFrame
        Columns `target_chembl_id`, `pref_name`, `organism` and `accession` (the
        UniProt accession of the protein).
    """
    def build():
        params = {"target_type": "SINGLE PROTEIN",
                  "only": "target_chembl_id,pref_name,organism,target_components"}
        rows = []
        for t in paged("target", "targets", params, desc="ChEMBL targets"):
            components = t.get("target_components") or [{}]
            rows.append({"target_chembl_id": t["target_chembl_id"],
                         "pref_name": t.get("pref_name"),
                         "organism": t.get("organism"),
                         "accession": components[0].get("accession")})
        return pd.DataFrame(rows).dropna(subset=["accession"])

    return _cached("chembl_single_protein_targets.csv", build)


def targets_for_accession(accession):
    """Find the ChEMBL targets that are exactly one protein.

    Parameters
    ----------
    accession : str
        UniProt accession, e.g. `P9WGR1`.

    Returns
    -------
    pandas.DataFrame
        One row per ChEMBL target holding that protein, with its type and organism.
        Empty if ChEMBL has never studied it.
    """
    params = {"target_components__accession": accession,
              "only": "target_chembl_id,pref_name,organism,target_type"}
    return pd.DataFrame(list(paged("target", "targets", params)))


def live_compounds(target_chembl_id, pchembl_min=5):
    """Ask ChEMBL, right now, which compounds were tested on one target.

    Parameters
    ----------
    target_chembl_id : str
        ChEMBL target identifier, e.g. `CHEMBL1849`.
    pchembl_min : float, optional
        Only activities with at least this pChEMBL value are counted.

    Returns
    -------
    set of str
        The identifier of every compound, each one only once.
    """
    params = {"target_chembl_id": target_chembl_id, "pchembl_value__gte": pchembl_min,
              "only": "molecule_chembl_id"}
    return {r["molecule_chembl_id"] for r in paged("activity", "activities", params)}


def target_sequences(accessions=None):
    """Return the amino acid sequence of every ChEMBL protein target.

    Parameters
    ----------
    accessions : set of str, optional
        Keep only these accessions. Everything is kept if this is None.

    Returns
    -------
    pandas.DataFrame
        Columns `accession`, `organism` and `sequence`.
    """
    def build():
        rows = []
        params = {"only": "accession,organism,sequence,component_type"}
        for c in paged("target_component", "target_components", params,
                       desc="ChEMBL sequences"):
            if c.get("component_type") == "PROTEIN" and c.get("sequence"):
                rows.append({"accession": c["accession"], "organism": c.get("organism"),
                             "sequence": c["sequence"]})
        return pd.DataFrame(rows).drop_duplicates(subset=["accession"])

    table = _cached("chembl_target_sequences.csv", build)
    if accessions is not None:
        table = table[table["accession"].isin(accessions)].reset_index(drop=True)
    return table.reset_index(drop=True)


def uniprot_sequences(accessions):
    """Download sequences from UniProt for a handful of accessions.

    Parameters
    ----------
    accessions : list of str
        UniProt accessions.

    Returns
    -------
    pandas.DataFrame
        Columns `uniprot_ac` and `sequence`, one row per accession found.
    """
    rows = []
    accessions = list(accessions)
    for start in range(0, len(accessions), 100):
        batch = accessions[start:start + 100]
        query = " OR ".join(f"accession:{a}" for a in batch)
        text = _get(UNIPROT_STREAM, {"query": query, "format": "fasta"}).text
        for block in ("\n" + text).split("\n>")[1:]:
            header, *lines = block.splitlines()
            rows.append({"uniprot_ac": header.split("|")[1], "sequence": "".join(lines)})
    return pd.DataFrame(rows)


def secondary_accessions(accessions):
    """Map old UniProt accessions to the current one.

    UniProt renumbered most *M. tuberculosis* proteins (`P0A5Y6` became `P9WGR1`, for
    example). ChEMBL entries made before that still carry the old accession, so a
    target of ours and its ChEMBL entry can look like two different proteins.

    Parameters
    ----------
    accessions : list of str
        Current UniProt accessions.

    Returns
    -------
    dict
        Old accession -> current accession.
    """
    alias = {}
    accessions = list(accessions)
    for start in range(0, len(accessions), 100):
        batch = accessions[start:start + 100]
        query = " OR ".join(f"accession:{a}" for a in batch)
        text = _get(UNIPROT_STREAM, {"query": query, "format": "txt"}).text
        # Each entry lists its accessions on one or more AC lines, current one first.
        current = None
        for line in text.splitlines():
            if line.startswith("ID   "):
                current = None
            elif line.startswith("AC   "):
                found = [a.strip() for a in line[5:].split(";") if a.strip()]
                if current is None:
                    current, found = found[0], found[1:]
                alias.update({old: current for old in found})
    return alias


def find_homologs(queries, subjects, evalue=1e-3, max_hits=1000, cpus=0):
    """Search every query protein against every subject protein.

    This is a first pass, made to be fast: it finds the proteins that are worth
    aligning properly, and misses very little. `phmmer` compares each query against
    all subjects in one go, which takes seconds rather than the hours a full
    all-against-all alignment would need.

    Parameters
    ----------
    queries : pandas.DataFrame
        Columns `uniprot_ac` and `sequence`.
    subjects : pandas.DataFrame
        Columns `accession` and `sequence`.
    evalue : float, optional
        Keep hits at least this significant. A larger number keeps more, weaker hits.
    max_hits : int, optional
        Keep at most this many hits per query, best first. Some proteins, such as the
        ribosomal ones, have relatives in thousands of organisms, and the weakest of
        them are never going to pass the identity cutoffs.
    cpus : int, optional
        Processor cores to use. 0 means all of them.

    Returns
    -------
    pandas.DataFrame
        One row per (query, subject) candidate, with columns `uniprot_ac`,
        `accession` and `evalue`.
    """
    import pyhmmer

    alphabet = pyhmmer.easel.Alphabet.amino()

    def block(names, seqs):
        digital = [pyhmmer.easel.TextSequence(name=n.encode(), sequence=s).digitize(alphabet)
                   for n, s in zip(names, seqs)]
        return pyhmmer.easel.DigitalSequenceBlock(alphabet, digital)

    def text(name):
        return name.decode() if isinstance(name, bytes) else str(name)

    targets = block(subjects["accession"], subjects["sequence"])
    query_block = block(queries["uniprot_ac"], queries["sequence"])
    rows = []
    for hits in pyhmmer.hmmer.phmmer(query_block, targets, E=evalue, cpus=cpus):
        query = text(hits.query.name)
        for hit in list(hits)[:max_hits]:
            if hit.evalue <= evalue:
                rows.append({"uniprot_ac": query, "accession": text(hit.name),
                             "evalue": hit.evalue})
    return pd.DataFrame(rows)


def global_identity(query, subject):
    """Align two proteins end to end and measure how identical they are.

    Identity is the number of positions where the two proteins have the same amino
    acid, divided by the length of the alignment (gaps included). Coverage is the
    part of each protein that the alignment actually matches up, which is what tells
    a whole protein apart from a single domain of it.

    Parameters
    ----------
    query, subject : str
        Amino acid sequences.

    Returns
    -------
    dict
        `identity`, `query_coverage` and `subject_coverage`, each between 0 and 1.
    """
    aligner = _aligner()
    alignment = aligner.align(_clean(query), _clean(subject))[0]
    q, s = alignment[0], alignment[1]
    same = sum(a == b for a, b in zip(q, s) if a != "-" and b != "-")
    aligned = sum(a != "-" and b != "-" for a, b in zip(q, s))
    return {"identity": same / len(q),
            "query_coverage": aligned / len(query),
            "subject_coverage": aligned / len(subject)}


def _clean(sequence):
    """Replace anything that is not one of the 20 amino acids with an X.

    A few database entries contain unusual letters, such as `U` for selenocysteine
    or `*` for the end of the protein. The scoring table does not know them, and X
    means "some amino acid", which is exactly what we want here.
    """
    known = set(_aligner().substitution_matrix.alphabet)
    return "".join(c if c in known else "X" for c in sequence.upper())


def _aligner():
    """Return the pairwise aligner, built once and reused.

    BLOSUM62 with a gap penalty of 11 to open and 1 to extend is the standard choice
    for comparing proteins; it is what BLAST uses by default.
    """
    global _ALIGNER
    if _ALIGNER is None:
        from Bio import Align
        from Bio.Align import substitution_matrices

        aligner = Align.PairwiseAligner(mode="global")
        aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
        aligner.open_gap_score, aligner.extend_gap_score = -11, -1
        _ALIGNER = aligner
    return _ALIGNER


_ALIGNER = None


def align_pairs(pairs, queries, subjects, workers=4, desc="Aligning"):
    """Measure identity and coverage for every candidate pair.

    Parameters
    ----------
    pairs : pandas.DataFrame
        Columns `uniprot_ac` and `accession`, as returned by `find_homologs`.
    queries : pandas.DataFrame
        Columns `uniprot_ac` and `sequence`.
    subjects : pandas.DataFrame
        Columns `accession` and `sequence`.
    workers : int, optional
        Alignments to run at the same time.
    desc : str, optional
        Label for the progress bar.

    Returns
    -------
    pandas.DataFrame
        `pairs` with `identity`, `query_coverage` and `subject_coverage` added.
    """
    q_seq = dict(zip(queries["uniprot_ac"], queries["sequence"]))
    s_seq = dict(zip(subjects["accession"], subjects["sequence"]))
    jobs = list(zip(pairs["uniprot_ac"], pairs["accession"]))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        scores = list(tqdm(pool.map(lambda j: global_identity(q_seq[j[0]], s_seq[j[1]]), jobs),
                           total=len(jobs), desc=desc, unit="pair"))
    return pd.concat([pairs.reset_index(drop=True), pd.DataFrame(scores)], axis=1)


def homolog_table(queries, subjects, evalue=1e-3, max_hits=1000, min_length_ratio=0.5,
                  cache="homolog_pairs.csv"):
    """Find the relatives of every query protein and measure how similar they are.

    Two steps: `phmmer` finds the proteins worth looking at, then every surviving
    pair is aligned end to end by `global_identity`, which is the number the tiers
    are built on. Pairs where the ChEMBL protein is far too short to cover the query
    are dropped before aligning, since they could never pass the coverage cutoff.

    The result is cached, so running the notebook again costs nothing.

    Parameters
    ----------
    queries : pandas.DataFrame
        Columns `uniprot_ac` and `sequence`.
    subjects : pandas.DataFrame
        Columns `accession` and `sequence`.
    evalue, max_hits : float, int, optional
        Passed to `find_homologs`.
    min_length_ratio : float, optional
        Drop a pair when the ChEMBL protein is shorter than this fraction of ours.
    cache : str, optional
        File name under `data/downloads/chembl/`.

    Returns
    -------
    pandas.DataFrame
        Columns `uniprot_ac`, `accession`, `evalue`, `identity`, `query_coverage`
        and `subject_coverage`.
    """
    def build():
        pairs = find_homologs(queries, subjects, evalue=evalue, max_hits=max_hits)
        q_len = queries.set_index("uniprot_ac")["sequence"].str.len()
        s_len = subjects.set_index("accession")["sequence"].str.len()
        long_enough = (pairs["accession"].map(s_len)
                       >= min_length_ratio * pairs["uniprot_ac"].map(q_len))
        return align_pairs(pairs[long_enough].reset_index(drop=True), queries, subjects)

    return _cached(cache, build)


def _live_pairs(target_ids, pchembl_min, batch_size=40, workers=4):
    """Ask ChEMBL for the compounds of some targets, a few targets per request."""
    os.makedirs(CACHE_FOLDER, exist_ok=True)
    batches = [target_ids[i:i + batch_size] for i in range(0, len(target_ids), batch_size)]

    def batch(ids):
        name = os.path.join(CACHE_FOLDER, f"pairs_{hash(tuple(ids)) & 0xffffffff:08x}.csv")
        if os.path.exists(name):
            return pd.read_csv(name)
        params = {"target_chembl_id__in": ",".join(ids), "pchembl_value__gte": pchembl_min,
                  "only": "molecule_chembl_id,target_chembl_id"}
        rows = [(r["target_chembl_id"], r["molecule_chembl_id"])
                for r in paged("activity", "activities", params)]
        table = pd.DataFrame(rows, columns=["target_chembl_id", "molecule_chembl_id"])
        table.to_csv(name + ".tmp", index=False)
        os.replace(name + ".tmp", name)
        return table

    with ThreadPoolExecutor(max_workers=workers) as pool:
        tables = list(tqdm(pool.map(batch, batches), total=len(batches),
                           desc="ChEMBL compounds", unit="batch"))
    return pd.concat(tables, ignore_index=True) if tables else pd.DataFrame(
        columns=["target_chembl_id", "molecule_chembl_id"])


def precedent_pairs(target_ids, pchembl_min=5):
    """Return every (target, compound) pair for a list of ChEMBL targets.

    The pairs are downloaded from ChEMBL, a few targets per request, and cached under
    `data/downloads/chembl/`, so an interrupted run carries on where it stopped and a
    second run costs nothing.

    Parameters
    ----------
    target_ids : iterable of str
        ChEMBL target identifiers, e.g. `CHEMBL1849`.
    pchembl_min : float, optional
        Only activities with at least this pChEMBL value are counted.

    Returns
    -------
    pandas.DataFrame
        Columns `target_chembl_id` and `molecule_chembl_id`, without duplicates.
    """
    target_ids = sorted(set(target_ids))
    pairs = _live_pairs(target_ids, pchembl_min)
    return pairs.drop_duplicates().reset_index(drop=True)
