"""Helper functions for the yellow group's ACE data curation notebook.

These are the steps that are too long to read comfortably inside a notebook cell:
reading four differently shaped files into one table, standardising molecules,
finding records that are copies of each other, and collapsing repeats. The decisions
(which records to trust, which cutoff to use) are left in the notebook.
"""

import os

import numpy as np
import pandas as pd

# Every file is turned into a table with these columns, whatever it looked like.
COLUMNS = ["source", "record_id", "depositor", "reference", "assay", "smiles_in",
           "endpoint", "relation_raw", "value", "units", "comment", "validity",
           "pchembl_db"]

# The order in which databases are trusted when two records are the same measurement.
SOURCES = ["chembl", "bindingdb", "pubchem", "manual"]

# Databases write the same idea in several ways. A missing relation means the value is
# an exact measurement.
RELATIONS = {
    "=": "=", "~": "=", "": "=",
    ">": ">", ">=": ">", ">>": ">",
    "<": "<", "<=": "<", "<<": "<",
}

# How many nanomolar one unit of each kind is worth.
UNIT_TO_NM = {"nM": 1.0, "pM": 1e-3, "uM": 1e3, "µM": 1e3, "mM": 1e6, "M": 1e9}

# Micrograms per millilitre is a mass, not a concentration of molecules, so it can
# only be converted once we know how heavy the molecule is.
MASS_UNITS = {"ug.mL-1", "ug ml-1", "ug/mL"}

# Comments that say a compound was tested and did nothing.
INACTIVE_COMMENTS = ["not active", "inactive", "no significant activity", "no activity"]

# What ChEMBL's `src_id` numbers mean, for the ones that appear in the ACE data.
CHEMBL_SOURCES = {"1": "ChEMBL (Scientific Literature)", "15": "ChEMBL (DrugMatrix)",
                  "37": "ChEMBL (BindingDB Patent Bioactivity Data)"}

PUBCHEM_API = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


def _read_table(path):
    """Read a CSV or TSV whatever its separator, with tidy lower_case column names."""
    with open(path, encoding="utf-8-sig") as handle:
        header = handle.readline()
    separator = max([",", ";", "\t"], key=header.count)
    frame = pd.read_csv(path, sep=separator, dtype=str, encoding="utf-8-sig")
    frame.columns = [c.strip().strip('"').lstrip("#").strip().lower().replace(" ", "_")
                     for c in frame.columns]
    return frame


def _require(frame, columns, path):
    absent = [c for c in columns if c not in frame]
    if absent:
        raise ValueError(f"{path} has no column called {' or '.join(absent)}. "
                         f"It has: {', '.join(sorted(frame.columns))}")


def load_chembl(path):
    """Read a ChEMBL activity export (website or programming interface).

    The website writes `Smiles` and `Comment` where the programming interface writes
    `canonical_smiles` and `activity_comment`, and it puts quotes around the relation
    ('='). Both versions are accepted.

    Parameters
    ----------
    path : str
        The CSV file downloaded from ChEMBL.

    Returns
    -------
    pandas.DataFrame
        One row per record, with the columns in `COLUMNS`.
    """
    t = _read_table(path).rename(columns={
        "smiles": "canonical_smiles", "comment": "activity_comment", "source_id": "src_id"})
    _require(t, ["canonical_smiles", "standard_type", "standard_relation",
                 "standard_value", "standard_units"], path)
    for column in ["activity_id", "src_id", "source_description", "document_chembl_id",
                   "assay_chembl_id", "molecule_chembl_id", "activity_comment",
                   "standard_text_value", "data_validity_comment", "pchembl_value"]:
        if column not in t:
            t[column] = pd.Series(np.nan, index=t.index, dtype=object)
    # The website export has no activity id, so a record is named by its assay, its
    # molecule and its row in the file instead.
    fallback = (t["assay_chembl_id"].fillna("") + ":" + t["molecule_chembl_id"].fillna("")
                + ":row" + t.index.astype(str))
    described = "ChEMBL (" + t["source_description"] + ")"
    return pd.DataFrame({
        "source": "chembl",
        "record_id": "chembl:" + t["activity_id"].fillna(fallback),
        "depositor": described.fillna(t["src_id"].map(CHEMBL_SOURCES))
                              .fillna("ChEMBL (other)"),
        "reference": t["document_chembl_id"],
        "assay": t["assay_chembl_id"],
        "smiles_in": t["canonical_smiles"],
        "endpoint": t["standard_type"],
        "relation_raw": t["standard_relation"].str.strip("'\" "),
        "value": t["standard_value"],
        "units": t["standard_units"],
        # The website export has both; ChEMBL often writes "Not active" in the text
        # value and the reason (e.g. "Inhibition < 50% @ 10 uM") in the comment.
        "comment": t["activity_comment"].str.cat(t["standard_text_value"], sep=" | ",
                                                 na_rep="").str.strip(" |")
                                        .replace("", np.nan),
        "validity": t["data_validity_comment"],
        "pchembl_db": t["pchembl_value"],
    })


