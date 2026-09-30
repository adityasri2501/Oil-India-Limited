"""Supervised model trained only from explicitly uploaded measured well records."""
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error

FEATURES = ["steam_tonnes", "steam_temp_c", "soak_hours", "spm", "stroke_m"]
TARGET = "oil_rate_m3d"
DATA_DIR = Path(os.getenv("PS120_DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
MODEL_PATH = DATA_DIR / "measured_well_model.joblib"
META_PATH = DATA_DIR / "measured_well_model.json"
DATA_PATH = DATA_DIR / "measured_well_records.csv"

def status():
    if not META_PATH.exists():
        return {"trained": False, "provenance": "No measured well dataset uploaded", "required_columns": FEATURES + [TARGET], "minimum_rows": 30}
    return json.loads(META_PATH.read_text(encoding="utf-8"))

def train(csv_text: str):
    try:
        frame = pd.read_csv(pd.io.common.StringIO(csv_text))
    except Exception as exc:
        raise ValueError(f"Could not read CSV: {exc}") from exc
    missing = [column for column in ["timestamp"] + FEATURES + [TARGET] if column not in frame.columns]
    if missing:
        raise ValueError("Missing required measured columns: " + ", ".join(missing))
    if "well_id" in frame.columns and frame["well_id"].dropna().nunique() > 1:
        raise ValueError("Upload one well per training file so the evaluation measures out-of-time performance for that well")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    numeric = frame[FEATURES + [TARGET]].apply(pd.to_numeric, errors="coerce")
    valid = numeric.notna().all(axis=1) & (numeric[FEATURES] >= 0).all(axis=1) & (numeric[TARGET] > 0)
    frame = frame.loc[valid].reset_index(drop=True)
    numeric = numeric.loc[valid].reset_index(drop=True)
    if len(frame) < 30:
        raise ValueError(f"At least 30 valid measured rows are required after cleaning; found {len(frame)}")
    # Keep the final 20% out of training for honest, chronological evaluation.
    cut = max(1, int(len(frame) * .8))
    train_frame, test_frame = numeric.iloc[:cut], numeric.iloc[cut:]
    if len(test_frame) < 3:
        raise ValueError("Need at least 3 holdout rows; upload at least 30 records")
    model = RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=120, n_jobs=-1)
    model.fit(train_frame[FEATURES], train_frame[TARGET])
    pred = model.predict(test_frame[FEATURES])
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(DATA_PATH, index=False)
    joblib.dump(model, MODEL_PATH)
    meta = {"trained": True, "provenance": "User-uploaded measured well records", "rows_used": int(len(frame)),
      "training_rows": int(len(train_frame)), "holdout_rows": int(len(test_frame)), "features": FEATURES,
      "target": TARGET, "evaluation": {"mae_m3d": round(float(mean_absolute_error(test_frame[TARGET], pred)), 4),
      "rmse_m3d": round(float(root_mean_squared_error(test_frame[TARGET], pred)), 4),
      "r2": round(float(r2_score(test_frame[TARGET], pred)), 4)},
      "note": "Validation uses the last 20% of supplied rows. Sort the CSV chronologically before upload. This model is not used to calibrate the physics simulator."}
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta

def predict(inputs: dict):
    meta = status()
    if not meta.get("trained"):
        raise ValueError("Upload measured well records and train the model first")
    model = joblib.load(MODEL_PATH)
    row = [[float(inputs[key]) for key in FEATURES]]
    return {"predicted_oil_rate_m3d": round(float(model.predict(row)[0]), 3), "provenance": meta["provenance"], "model_metrics": meta["evaluation"]}
