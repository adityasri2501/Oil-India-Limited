# PS120 Baghewala Digital Twin — architecture

## Runtime

- **Frontend:** React + Vite + Tailwind CSS, Recharts and Lucide. The industrial control-room shell provides ten module views over a shared active-well state.
- **API:** FastAPI + Pydantic. `/api/wells/BGW-001/state` is the shared source of computed state. CSS and SRP control changes are sent to the state API and trigger a full coupled recomputation.
- **Persistence:** Docker Compose mounts a durable SQLite fallback volume for saved what-if scenarios. This keeps the prototype self-contained; production deployment should replace it with PostgreSQL/PostGIS and migrations.
- **Numerics and ML:** NumPy implements screening physics. Optuna evaluates each candidate directly with the simulator. User-uploaded Baghewala records can train a separate production model. The bundled, author-published Hugging Face NK Field telemetry trains an isolated chronological SRP sensor forecaster; neither external telemetry nor Petrobras 3W is applied to BGW-001.
- **Telemetry:** REST polling and a WebSocket produce noisy synthetic samples from the active computed state. No SCADA connection is configured.

## Computation path

`CSS controls → lumped reservoir heat response → viscosity-temperature relation → mobility/inflow → SRP displacement/fillage/load proxies → oil/water production → SOR/energy → risk → direct constrained optimizer`

Changing either CSS or SRP controls updates all downstream values. The charts use the returned simulator values; illustrative time-series are explicitly synthetic projections around the computed state.

## Contracts and API

Typed Pydantic contracts include `WellState`, `CSSInput`, and `SRPInput`; computation returns reservoir, wellbore/inflow, SRP, production, risk and dynacard outputs. Routes cover wells/state, CSS, SRP, production, risk, optimization, scenarios, telemetry, measured dataset training/prediction, public SRP benchmark training/forecast, a keyed PPAC/data.gov.in source adapter, integrations and explanations. Scenario records and trained model artifacts persist in the configured data volume.

## Government adapters

`/api/integrations` reports adapter readiness. AIKosh and API Setu link to catalogue/marketplace onboarding; data.gov.in provides a credentialed PPAC query; BHASHINI uses a credentialed ULCA translation pipeline. Unconfigured connectors return explicit setup responses. Credentials remain in backend environment settings.

NWIS is a separate drilling knowledge module alongside the CSS/SRP twin. Its `/api/nwis/offsets`, `/api/nwis/events`, `/api/nwis/wells/import`, and `/api/nwis/documents/import` routes support coordinate-based radius/depth retrieval, formation/event search, analogue alerts, and user-uploaded well/event exports. Seeded data and locations are synthetic; authorized uploads are source-labeled but not authenticated. OIL E&P Databank / DGH NDR direct connectivity and eRTMAC streaming require access onboarding and credentials. See [NWIS.md](NWIS.md).

## Local run

Use `docker compose up --build`, then open `http://localhost:5173`; FastAPI docs are at `http://localhost:8000/docs`. Without Docker, install `backend/requirements.txt` and run Uvicorn from `backend`; install frontend dependencies in `frontend` and run Vite. Configure the Vite dev proxy to `http://localhost:8000` when running outside Compose (Compose networking is handled by the frontend proxy configuration).
