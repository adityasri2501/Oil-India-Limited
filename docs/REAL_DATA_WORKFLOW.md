# Real-data setup

## Scope

The digital-twin physics dashboard remains a clearly labeled screening simulation until OIL/DGH well measurements are provided. A national oil-production series cannot train or validate a Baghewala well-response model: it has no per-well steam, SRP settings, pressure or production-test linkage. DGH's National Data Repository describes its collection as including well/log and production information for entitled users. Request access to the relevant Baghewala records through OIL India/DGH NDR before treating the ML model as a field model.

The app now includes the real historical test summaries published in OIL tender CJG3289P15: grouped BGW-1/BGW-4 rates for 1995 and 2009–10, and a 2012 Punam-1 test. These are visible on **Real Data & ML** and stored in `backend/public_data/baghewala_public_test_benchmarks.csv`. Since the BGW-1/BGW-4 results are grouped and lack paired steam/SRP inputs, they serve as source-labeled historical context only; they cannot train the model. The Punam-1 result is kept separate because it is another structure.

## Train a separate real-well event model from Petrobras 3W

The app supports an additional public training source for abnormal-event classification: Petrobras [3W Dataset 2.0.0](https://figshare.com/articles/dataset/3W_Dataset_2_0_0/29205836), licensed CC BY 4.0. It is a 1.67 GB Parquet release with 27 variables and episodes from 42 anonymized offshore wells. It is not Baghewala data and has no CSS cycle design or measured Baghewala oil-rate target. Therefore, this model is separate from the BGW physics model, is not applied to its synthetic telemetry, and only serves as an offshore event-classification research benchmark.

Download and extract the official archive into `datasets/3w-2.0.0` beside `docker-compose.yml`. Keep the original attribution/license. In Docker Compose, this folder is mounted read-only at `/datasets/3w`. For another location, set `PS120_3W_DATASET_DIR` to the extracted root. Select **Train offshore event model** in Real Data & ML. The trainer reads Parquet files named `WELL-*`, excludes `SIMULATED_*` and `DRAWN_*`, summarizes each episode, and holds out entire physical well IDs to reduce leakage across overlapping records. It reports accuracy, balanced accuracy, macro-F1 and counts; classes missing from training are excluded from the scored holdout and counted separately. Results are sensitive to the limited number of real wells and event-class coverage; this is not an operational risk model.

## Train with measured well history

Use **Real Data & ML** in the app to upload a CSV. The model parses timestamps and sorts records chronologically. Train one well per file. Required columns and units:

| Column | Unit |
| --- | --- |
| `timestamp` | ISO-8601 observation time |
| `steam_tonnes` | tonnes injected in the represented cycle |
| `steam_temp_c` | °C |
| `soak_hours` | hours |
| `spm` | strokes/minute |
| `stroke_m` | metres |
| `oil_rate_m3d` | measured oil rate, m³/day |

At least 30 valid rows are required. The application trains a Random Forest on the first 80% and reports MAE, RMSE and R² on the final 20% by timestamp. The CSV may include `well_id` (if present, only one distinct well is accepted); additional metadata columns are preserved in the stored uploaded records but are not model features. The model does not yet use time-series lag features. Uploaded CSV and model artifacts persist in `PS120_DATA_DIR` (Docker Compose maps it to the named `/data` volume).

This is a small-data supervised baseline, not an approved operational model. Check coverage, leakage, unit consistency, and out-of-time performance with a petroleum engineer before relying on it. It predicts oil rate only; it does not predict viscosity, pump loads, failure probability or safety limits.

## Dynamic public aggregate feed

The Real Data & ML page can query the PPAC **Monthly Indigenous Crude Oil Production** resource published through data.gov.in. That is real government data at national scale and is displayed separately from BGW-001. Configure both `DATAGOV_API_KEY` and `DATAGOV_CRUDE_RESOURCE_ID` in the backend environment; generate the key and identify the resource through the official [data.gov.in resource page](https://data.gov.in/resource/monthly-indigenous-crude-oil-production). The adapter fetches the source only when the user selects Refresh. It does not infer Baghewala values from national aggregates. The PPAC site also publishes monthly reports and historical snapshots at [ppac.gov.in](https://ppac.gov.in/).

## Access and sources

- [DGH National Data Repository](https://dghindia.gov.in/ndr): official overview and registration/access route for E&P records; availability and permissions for Baghewala well data need confirmation.
- [PPAC monthly indigenous crude-oil resource on data.gov.in](https://data.gov.in/resource/monthly-indigenous-crude-oil-production): official national monthly aggregate series.
- [PPAC reports and snapshots](https://ppac.gov.in/): official published aggregate reports.
- [OIL India Rajasthan Fields](https://www.oil-india.com/leveraging-technology): public field/program context, not a downloadable per-well historian.

Never fill a missing measured column with simulator output and then call it real training data. Do not mix aggregate national production into well-level model training.