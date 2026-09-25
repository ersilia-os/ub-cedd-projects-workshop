"""Score molecules against CpABC1 with the ligand half of SPRINT.

SPRINT (Adduri et al., arXiv 2411.15418, MLSB 2024, https://github.com/abhinadduri/panspecies-dti,
MIT licence) puts a protein and a molecule into the same 1024-dimensional space, so that
scoring a pair is a single cosine similarity.

The protein half is expensive: it needs foldseek and a 2.43 GB protein language model.
But for one fixed target it only ever produces one vector, so CpABC1's vector is computed
once and stored in `data/cpabc1_sprint_embedding.npy`. That leaves the notebook with just
the molecule half: a Morgan fingerprint and a small neural network whose weights are in
`data/sprint_drug_projector.pt`. Nothing to download, and it runs on a CPU.

**What the score does and does not mean.** Read this before using it.

It ranks molecules, and a higher score means SPRINT considers the molecule more likely to
interact. It is *not* a predicted binding affinity, and it is *not* specific to CpABC1. We
checked: the same 20-compound panel scored against human carbonic anhydrase II, a small
enzyme with no relationship to ABC transporters, separated known transporter inhibitors
from inert decoys just as well as CpABC1 did (+0.369 against +0.340). So most of what this
score responds to is the molecule, not the target. Treat it as a way to put a large list in
a sensible order, not as evidence that a molecule binds CpABC1.
"""

import numpy as np
import torch
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from torch import nn

FINGERPRINT_BITS = 2048
FINGERPRINT_RADIUS = 2
LATENT_DIM = 1024


class LargeDrugProjector(nn.Module):
    """The molecule network from SPRINT, copied so nothing has to be installed.

    Reproduced from `ultrafast/modules.py` in github.com/abhinadduri/panspecies-dti
    (MIT licence). The `forward` loop is kept exactly as written there, including one
    quirk: `non_linearity` is registered as a child module, so iterating `children()`
    applies it once after the last linear layer and then a second time as a layer in its
    own right. Tidying that up would change every number this produces.
    """

    def __init__(self, drug_dim=FINGERPRINT_BITS, latent_dim=LATENT_DIM,
                 activation=nn.LeakyReLU, dropout=0.05):
        super().__init__()
        self.linear1 = nn.Linear(drug_dim, 1260)
        self.drop1 = nn.Dropout(dropout)
        self.bn1 = nn.BatchNorm1d(1260)
        self.linear2 = nn.Linear(1260, latent_dim)
        self.drop2 = nn.Dropout(dropout)
        self.bn2 = nn.BatchNorm1d(latent_dim)
        self.linear3 = nn.Linear(latent_dim, latent_dim)
        self.drop3 = nn.Dropout(dropout)
        self.bn3 = nn.BatchNorm1d(latent_dim)
        self.linear4 = nn.Linear(latent_dim, latent_dim)
        self.non_linearity = activation()

    def forward(self, x):
        for layer in self.children():
            x = layer(x)
            if isinstance(layer, nn.Linear):
                x = self.non_linearity(x)
        return x


def load_projector(weights_path):
    """The trained molecule network, ready to use."""
    model = LargeDrugProjector()
    model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()  # switches dropout off and uses the stored batch-norm statistics
    return model


def fingerprint(smiles):
    """Morgan fingerprint, matching SPRINT's own settings.

    Returns None for a SMILES that RDKit cannot read, so the caller can count and report
    those rather than silently scoring a wrong molecule.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    # SPRINT canonicalises first; the fingerprint is the same either way, but this keeps
    # the two paths identical.
    mol = Chem.MolFromSmiles(Chem.MolToSmiles(mol, isomericSmiles=True))
    if mol is None:
        return None
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=FINGERPRINT_RADIUS, fpSize=FINGERPRINT_BITS)
    bits = np.zeros((FINGERPRINT_BITS,), dtype=np.float32)
    DataStructs.ConvertToNumpyArray(generator.GetFingerprint(mol), bits)
    return bits


def score_molecules(smiles_list, projector, target_embedding, batch_size=512):
    """Cosine similarity between each molecule and the target, in [-1, 1].

    Returns an array the same length as `smiles_list`, with NaN wherever RDKit could not
    read the SMILES. Batching keeps memory flat for long lists; batch-norm is in eval mode
    so the batch a molecule lands in does not change its score.
    """
    fingerprints = [fingerprint(s) for s in smiles_list]
    usable = [i for i, fp in enumerate(fingerprints) if fp is not None]
    scores = np.full(len(smiles_list), np.nan, dtype=np.float32)
    if not usable:
        return scores

    target = np.asarray(target_embedding, dtype=np.float32).reshape(-1)
    target_norm = np.linalg.norm(target)

    for start in range(0, len(usable), batch_size):
        chunk = usable[start:start + batch_size]
        x = torch.from_numpy(np.stack([fingerprints[i] for i in chunk]))
        with torch.no_grad():
            projected = projector(x).numpy()
        norms = np.linalg.norm(projected, axis=1) * target_norm
        scores[chunk] = (projected @ target) / np.maximum(norms, 1e-12)
    return scores
