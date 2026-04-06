#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "rdkit>=2023.9.1",
#     "scikit-learn>=1.3.0",
#     "pandas>=2.0.0",
#     "numpy>=1.24.0",
#     "joblib>=1.3.0",
# ]
# ///
import csv
import os
from collections import defaultdict

import numpy as np
import pandas as pd
from joblib import dump
from rdkit import Chem, RDLogger, rdBase
from rdkit.Chem import AllChem
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    roc_auc_score,
)

rdBase.DisableLog("rdApp.error")
RDLogger.DisableLog("rdApp.*")

BASE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(BASE)
ETOXPRED = os.path.join(PARENT, "etoxpred")

CATEGORIES = {
    "carcinogen": os.path.join(PARENT, "training_data", "carcinogens.smi"),
    "psychoactive": os.path.join(PARENT, "training_data", "psychoactive_drugs.smi"),
    "endocrine_disruptor": os.path.join(PARENT, "training_data", "endocrine_disruptors.smi"),
}


def load_smi(path):
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) < 2:
                parts = line.split(" ", 1)
            if len(parts) >= 2:
                entries.append((parts[0], parts[1]))
    return entries


def smiles_to_fp(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=1024)
    arr = np.zeros(1024, dtype=np.float32)
    for bit in fp.GetOnBits():
        arr[bit] = 1.0
    return arr