def load_bindingdb(path):
    """Read a BindingDB target download (TSV) and put one measurement per row.

    BindingDB gives each type of measurement its own column (`Ki (nM)`, `IC50 (nM)`,
    ...), always in nanomolar, and writes limits inside the value (">10000"). The
    rows can be longer than the header, because the file ends with one block of
    columns per protein chain, so only the columns named in the header are read.
    """
    with open(path, encoding="utf-8-sig") as handle:
        header = handle.readline().rstrip("\r\n").split("\t")
        rows = [line.rstrip("\r\n").split("\t")[:len(header)] for line in handle]
    # dtype=object keeps empty columns as text; otherwise older pandas turns a column
    # with no values into numbers and the `.str` calls below fail.
    t = pd.DataFrame(rows, columns=header, dtype=object)
    t = t.mask(t == "", None).astype(object)
    _require(t, ["Ligand SMILES", "Curation/DataSource"], path)
    wide = {"Ki": "Ki (nM)", "IC50": "IC50 (nM)", "Kd": "Kd (nM)", "EC50": "EC50 (nM)"}
    pieces = []
    for endpoint, column in wide.items():
        part = t[t[column].notna()]
        if part.empty:
            continue
        raw = part[column].astype(str).str.strip()
        paper = ("pmid:" + part["PMID"]).fillna("doi:" + part["Article DOI"])
        pieces.append(pd.DataFrame({
            "source": "bindingdb",
            "record_id": "bindingdb:" + part["BindingDB Reactant_set_id"] + ":" + endpoint,
            "depositor": part["Curation/DataSource"],
            "reference": paper,
            "assay": np.nan,
            "smiles_in": part["Ligand SMILES"].str.split(" ").str[0],
            "endpoint": endpoint,
            "relation_raw": raw.str.extract(r"^([<>]=?)")[0],
            "value": raw.str.replace(r"^[<>]=?\s*", "", regex=True),
            "units": "nM",
            "comment": np.nan,
            "validity": np.nan,
            "pchembl_db": np.nan,
        }))
    return pd.concat(pieces, ignore_index=True)


def _pubchem_lookup(ids, kind, cache):
    """Fetch SMILES (for CIDs) or depositor names (for AIDs) from PubChem, cached."""
    import requests

    known = pd.read_csv(cache, dtype=str) if os.path.exists(cache) else pd.DataFrame()
    todo = sorted(set(ids) - set(known.get("id", [])), key=int)
    rows = []
    for start in range(0, len(todo), 200):
        chunk = ",".join(todo[start:start + 200])
        if kind == "cid":
            reply = requests.post(f"{PUBCHEM_API}/compound/cid/property/SMILES/JSON",
                                  data={"cid": chunk}, timeout=300).json()
            rows += [{"id": str(p["CID"]), "smiles": p.get("SMILES")}
                     for p in reply["PropertyTable"]["Properties"]]
        else:
            reply = requests.post(f"{PUBCHEM_API}/assay/aid/summary/JSON",
                                  data={"aid": chunk}, timeout=300).json()
            rows += [{"id": str(s["AID"]), "depositor": s["SourceName"],
                      "depositor_id": s.get("SourceID")}
                     for s in reply["AssaySummaries"]["AssaySummary"]]
    if rows:
        known = pd.concat([known, pd.DataFrame(rows)], ignore_index=True)
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        known.to_csv(cache, index=False)
    return known.set_index("id")


