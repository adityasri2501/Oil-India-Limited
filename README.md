# PS120 Baghewala Digital Twin

An interactive engineering demonstrator for a synthetic Baghewala CSS and sucker-rod pumping well. It couples CSS thermal response, reservoir mobility/inflow, SRP proxies, production, SOR, energy and risk. Optimizer candidates are evaluated directly by the simulator. The Real Data & ML workspace keeps measured Baghewala production training separate from a real offshore abnormal-event benchmark trained from Petrobras 3W.

## Start

With Docker Desktop running:

```sh
docker compose up --build
```

Open `http://localhost:5173`. The API and OpenAPI page are at `http://localhost:8000` and `http://localhost:8000/docs`. Compose uses a persistent SQLite volume for saved scenarios and imported NWIS event records. For local development, start the API from `backend` with `python -m uvicorn app.main:app --reload --port 8000`, then run `npm ci && npm run dev` in `frontend`.

## GitHub Pages demo

The repository includes a GitHub Actions workflow that builds and publishes the Vite frontend when changes are pushed to `main` (or when run manually). In the repository, open **Settings → Pages** and set **Build and deployment → Source** to **GitHub Actions**. The published site will use `https://adityasri2501.github.io/Oil-India-Limited/`.

GitHub Pages serves static files and cannot host the FastAPI service. Until a backend is deployed to a public HTTPS host, the page shows a clear API connection message; simulator-backed pages need that API. After deploying the backend, add a repository Actions variable named `VITE_API_BASE_URL` under **Settings → Secrets and variables → Actions → Variables**. Set it to the backend origin only (for example, `https://your-api.example.com`, without `/api` or a trailing slash), allow the Pages origin in backend CORS, then rerun **Actions → Deploy PS120 frontend to GitHub Pages → Run workflow**. Do not put credentials in this frontend variable; keep provider credentials on the backend.

### Deploying the API on Vercel

Create a Vercel project from this repository and set **Root Directory** to `backend`. Vercel will use `backend/index.py` as its FastAPI entry point and install `backend/requirements.txt`. After deployment, confirm `https://<your-vercel-domain>/api/health` returns JSON. Then set `VITE_API_BASE_URL` in the GitHub repository Actions variables to `https://<your-vercel-domain>` (origin only) and rerun the Pages workflow.

Vercel Functions are stateless: this demo's in-memory active-well controls and local SQLite scenario/NWIS storage are not durable across instances or redeployments. Use a hosted PostgreSQL service and persistent object storage before relying on saved scenarios, uploaded records, or model training data in a shared deployment. Public datasets stored outside `backend/` are not included when deploying only the backend root.

## Scope

The seeded `BGW-001` well and live telemetry are explicitly synthetic. No proprietary OIL India well telemetry, SCADA feed, authenticated government integration, or operational limit is represented. Government platform adapters return demo fallbacks until access and onboarding are configured. See [architecture](docs/ARCHITECTURE.md), [assumptions](docs/ENGINEERING_ASSUMPTIONS.md), [sources](docs/DATA_SOURCES.md), the detailed [source audit](docs/SOURCE_AUDIT.md), and [model notes](docs/MODEL_DOCUMENTATION.md).

The merged **NWIS · Offset Wells** module is a separate drilling knowledge workspace. Its seeded map, wells, formations and events are synthetic; proximity alerts are analogue retrieval, not predictive probabilities. Authorized well-survey and event CSV exports can be imported into the persistent database and used for real-coordinate, depth-aware lookups; uploads are unverified and are not independently authenticated. OIL E&P Databank / DGH NDR live access, scanned PDF OCR, and eRTMAC streaming are not connected because credentials/onboarding are not configured. See [NWIS scope and data contract](docs/NWIS.md).

## Public training dataset

The workspace includes the 12.6 MB author-published Hugging Face [NK Field SRP telemetry dataset](https://huggingface.co/datasets/Arailym-tleubayeva/NK-Oil-Well-Sensor-Monitoring) (Apache-2.0). Use **Real Data & ML → Public SRP telemetry** to train a separate chronological next-hour sensor forecast. It is a different field, has no CSS or oil-rate/failure labels, and must not be presented as Baghewala validation. The dataset card has provenance and timestamp caveats; see [REAL_DATA_WORKFLOW.md](docs/REAL_DATA_WORKFLOW.md).

The optional Petrobras [3W Dataset 2.0.0](https://figshare.com/articles/dataset/3W_Dataset_2_0_0/29205836) (CC BY 4.0) supports a separate offshore well-event classification benchmark. Its full archive is about 1.67 GB; download and extract it under `datasets/3w-2.0.0`, then use **Real Data & ML → Train offshore event model**. Training uses real `WELL-*` Parquet episodes only, with a held-out physical-well split. Neither public benchmark trains the Baghewala CSS production model or scores BGW-001 simulator telemetry. See [REAL_DATA_WORKFLOW.md](docs/REAL_DATA_WORKFLOW.md) for scope and caveats.
