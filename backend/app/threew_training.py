"""Separate event-classifier baseline for Petrobras 3W real offshore well episodes.

This is not a Baghewala production-response model and must never be applied to
the synthetic BGW simulator state. Training only includes WELL-* parquet files
from the official 3W v2 folder; SIMULATED_* and DRAWN_* examples are excluded.
"""
import json
import os
from io import BytesIO
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.model_selection import GroupShuffleSplit

DATA_DIR = Path(os.getenv("PS120_DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
DATASET_DIR = Path(os.getenv("PS120_3W_DATASET_DIR", Path(__file__).resolve().parents[2] / "datasets" / "3w-2.0.0"))
MODEL_PATH = DATA_DIR / "threew_event_model.joblib"
META_PATH = DATA_DIR / "threew_event_model.json"


def status():
    result = {"trained": False, "dataset": "Petrobras 3W Dataset 2.0.0", "dataset_available": DATASET_DIR.exists(),
              "dataset_path": str(DATASET_DIR), "training_scope": "Real WELL-* episodes only; simulated and hand-drawn instances excluded",
              "model_scope": "Offshore well event classification; not Baghewala CSS production prediction"}
    if META_PATH.exists():
        result.update(json.loads(META_PATH.read_text(encoding="utf-8")))
    return result


def _summarize(frame: pd.DataFrame):
    # Per-instance features avoid treating adjacent 1 Hz samples as independent
    # train/test observations. The split is further grouped by physical well.
    numeric = frame.select_dtypes(include=[np.number]).drop(columns=["class", "state"], errors="ignore")
    numeric = numeric.replace([np.inf, -np.inf], np.nan)
    features = {}
    for name in numeric.columns:
        values = numeric[name].dropna()
        if values.empty:
            continue
        features[f"{name}__mean"] = float(values.mean())
        features[f"{name}__std"] = float(values.std(ddof=0))
        features[f"{name}__q10"] = float(values.quantile(.1))
        features[f"{name}__q90"] = float(values.quantile(.9))
    labels = pd.to_numeric(frame.get("class"), errors="coerce").dropna()
    return features, int(labels.mode().iloc[0]) if len(labels) else None


def train():
    if not DATASET_DIR.exists():
        raise ValueError(f"3W dataset folder not found at {DATASET_DIR}. Download/extract the official 3W Dataset 2.0.0 and set PS120_3W_DATASET_DIR.")
    paths = sorted(path for path in DATASET_DIR.rglob("*.parquet") if path.name.startswith("WELL-"))
    if not paths:
        raise ValueError("No real WELL-*.parquet episodes found. Point PS120_3W_DATASET_DIR at the extracted 3W dataset root.")

    records, failures = [], 0
    for path in paths:
        try:
            frame = pd.read_parquet(path)
            features, label = _summarize(frame)
            if label is None or not features:
                failures += 1
                continue
            # WELL-00014_<timestamp>.parquet -> physical well group WELL-00014
            well_group = path.stem.split("_")[0]
            records.append({"well_group": well_group, "label": label, **features})
        except Exception:
            failures += 1
    if len(records) < 12 or len({r["well_group"] for r in records}) < 4:
        raise ValueError(f"Need at least 12 readable real episodes across 4 wells; found {len(records)} episodes across {len({r['well_group'] for r in records})} wells.")

    table = pd.DataFrame(records)
    feature_cols = sorted(column for column in table.columns if column not in {"well_group", "label"})
    x = table[feature_cols].replace([np.inf, -np.inf], np.nan)
    x = x.fillna(x.median()).fillna(0)
    y = table["label"].astype(int)
    groups = table["well_group"]
    splitter = GroupShuffleSplit(n_splits=1, test_size=.25, random_state=120)
    train_idx, test_idx = next(splitter.split(x, y, groups))
    train_classes = set(y.iloc[train_idx])
    test_idx = np.asarray([i for i in test_idx if y.iloc[i] in train_classes], dtype=int)
    if len(train_classes) < 2:
        raise ValueError("The real-well training split contains fewer than two event classes. No meaningful event classifier can be trained from this split.")
    if len(test_idx) < 2:
        raise ValueError("The well-group holdout has too few classes represented in training to evaluate. Add/retain more real wells; do not mix in simulated examples to inflate coverage.")
    model = RandomForestClassifier(n_estimators=350, min_samples_leaf=2, class_weight="balanced_subsample", random_state=120, n_jobs=-1)
    model.fit(x.iloc[train_idx], y.iloc[train_idx])
    predicted = model.predict(x.iloc[test_idx])
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": feature_cols, "medians": x.iloc[train_idx].median().to_dict()}, MODEL_PATH)
    meta = {"trained": True, "dataset": "Petrobras 3W Dataset 2.0.0 (CC BY 4.0)", "rows_used": len(table),
            "physical_wells": int(groups.nunique()), "training_episodes": len(train_idx), "holdout_episodes": len(test_idx),
            "holdout_wells": int(groups.iloc[test_idx].nunique()), "excluded_unreadable": failures,
            "event_classes": sorted(int(v) for v in y.unique()), "holdout_event_classes": sorted(int(v) for v in set(y.iloc[test_idx])),
            "holdout_episodes_excluded_unseen_classes": int(len(records) - len(train_idx) - len(test_idx)), "feature_count": len(feature_cols),
            "evaluation": {"accuracy": round(float(accuracy_score(y.iloc[test_idx], predicted)), 4),
                           "balanced_accuracy": round(float(balanced_accuracy_score(y.iloc[test_idx], predicted)), 4),
                           "macro_f1": round(float(f1_score(y.iloc[test_idx], predicted, average="macro", zero_division=0)), 4)},
            "provenance": "Official 3W v2 Parquet files, real WELL-* episodes only; group holdout by anonymized physical well ID.",
            "caveat": "Offshore Brazilian well events. The model is a research benchmark for event classification, not Baghewala CSS, production-rate prediction, or an operational risk score. Event coverage and holdout metrics depend on the real instances available in the downloaded release."}
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def predict_episode(raw: bytes, filename: str):
    if not filename.lower().startswith("well-"):
        raise ValueError("Choose an actual WELL-* instance file; SIMULATED_* and DRAWN_* samples are not accepted.")
    try:
        frame = pd.read_parquet(BytesIO(raw)) if filename.lower().endswith(".parquet") else pd.read_csv(BytesIO(raw))
    except Exception as exc:
        raise ValueError(f"Could not read the 3W episode: {exc}") from exc
    features, _ = _summarize(frame)
    if not features:
        raise ValueError("The episode has no numeric sensor observations.")
    if not MODEL_PATH.exists():
        raise ValueError("Train the 3W event model before classifying an episode.")
    bundle = joblib.load(MODEL_PATH)
    row = pd.DataFrame([features]).reindex(columns=bundle["features"])
    row = row.fillna(pd.Series(bundle["medians"])).fillna(0)
    model = bundle["model"]
    probabilities = model.predict_proba(row)[0]
    order = np.argsort(probabilities)[::-1]
    return {"predicted_event_class": int(model.classes_[order[0]]), "confidence": round(float(probabilities[order[0]]), 4),
            "class_probabilities": {str(int(model.classes_[i])): round(float(probabilities[i]), 4) for i in order},
            "scope": "Petrobras 3W offshore event labels; research benchmark only, not Baghewala risk."}