def load_pubchem(path, cache_dir="data/downloads"):
    """Read PubChem's bioactivity table for a protein and add SMILES and depositors.

    PubChem's table lists compounds by number (CID) and assays by number (AID). The
    structure of each compound and the name of whoever deposited each assay are
    fetched from PubChem once and kept in `cache_dir`, so this needs the internet the
    first time only.
    """
    t = _read_table(path).rename(columns={"activity_value_[um]": "value_um"})
    _require(t, ["aid", "sid", "cid", "activity_name", "value_um"], path)
    t = t[t["cid"].notna()]
    smiles = _pubchem_lookup(t["cid"], "cid", f"{cache_dir}/pubchem_smiles.csv")
    assays = _pubchem_lookup(t["aid"], "aid", f"{cache_dir}/pubchem_assays.csv")
    return pd.DataFrame({
        "source": "pubchem",
        "record_id": "pubchem:AID" + t["aid"] + ":SID" + t["sid"],
        "depositor": t["aid"].map(assays["depositor"]),
        "reference": "pmid:" + t["pubmed_id"],
        "assay": t["aid"].map(assays["depositor_id"]),
        "smiles_in": t["cid"].map(smiles["smiles"]),
        "endpoint": t["activity_name"],
        "relation_raw": t["activity_qualifier"],
        "value": t["value_um"],
        "units": "uM",
        "comment": t["activity_outcome"],
        "validity": np.nan,
        "pchembl_db": np.nan,
    }).reset_index(drop=True)


def load_manual(path):
    """Read the group's own curation table.

    Expected columns: `smiles`, `standard_type`, `standard_value`, `standard_unit`,
    and optionally `compound_id`, `source` (where the row was taken from) and
    `reference`.
    """
    t = _read_table(path)
    _require(t, ["smiles", "standard_type", "standard_value", "standard_unit"], path)
    for column in ["compound_id", "source", "reference"]:
        if column not in t:
            t[column] = pd.Series(np.nan, index=t.index, dtype=object)
    record = t["compound_id"].fillna(pd.Series(t.index.astype(str), index=t.index))
    return pd.DataFrame({
        "source": "manual",
        "record_id": "manual:" + record + ":" + t.index.astype(str),
        "depositor": t["source"].fillna("manual"),
        "reference": t["reference"],
        "assay": np.nan,
        "smiles_in": t["smiles"],
        "endpoint": t["standard_type"],
        "relation_raw": np.nan,
        "value": t["standard_value"],
        "units": t["standard_unit"],
        "comment": np.nan,
        "validity": np.nan,
        "pchembl_db": np.nan,
    })


