# PS120 Baghewala Digital Twin

An interactive engineering demonstrator for a synthetic Baghewala CSS and sucker-rod pumping well. It couples CSS thermal response, reservoir mobility/inflow, SRP proxies, production, SOR, energy and risk. Optimizer candidates are evaluated directly by the simulator. The Real Data & ML workspace keeps measured Baghewala production training separate from a real offshore abnormal-event benchmark trained from Petrobras 3W.

## Start

With Docker Desktop running:

```sh
docker compose up --build
```

Open `http://localhost:5173`. The API and OpenAPI page are at `http://localhost:8000` and `http://localhost:8000/docs`. Compose uses a persistent SQLite volume for saved scenarios and imported NWIS event records. For local development, start the API from `backend` with `python -m uvicorn app.main:app --reload --port 8000`, then run `npm ci && npm run dev` in `frontend`.

## Scope

The seeded `BGW-001` well and live telemetry are explicitly synthetic. No proprietary OIL India well telemetry, SCADA feed, authenticated government integration, or operational limit is represented. Government platform adapters return demo fallbacks until access and onboarding are configured. See [architecture](docs/ARCHITECTURE.md), [assumptions](docs/ENGINEERING_ASSUMPTIONS.md), [sources](docs/DATA_SOURCES.md), the detailed [source audit](docs/SOURCE_AUDIT.md), and [model notes](docs/MODEL_DOCUMENTATION.md).

The merged **NWIS · Offset Wells** module is a separate drilling knowledge workspace. Its seeded map, wells, formations and events are synthetic; proximity alerts are analogue retrieval, not predictive probabilities. Authorized well-survey and event CSV exports can be imported into the persistent database and used for real-coordinate, depth-aware lookups; uploads are unverified and are not independently authenticated. OIL E&P Databank / DGH NDR live access, scanned PDF OCR, and eRTMAC streaming are not connected because credentials/onboarding are not configured. See [NWIS scope and data contract](docs/NWIS.md).

## Public training dataset

The optional Petrobras [3W Dataset 2.0.0](https://figshare.com/articles/dataset/3W_Dataset_2_0_0/29205836) (CC BY 4.0) supports a separate offshore well-event classification benchmark. Download and extract it under `datasets/3w-2.0.0` (large archive, about 1.67 GB); then use **Real Data & ML → Train offshore event model**. Docker Compose mounts that folder read-only into the API container. Training uses real `WELL-*` Parquet episodes only, with a held-out physical-well split. This benchmark does not train the Baghewala CSS production model or score BGW-001 simulator telemetry. See [REAL_DATA_WORKFLOW.md](docs/REAL_DATA_WORKFLOW.md) for scope and caveats.