def get_scaffold(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    try:
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception:
        return None


def scaffold_split(smiles_list, labels, test_size=0.2, seed=42):
    np.random.seed(seed)
    scaffold_to_indices = defaultdict(list)
    for i, smi in enumerate(smiles_list):
        scaffold = get_scaffold(smi)
        if scaffold is None:
            scaffold = f"__no_scaffold_{i}__"
        scaffold_to_indices[scaffold].append(i)
    scaffolds = list(scaffold_to_indices.keys())
    np.random.shuffle(scaffolds)
    train_indices = []
    test_indices = []
    test_count = 0
    target_test = int(len(smiles_list) * test_size)
    for scaffold in scaffolds:
        indices = scaffold_to_indices[scaffold]
        if test_count < target_test:
            test_indices.extend(indices)
            test_count += len(indices)
        else:
            train_indices.extend(indices)
    return train_indices, test_indices


def main():
    print("=" * 60)
    print("Training Custom Classifiers")
    print("=" * 60)

    smiles_to_categories = defaultdict(set)
    smiles_to_name = {}

    for cat, path in CATEGORIES.items():
        for smi, name in load_smi(path):
            smiles_to_categories[smi].add(cat)
            smiles_to_name[smi] = name
        print(
            f"Loaded {cat}: {sum(1 for s in smiles_to_categories if cat in smiles_to_categories[s])} compounds"
        )

    train_path = os.path.join(ETOXPRED, "training_set.smi")
    df = pd.read_csv(train_path, sep="\t", names=["smiles", "name", "label"])
    safe_smiles = set()
    for _, row in df[df["label"] == 0].iterrows():
        smi = row["smiles"]
        if smi not in smiles_to_categories:
            safe_smiles.add(smi)
            smiles_to_name[smi] = row["name"]
    print(f"Loaded FDA-safe baseline: {len(safe_smiles)} compounds")

    print("\nComputing fingerprints...")
    fp_cache = {}
    all_smiles = list(set(smiles_to_categories.keys()) | safe_smiles)
    total = len(all_smiles)
    for i, smi in enumerate(all_smiles):
        if i % 500 == 0:
            print(f"  Progress: {i}/{total}", flush=True)
        fp = smiles_to_fp(smi)
        if fp is not None:
            fp_cache[smi] = fp
    print(f"  {len(fp_cache)} valid fingerprints")

    models = {}

    for cat in CATEGORIES:
        print(f"\n{'=' * 60}")
        print(f"Training: {cat.upper()}")
        print("=" * 60)

        positives = [s for s in fp_cache if cat in smiles_to_categories[s]]
        negatives = [s for s in fp_cache if s in safe_smiles]

        print(f"  Positives: {len(positives)}")
        print(f"  Negatives (FDA-safe only): {len(negatives)}")

        np.random.seed(42)
        if len(negatives) > len(positives) * 2:
            negatives = list(np.random.choice(negatives, len(positives) * 2, replace=False))
            print(f"  Negatives (after balancing): {len(negatives)}")

        all_smi = positives + negatives
        labels = [1] * len(positives) + [0] * len(negatives)

        train_idx, test_idx = scaffold_split(all_smi, labels, test_size=0.2)

        X_train = np.array([fp_cache[all_smi[i]] for i in train_idx])
        y_train = np.array([labels[i] for i in train_idx])
        X_test = np.array([fp_cache[all_smi[i]] for i in test_idx])
        y_test = np.array([labels[i] for i in test_idx])

        print(f"\n  Train: {len(X_train)} ({sum(y_train)} pos, {len(y_train) - sum(y_train)} neg)")
        print(f"  Test:  {len(X_test)} ({sum(y_test)} pos, {len(y_test) - sum(y_test)} neg)")

        clf = ExtraTreesClassifier(
            n_estimators=400,
            min_samples_split=10,
            min_samples_leaf=3,
            max_features=15,
            random_state=42,
            n_jobs=-1,
        )
        clf.fit(X_train, y_train)

        y_test_pred = clf.predict(X_test)
        y_test_prob = clf.predict_proba(X_test)[:, 1]

        print("\n  TEST METRICS (scaffold split):")
        print(f"  Accuracy:  {accuracy_score(y_test, y_test_pred):.4f}")
        print(f"  ROC-AUC:   {roc_auc_score(y_test, y_test_prob):.4f}")
        print(f"  PR-AUC:    {average_precision_score(y_test, y_test_prob):.4f}")
        print(classification_report(y_test, y_test_pred, target_names=["Negative", "Positive"]))

        model_path = os.path.join(ETOXPRED, f"model_{cat}.joblib")
        dump(clf, model_path)
        models[cat] = clf
        print(f"  Saved: {model_path}")

    print(f"\n{'=' * 60}")
    print("Scoring all chemicals...")
    print("=" * 60)

    all_entries = []
    seen = set()

    for cat, path in CATEGORIES.items():
        for smi, name in load_smi(path):
            key = name.lower()
            if key not in seen:
                seen.add(key)
                all_entries.append((smi, name))

    noot_path = os.path.join(PARENT, "training_data", "nootropics.smi")
    if os.path.exists(noot_path):
        noot_count = 0
        for smi, name in load_smi(noot_path):
            key = name.lower()
            if key not in seen:
                seen.add(key)
                all_entries.append((smi, name))
                noot_count += 1
        print(f"  Added {noot_count} nootropics (not used in training)")

    print(f"  Total: {len(all_entries)} unique chemicals")

    results = []
    for smi, name in all_entries:
        fp = smiles_to_fp(smi)
        if fp is None:
            continue
        fp_2d = fp.reshape(1, -1)
        scores = {}
        for cat, clf in models.items():
            prob = clf.predict_proba(fp_2d)[:, 1][0]
            scores[cat] = prob
        results.append(
            {
                "name": name,
                "smiles": smi,
                "carcinogen_score": scores["carcinogen"],
                "psychoactive_score": scores["psychoactive"],
                "endocrine_score": scores["endocrine_disruptor"],
            }
        )

    out_path = os.path.join(ETOXPRED, "custom_scores.csv")
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "name",
                "smiles",
                "carcinogen_score",
                "psychoactive_score",
                "endocrine_score",
            ],
        )
        w.writeheader()
        w.writerows(results)
    print(f"  Wrote {len(results)} scored chemicals to {out_path}")
    print("\nDONE")


if __name__ == "__main__":
    main()
