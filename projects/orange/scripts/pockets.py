"""Helper functions for the orange group's pocket detection notebook.

P2Rank is a Java program, not a Python package, so running it from a notebook takes
some plumbing: finding (or installing) Java, downloading P2Rank once, writing the list
of structures it should read, and gathering its one-file-per-protein output back into
a single table. That plumbing lives here. What the scores mean, and what to do with
them, is left in the notebook.
"""

import glob
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request

import gemmi
import pandas as pd

P2RANK_VERSION = "2.5.1"
P2RANK_URL = (f"https://github.com/rdk/p2rank/releases/download/{P2RANK_VERSION}/"
              f"p2rank_{P2RANK_VERSION}.tar.gz")
P2RANK_FOLDER = "data/downloads"
# P2Rank needs Java 17 or newer. This is where apt puts it on Colab.
COLAB_JAVA_HOME = "/usr/lib/jvm/java-17-openjdk-amd64"


def _java_version(java):
    """Return the major version of a Java executable, or 0 if it does not run."""
    try:
        result = subprocess.run([java, "-version"], capture_output=True, text=True)
    except OSError:
        return 0
    # Java prints e.g. `openjdk version "17.0.18" 2026-01-20` to stderr.
    for word in result.stderr.split():
        if word.startswith('"'):
            return int(word.strip('"').split(".")[0])
    return 0


def find_java():
    """Find a Java 17 or newer, installing it first if on Colab.

    Returns
    -------
    str
        The Java home folder, the one that contains `bin/java`.

    Raises
    ------
    RuntimeError
        Outside Colab, if no suitable Java is installed.
    """
    candidates = [os.environ.get("JAVA_HOME"), COLAB_JAVA_HOME]
    java = shutil.which("java")
    if java:
        candidates.append(os.path.dirname(os.path.dirname(os.path.realpath(java))))
    for home in filter(None, candidates):
        if _java_version(os.path.join(home, "bin", "java")) >= 17:
            return home
    if "google.colab" not in sys.modules:
        raise RuntimeError("P2Rank needs Java 17 or newer. Install it, e.g. "
                           "`conda install -c conda-forge openjdk=17`.")
    subprocess.run(["apt-get", "install", "-y", "-qq", "openjdk-17-jre-headless"],
                   check=True, capture_output=True)
    return COLAB_JAVA_HOME


def install_p2rank(folder=P2RANK_FOLDER):
    """Download and unpack P2Rank, unless it is already there.

    The download is about 275 MB, so it happens once per runtime. `data/downloads/`
    is not committed to the repository.

    Parameters
    ----------
    folder : str, optional
        Where to put P2Rank.

    Returns
    -------
    str
        Path to the `prank` program.
    """
    prank = os.path.join(folder, f"p2rank_{P2RANK_VERSION}", "prank")
    if not os.path.exists(prank):
        os.makedirs(folder, exist_ok=True)
        archive = os.path.join(folder, f"p2rank_{P2RANK_VERSION}.tar.gz")
        if not os.path.exists(archive):
            urllib.request.urlretrieve(P2RANK_URL, archive)
        with tarfile.open(archive) as tar:
            tar.extractall(folder)
        os.remove(archive)
    return prank


def run_p2rank(prank, files, out_dir, config=None, threads=2):
    """Run P2Rank on a list of structure files in one go.

    Starting Java takes a few seconds, so P2Rank is given all the files at once in a
    dataset file (`.ds`, one path per line) rather than being called once per protein.

    Parameters
    ----------
    prank : str
        Path to the `prank` program, from `install_p2rank`.
    files : list of str
        Structure files (PDB format).
    out_dir : str
        Folder for the results. P2Rank writes a `<file>_predictions.csv` here for
        every structure.
    config : str, optional
        A P2Rank profile. `alphafold` is the one for predicted structures, cryo-EM
        and NMR; None uses the default, trained on X-ray crystal structures.
    threads : int, optional
        How many structures to work on at the same time.

    Returns
    -------
    str
        `out_dir`.
    """
    os.makedirs(out_dir, exist_ok=True)
    dataset = os.path.join(out_dir, "structures.ds")
    with open(dataset, "w") as f:
        f.write("\n".join(os.path.abspath(p) for p in files) + "\n")
    command = ["bash", prank, "predict", dataset, "-o", out_dir,
               "-threads", str(threads), "-visualizations", "0"]
    if config:
        command += ["-c", config]
    env = dict(os.environ, JAVA_HOME=find_java())
    result = subprocess.run(command, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"P2Rank failed:\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}")
    return out_dir


def read_predictions(out_dir):
    """Gather P2Rank's per-protein prediction files into one table.

    Parameters
    ----------
    out_dir : str
        A folder written by `run_p2rank`.

    Returns
    -------
    pandas.DataFrame
        One row per pocket, with `uniprot_ac` and `structure_source` (taken from the
        file name) plus P2Rank's columns: `rank`, `score`, `probability`,
        `sas_points`, `surf_atoms`, `center_x`, `center_y`, `center_z` and
        `residue_ids`. Proteins with no pocket at all have no rows.
    """
    tables = []
    for path in sorted(glob.glob(os.path.join(out_dir, "*_predictions.csv"))):
        # P2Rank pads its columns with spaces so the file lines up in a text editor.
        df = pd.read_csv(path, skipinitialspace=True)
        if df.empty:
            continue
        df.columns = df.columns.str.strip()
        name = os.path.basename(path).removesuffix(".pdb_predictions.csv")
        df["uniprot_ac"], df["structure_source"] = name.split("_")
        tables.append(df)
    pockets = pd.concat(tables, ignore_index=True)
    columns = ["uniprot_ac", "structure_source", "rank", "score", "probability",
               "sas_points", "surf_atoms", "center_x", "center_y", "center_z",
               "residue_ids"]
    return pockets[columns]


def pocket_plddt(structure_file, residue_ids):
    """Average AlphaFold confidence (pLDDT) of the residues lining one pocket.

    AlphaFold stores its confidence in each atom's B-factor column, from 0 to 100.

    Parameters
    ----------
    structure_file : str
        An AlphaFold model.
    residue_ids : str
        P2Rank's residue list, e.g. `A_103 A_14 A_147`.

    Returns
    -------
    float
        Mean pLDDT over the pocket's residues.
    """
    chain = gemmi.read_structure(structure_file)[0][0]
    plddt = {residue.seqid.num: residue[0].b_iso for residue in chain}
    numbers = [int(r.split("_")[1]) for r in residue_ids.split()]
    return sum(plddt[n] for n in numbers) / len(numbers)


def summarise(pockets, min_probability=0.5):
    """One row per protein, describing its pockets.

    Parameters
    ----------
    pockets : pandas.DataFrame
        As returned by `read_predictions`.
    min_probability : float, optional
        The probability above which a pocket counts as likely to bind a ligand.

    Returns
    -------
    pandas.DataFrame
        `uniprot_ac`, `n_pockets`, `n_likely_pockets` (probability at least
        `min_probability`), and the `top_score`, `top_probability` and
        `top_residues` of the best pocket.
    """
    top = pockets.sort_values("rank").drop_duplicates("uniprot_ac")
    counts = pockets.groupby("uniprot_ac").agg(
        n_pockets=("rank", "size"),
        n_likely_pockets=("probability", lambda p: int((p >= min_probability).sum())),
    )
    top = top.set_index("uniprot_ac")[["score", "probability", "residue_ids"]]
    top.columns = ["top_score", "top_probability", "top_residues"]
    return counts.join(top).reset_index()
