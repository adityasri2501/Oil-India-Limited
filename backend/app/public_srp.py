"""External SRP telemetry benchmark from the Hugging Face NK field dataset.

The source is not Baghewala data and does not include production or CSS labels.
It is used only for next-hour SRP sensor forecasting and data-quality review.
"""
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import mean_absolute_error

DATA_DIR = Path(os.getenv("PS120_DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
DATASET_PATH = Path(os.getenv("PS120_PUBLIC_SRP_DATASET", Path(__file__).resolve().parents[2] / "datasets" / "hf_nk_oil_well_sensor_monitoring" / "wells_dataset.csv")).resolve()
MODEL_PATH = DATA_DIR / "public_srp_forecaster.joblib"
META_PATH = DATA_DIR / "public_srp_forecaster.json"
SOURCE = "Arailym Tleubayeva, Oil Well Sensor Monitoring Dataset: NK Field (Hugging Face; Apache-2.0)"
SOURCE_URL = "https://huggingface.co/datasets/Arailym-tleubayeva/NK-Oil-Well-Sensor-Monitoring"
FEATURES = ["SPM", "pump_fillage", "min_rod_weight", "max_rod_weight"]


def _read():
    if not DATASET_PATH.is_file():
        raise ValueError(f"Public SRP dataset file is missing: {DATASET_PATH}")
    frame = pd.read_csv(DATASET_PATH)
    required = {"well_id", "well_type", "timestamp", "parameter", "value"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("Public SRP file is missing columns: " + ", ".join(sorted(missing)))
    frame = frame.loc[frame["well_type"].eq("sucker_rod_pump")].copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame.dropna(subset=["well_id", "timestamp", "parameter", "value"])
    wide = frame.pivot_table(index=["well_id", "timestamp"], columns="parameter", values="value", aggfunc="last").reset_index()
    for feature in FEATURES:
        if feature not in wide:
            wide[feature] = np.nan
    wide = wide.sort_values(["well_id", "timestamp"])
    return frame, wide


def status():
    result = {"trained": MODEL_PATH.is_file() and META_PATH.is_file(), "dataset_available": DATASET_PATH.is_file(), "dataset_path": str(DATASET_PATH),
              "source": SOURCE, "source_url": SOURCE_URL, "license": "Apache-2.0",
              "scope": "External sucker-rod pump telemetry benchmark; not Baghewala and not CSS/production response.",
              "caveats": ["Dataset card says timestamps were assigned to 2026 from source-file ordering; verify against original SCADA before time-sensitive use.",
                          "No oil-rate, CSS-cycle, failure, or pump-unsetting labels are provided.",
                          "The source documents extreme dynamometer-area values; that field is excluded from this model."],
              "model_path": str(MODEL_PATH)}
    if META_PATH.exists():
        result.update(json.loads(META_PATH.read_text(encoding="utf-8")))
        result["dataset_available"] = DATASET_PATH.is_file()
        result["dataset_path"] = str(DATASET_PATH)
    return result


def train():
    raw, wide = _read()
    # Keep physically plausible rows for this forecast benchmark; preserve the
    # untouched source CSV and report all exclusions in model metadata.
    valid = wide[FEATURES].notna().all(axis=1)
    valid &= wide["SPM"].between(0.1, 12) & wide["pump_fillage"].between(0, 100)
    valid &= wide["min_rod_weight"].ge(0) & wide["max_rod_weight"].ge(wide["min_rod_weight"])
    clean = wide.loc[valid].copy()
    pairs = []
    for well_id, group in clean.groupby("well_id", sort=True):
        group = group.sort_values("timestamp").reset_index(drop=True)
        gap = group["timestamp"].diff().eq(pd.Timedelta(hours=1))
        for lag in range(3):
            for name in FEATURES:
                group[f"lag{lag + 1}_{name}"] = group[name].shift(lag)
        group["next_timestamp"] = group["timestamp"].shift(-1)
        for name in FEATURES:
            group[f"target_{name}"] = group[name].shift(-1)
        pair_ok = gap & gap.shift(1, fill_value=False) & group["next_timestamp"].sub(group["timestamp"]).eq(pd.Timedelta(hours=1))
        pairs.append(group.loc[pair_ok].copy())
    table = pd.concat(pairs, ignore_index=True) if pairs else pd.DataFrame()
    features = [f"lag{lag}_{name}" for lag in range(1, 4) for name in FEATURES]
    targets = [f"target_{name}" for name in FEATURES]
    table = table.dropna(subset=features + targets).sort_values("timestamp")
    if len(table) < 100:
        raise ValueError(f"Only {len(table)} valid hourly SRP transitions were found; at least 100 are needed.")
    cut_time = table["timestamp"].quantile(.8)
    train_rows, test_rows = table[table.timestamp < cut_time], table[table.timestamp >= cut_time]
    if len(train_rows) < 50 or len(test_rows) < 20:
        raise ValueError("Not enough chronological training and holdout rows after quality filtering.")
    model = ExtraTreesRegressor(n_estimators=250, min_samples_leaf=3, max_features=1.0, random_state=120, n_jobs=-1)
    model.fit(train_rows[features], train_rows[targets])
    pred = model.predict(test_rows[features])
    persist = test_rows[[f"lag1_{name}" for name in FEATURES]].to_numpy()
    actual = test_rows[targets].to_numpy()
    model_mae = {name: round(float(mean_absolute_error(actual[:, i], pred[:, i])), 4) for i, name in enumerate(FEATURES)}
    persistence_mae = {name: round(float(mean_absolute_error(actual[:, i], persist[:, i])), 4) for i, name in enumerate(FEATURES)}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": features, "targets": FEATURES}, MODEL_PATH)
    meta = {"trained": True, "source": SOURCE, "source_url": SOURCE_URL, "license": "Apache-2.0",
            "input_rows": int(len(raw)), "sucker_rod_rows": int(len(wide)), "valid_hourly_transitions": int(len(table)),
            "training_rows": int(len(train_rows)), "holdout_rows": int(len(test_rows)),
            "training_wells": sorted(str(v) for v in train_rows.well_id.unique()),
            "holdout_wells": sorted(str(v) for v in test_rows.well_id.unique()),
            "chronological_cutoff_utc": cut_time.isoformat(), "features": FEATURES,
            "evaluation": {"mae": model_mae, "persistence_baseline_mae": persistence_mae,
                           "better_than_persistence": {name: model_mae[name] < persistence_mae[name] for name in FEATURES}},
            "excluded_quality_rows": int(len(wide) - len(clean)),
            "excluded_dynamometer_area": True,
            "note": "Next-hour sensor forecast only. Unlabeled external benchmark; forecast error is not event-detection accuracy and does not validate Baghewala outputs."}
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def forecast(well_id: str):
    if not MODEL_PATH.exists():
        raise ValueError("Train the public SRP benchmark model first.")
    _, wide = _read()
    valid = wide[FEATURES].notna().all(axis=1)
    valid &= wide["SPM"].between(.1, 12) & wide["pump_fillage"].between(0, 100)
    valid &= wide["min_rod_weight"].ge(0) & wide["max_rod_weight"].ge(wide["min_rod_weight"])
    history = wide.loc[valid & wide.well_id.eq(well_id)].sort_values("timestamp").tail(3)
    if len(history) < 3 or not history.timestamp.diff().dropna().eq(pd.Timedelta(hours=1)).all():
        raise ValueError("Need three consecutive, quality-filtered hourly rows for this public benchmark well.")
    names = [f"lag{lag}_{name}" for lag in range(1, 4) for name in FEATURES]
    row = [[float(history.iloc[-lag][name]) for lag in range(1, 4) for name in FEATURES]]
    bundle = joblib.load(MODEL_PATH)
    prediction = bundle["model"].predict(pd.DataFrame(row, columns=names))[0]
    latest = history.iloc[-1]
    metrics = status().get("evaluation", {})
    better = metrics.get("better_than_persistence", {})
    chosen = {name: float(prediction[i]) if better.get(name, False) else float(latest[name]) for i, name in enumerate(FEATURES)}
    methods = {name: "ExtraTrees" if better.get(name, False) else "persistence baseline (selected because it scored better on holdout)" for name in FEATURES}
    return {"well_id": well_id, "source": SOURCE, "source_url": SOURCE_URL,
            "latest_observation_utc": latest.timestamp.isoformat(),
            "forecast_for_utc": (latest.timestamp + pd.Timedelta(hours=1)).isoformat(),
            "latest_observed": {name: round(float(latest[name]), 4) for name in FEATURES},
            "forecast": {name: round(chosen[name], 4) for name in FEATURES},
            "method_by_parameter": methods,
            "scope": "External NK-field benchmark only; not BGW-001 and not a control recommendation."}