def standardize_smiles(smiles_list):
    """Clean up a list of SMILES strings and give each molecule an identity code.

    A SMILES string is a way of writing a molecule as text. The same molecule can be
    written in several different SMILES, and databases often store it as a salt (the
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
        One row per input SMILES, with columns `smiles_in` (the input), `smiles`
        (cleaned), `inchikey` and `mw` (molecular weight in g/mol). Molecules that
        cannot be read are left out.
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
            "smiles_in": smiles,
            "smiles": Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True),
            "inchikey": Chem.MolToInchiKey(mol),
            "mw": round(Descriptors.MolWt(mol), 3),
        })
    return pd.DataFrame(rows)


def to_nanomolar(values, units, weights):
    """Convert measured concentrations to nanomolar.

    Units that cannot be converted (percentages, ratios) give NaN. Mass units
    (ug/mL) need the molecular weight: ug/mL is mg/L, and dividing by the weight in
    mg/mmol gives mmol/L, which is a million nanomolar.
    """
    factor = units.map(UNIT_TO_NM)
    by_mass = values / weights * 1e6
    return pd.Series(np.where(units.isin(MASS_UNITS), by_mass, values * factor),
                     index=values.index)


def pactivity(value_nm):
    """Turn a concentration in nanomolar into a pActivity (pChEMBL-style) value.

    pActivity is minus the base-10 logarithm of the concentration in molar. It turns
    a number where small means potent into one where large means potent: 1 nM is 9,
    1 uM is 6, 100 uM is 4.
    """
    return -np.log10(value_nm * 1e-9)


def says_inactive(comments):
    """True where a free-text comment says the compound was inactive."""
    text = comments.fillna("").str.lower()
    return text.apply(lambda s: any(word in s for word in INACTIVE_COMMENTS))


def copy_of(depositor, source):
    """Which database a record says it was copied from, or "" if none.

    ChEMBL is the reference, so its records are never copies. BindingDB says in
    `Curation/DataSource` when it took a record from ChEMBL; PubChem assays are
    deposited by ChEMBL or BindingDB; the group's manual table says where each row
    was taken from.
    """
    name = depositor.fillna("").str.lower()
    claimed = np.select([name.str.contains("chembl"), name.str.contains("bindingdb")],
                        ["chembl", "bindingdb"], default="")
    return pd.Series(np.where(source == "chembl", "", claimed), index=depositor.index)


def mark_copies(df, tolerance=0.05):
    """Decide, record by record, whether it repeats a measurement held elsewhere.

    Molecules are compared on connectivity (the first 14 characters of the
    InChIKey), because databases do not always agree on stereochemistry. Two records
    are the same measurement when they share molecule and endpoint and their
    pActivity differs by no more than `tolerance`. Records flagged as unusable are
    still used as originals here, so that a copy of a record ChEMBL flagged as
    doubtful is recognised as such.

    Adds `claimed_copy_of` (what the record says) and `copy_status`, one of:
    - "original": ChEMBL, or a record that does not repeat anything;
    - "confirmed copy": says it is a copy and the original is there, same value;
    - "copy of a flagged record": the same, but the original is flagged as doubtful;
    - "copy, value differs": says it is a copy, the original database has this
      molecule and endpoint, but not with this value (a possible transcription error);
    - "copy, original not found": says it is a copy, but the original database has
      no record for this molecule and endpoint in our download;
    - "duplicate": a database earlier in `SOURCES` holds the same molecule,
      endpoint and value, although the record does not say it was copied from it
      (or says it was copied from somewhere we could not find it).
    """
    df = df.copy()
    df["connectivity"] = df["inchikey"].str[:14]
    df["claimed_copy_of"] = copy_of(df["depositor"], df["source"])
    df["copy_status"] = "original"
    valued = df[df["pactivity"].notna()]

    def matches(rows, reference):
        pairs = rows.reset_index().merge(
            reference[["connectivity", "endpoint", "pactivity", "usable"]],
            on=["connectivity", "endpoint"], suffixes=("", "_ref"))
        pairs = pairs.assign(close=(pairs["pactivity"] - pairs["pactivity_ref"]).abs()
                             <= tolerance)
        close = pairs[pairs["close"]]
        clean = set(close.loc[close["usable_ref"], "index"])
        return set(pairs["index"]), set(close["index"]) - clean, clean

    for original in ["chembl", "bindingdb"]:
        claims = valued[valued["claimed_copy_of"] == original]
        present, flagged, same = matches(claims, valued[valued["source"] == original])
        df.loc[claims.index, "copy_status"] = "copy, original not found"
        df.loc[list(present), "copy_status"] = "copy, value differs"
        df.loc[list(flagged), "copy_status"] = "copy of a flagged record"
        df.loc[list(same), "copy_status"] = "confirmed copy"

    for rank, source in enumerate(SOURCES[1:], start=1):
        status = df.loc[valued.index, "copy_status"]
        rows = valued[(valued["source"] == source)
                      & status.isin(["original", "copy, original not found"])]
        _, flagged, same = matches(rows, valued[valued["source"].isin(SOURCES[:rank])])
        df.loc[list(flagged), "copy_status"] = "copy of a flagged record"
        df.loc[list(same), "copy_status"] = "duplicate"
    return df


# Records whose value we use: the originals, and copies whose original we lack.
TRUSTED = ["original", "copy, original not found"]


def overlap_regions(sets):
    """Count molecules in each region of a Venn diagram of any number of sets."""
    names = list(sets)
    everything = set().union(*sets.values())
    regions = pd.Series([tuple(m in sets[n] for n in names) for m in everything],
                        dtype=object).value_counts()
    rows = []
    for inside, count in regions.items():
        members = [n for n, flag in zip(names, inside) if flag]
        rows.append({"databases": " + ".join(members) + (" only" if len(members) == 1 else ""),
                     "n_databases": len(members), "molecules": count})
    return pd.DataFrame(rows).sort_values(["n_databases", "molecules"],
                                          ascending=[False, False]).reset_index(drop=True)


def summarise_replicates(df, key):
    """Collapse repeated exact measurements of the same molecule into one row.

    The median is used rather than the mean because one badly wrong number cannot
    drag it far.
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


