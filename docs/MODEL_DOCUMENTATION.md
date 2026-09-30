# Model documentation

## State flow

`CSSInput(steam_tonnes, steam_temp_c, injection_pressure_bar, soak_hours, production_days)` and `SRPInput(spm, vfd_frequency_hz, stroke_m, pump_diameter_in, efficiency)` feed a deterministic coupled calculation. Injection pressure and VFD frequency are stored/displayed but deliberately excluded from the calculation until a well-specific pressure/steam-quality/injectivity relationship, drive-to-SPM calibration, and integrity envelope are supplied. Outputs include post-soak, production-average and end-of-period reservoir temperature plus a formula-generated production cooling/rate profile, viscosity/mobility/inflow, wellbore friction loss, pump capacity/fillage and load proxies, oil/water rates, SOR, energy proxy, risk components and an illustrative dynamometer card. Inflow and tubing friction are coupled with a scalar root solve.

## Surrogate and optimizer

The optimizer performs a 64-trial Optuna TPE search seeded with the current CSS/SRP settings and evaluates every trial directly with the coupled screening simulator. It does not use a synthetic-trained ML surrogate. The separate measured-data Random Forest can be trained from an uploaded CSV with the five CSS/SRP inputs and observed `oil_rate_m3d` target. It requires at least 30 valid rows, sorts by timestamp, trains on the first 80%, and evaluates against the final 20%. Sort input chronologically before upload; the model's prediction is advisory and does not alter or calibrate the physics-screening outputs. No measured training data is bundled with the prototype.

## External well-event benchmark

An optional independent event classifier can be trained from the CC BY 4.0 Petrobras 3W Dataset 2.0.0. It uses per-instance sensor summaries and real `WELL-*` files only, excludes simulated and hand-drawn examples, and partitions by physical well ID. It classifies the dataset's event labels; it is not calibrated to Baghewala, not connected to the BGW risk score, and not a substitute for field failure labels. Its group-holdout metrics measure only the represented offshore wells and classes. See [REAL_DATA_WORKFLOW.md](REAL_DATA_WORKFLOW.md) and [DATA_SOURCES.md](DATA_SOURCES.md) for dataset setup and attribution.

## XAI / explanation

`/api/explain` emits a rule-based trace of the actual current computed metrics and names the equation chain and caveats. It is not a free-form LLM, and it does not invent operating values. The frontend's AI Copilot view uses this endpoint.

## Typed API contracts

Pydantic contracts include `WellState`, `CSSState`, `ReservoirState`, `WellboreState`, `SRPState`, `ProductionState`, `RiskState`, `OptimizationResult`, and the input contract `ScenarioInput`. `WellState` nests CSS/SRP controls and identifies the synthetic source. Detailed simulator output fields are returned by the state endpoint and optimizer contract.

## Validation needed

Perform parameter sensitivity checks, unit audits, API 11L benchmarking, thermal model calibration, measured well-test reconciliation, uncertainty quantification, historical backtesting and independent review before treating any output as an engineering prediction.

## Interactive parameter sweeps

The What-if page can evaluate nine evenly spaced values for steam mass, injection temperature, soak duration, production period, pump speed, stroke length, pump diameter or mechanical efficiency while holding the other displayed controls fixed. Each point is run through simulate; the sweep does not use ML surrogate predictions. Supported input bounds are enforced by the API. The chart and table report the direct outputs for audit and repeatability. This improves comparison and sensitivity testing, but does not calibrate the screening equations against BGW-001 measurements.