def decisive_bounds(df, key, cutoff_nm):
    """Rescue molecules that only have a "greater than" or "less than" record.

    A bound is only worth keeping when it already falls on the decided side of the
    cutoff: with a cutoff of 1 uM, "> 50 uM" proves the molecule is inactive and
    "< 5 nM" proves it is active, but "> 100 nM" proves nothing either way.
    Molecules bounded from both sides at once are dropped.
    """
    lower = df[df["relation"] == ">"].groupby(key)["value_nm"].min()
    upper = df[df["relation"] == "<"].groupby(key)["value_nm"].max()
    inactive = lower[lower >= cutoff_nm]
    active = upper[upper <= cutoff_nm]
    both = inactive.index.intersection(active.index)
    bounded = pd.concat([
        pd.DataFrame({"pactivity": pactivity(inactive.drop(both)),
                      "evidence": "limit, inactive"}),
        pd.DataFrame({"pactivity": pactivity(active.drop(both)),
                      "evidence": "limit, active"}),
    ])
    bounded["n_exact"] = 0
    return bounded


def collapse(df, cutoff_nm):
    """One row per molecule and endpoint, from the records we trust.

    Exact values are summarised by their median. Molecules with no exact value are
    rescued from decisive limits and, failing that, from comments that say
    "inactive". Every record, copies included, is still listed in `record_ids`.
    """
    key = ["inchikey", "endpoint"]
    trusted = df[df["usable"] & df["copy_status"].isin(TRUSTED)]
    measured = summarise_replicates(trusted, key)
    measured["evidence"] = "measured"
    rest = trusted[~trusted.set_index(key).index.isin(measured.index)]
    bounded = decisive_bounds(rest, key, cutoff_nm)
    rest = rest[~rest.set_index(key).index.isin(bounded.index)]
    commented = rest[rest["comment_inactive"]].groupby(key).size().rename("n_exact") * 0
    commented = commented.to_frame().assign(pactivity=np.nan, evidence="comment, inactive")

    meta = df.groupby(key).agg(
        smiles=("smiles", "first"),
        sources=("source", lambda s: "+".join(x for x in SOURCES if x in set(s))),
        independent_sources=("source", lambda s: ""),
        record_ids=("record_id", lambda s: ";".join(sorted(s))),
    )
    independent = trusted.groupby(key)["source"].agg(
        lambda s: "+".join(x for x in SOURCES if x in set(s)))
    meta["independent_sources"] = independent.reindex(meta.index).fillna("")
    for source in SOURCES:
        meta[f"n_{source}"] = (df[df["source"] == source].groupby(key).size()
                               .reindex(meta.index).fillna(0).astype(int))
    out = meta.join(pd.concat([measured, bounded, commented]), how="inner")
    return out.reset_index()


def pactivity_or_nan(value_nm):
    """pActivity where the value is a positive number, NaN elsewhere."""
    return pactivity(value_nm.where(value_nm > 0))


def curate(tables, cutoff_nm, tolerance=0.05, endpoints=("IC50", "Ki")):
    """Run sections 2 to 5 of the notebook in one go on a list of loaded tables.

    Used to repeat the human curation on another species. Returns the records (with
    their flags and copy status) and one row per molecule and endpoint.
    """
    records = pd.concat(tables, ignore_index=True)
    records = records[records["endpoint"].isin(endpoints) & records["smiles_in"].notna()]
    structures = standardize_smiles(records["smiles_in"].unique())
    records = records.merge(structures, on="smiles_in", how="inner")
    records["value"] = pd.to_numeric(records["value"], errors="coerce")
    records["relation"] = records["relation_raw"].fillna("").str.strip().map(RELATIONS)
    records["value_nm"] = to_nanomolar(records["value"], records["units"], records["mw"])
    records["pactivity"] = pactivity_or_nan(records["value_nm"])
    records["comment_inactive"] = says_inactive(records["comment"])
    records["usable"] = (records["value_nm"].between(1e-3, 1e9)
                         & records["relation"].notna() & records["validity"].isna())
    records = mark_copies(records, tolerance)
    comment_only = ~records["usable"] & records["value_nm"].isna() & records["comment_inactive"]
    records.loc[comment_only, ["usable", "relation"]] = [True, "none"]
    return records, collapse(records, cutoff_nm)
