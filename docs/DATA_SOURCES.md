# Data sources and integrations

## Engineering references

- [OIL India — Rajasthan Fields / Baghewala](https://www.oil-india.com/hi/node/4588) is the primary reference for public field context (Jodhpur Sandstone, heavy-oil character, approximate depth, viscosity range and CSS/SRP use). These facts do not constitute well-level training data.
- [API Exploration & Production catalog (2024)](https://www.api.org/-/media/files/publications/2024-catalog/2024-exploration-and-production.pdf) lists TR 11L, *Design Calculations for Sucker Rod Pumping Systems (Conventional Units)* and describes its scope. The complete standard is not reproduced here. This prototype does not implement its full procedure; displayed rod loads are screening proxies.
- [U.S. DOE heavy-oil overview](https://www.energy.gov/sites/default/files/2022-11/22-TTG-Heavy-Oil.pdf) describes CSS injection, soak and production stages and the viscosity-reduction purpose of heating. The prototype's lumped heat equation is a demonstrator, not a field-calibrated implementation of that material.
- Student GitHub projects may inform software structure only; they are not engineering authorities.

## Public machine-learning benchmark

- [Oil Well Sensor Monitoring Dataset: NK Field](https://huggingface.co/datasets/Arailym-tleubayeva/NK-Oil-Well-Sensor-Monitoring) is an author-published Hugging Face dataset marked Apache-2.0. The dataset card reports 186,251 hourly observations across 10 wells (7 SRP wells), attributed to Galaz and Company LLP. A copy of `wells_dataset.csv` is included at `datasets/hf_nk_oil_well_sensor_monitoring/`. The application trains a separate chronological next-hour forecast for SPM, fillage and rod-load measurements; it does not use this dataset for Baghewala or the CSS/oil-rate model. Provenance is the dataset author's card, not independently audited source-system records. The card says years were assigned from source-file order, warns of extreme dynamometer-area values, and provides no oil production, CSS, failure or pump-unsetting labels. The anomalous dynamometer-area channel is excluded. Do not use for operations; verify source records and dates with the provider.
- [Petrobras 3W Dataset 2.0.0](https://figshare.com/articles/dataset/3W_Dataset_2_0_0/29205836) is a 1.67 GB CC BY 4.0 dataset of offshore well sensor episodes, with real, simulated, and hand-drawn examples. The app's optional event classifier uses only real `WELL-*` episodes and splits evaluation by anonymized physical well. It supports a separate offshore abnormal-event research benchmark only; it has no Baghewala CSS cycle, SRP settings, or matched oil-rate response and must not be used to train or validate those outputs. Cite Vaz Vargas et al., *Scientific Data* 13, 949 (2026), [DOI](https://doi.org/10.1038/s41597-026-07225-z).
- California CalGEM publishes well production/injection records, including monthly records in district datasets. These are a potential thermal-oil analogue source but use different reservoirs and reporting schemas; this app does not currently ingest them automatically. See [CalGEM production/injection data](https://conservation.ca.gov/calgem/pubs_stats/Pages/stats_prod.aspx).

Before external judging or deployment, attach the exact current OIL documents and API report editions used in the final engineering review. Licensing may restrict redistribution of API standards.

See [SOURCE_AUDIT.md](SOURCE_AUDIT.md) for dated public values, conflicting aggregates, government-platform coverage, and the recommended request for actual well records.

## Public digital platforms

- **AIKosh:** [official platform](https://aikosh.indiaai.gov.in/home/about-us/) for dataset/model/toolkit discovery. Potential catalog exploration only; no direct well telemetry assumption.
- **BHASHINI:** [official platform](https://bhashini.gov.in/) for language services and APIs. ULCA translation requires an onboarded `userID`, API key and pipeline ID; the adapter now makes the documented pipeline-config and inference requests when configured. See [onboarding](https://bhashini.gitbook.io/bhashini-apis/pre-requisites-and-onboarding) and [pipeline-config API](https://bhashini-developer-portal-dev.bhashini.co.in/docs/api/pipeline-config-call).
- **API Setu:** [official platform](https://apisetu.gov.in/) for government API discovery and onboarding; the application does not claim access to a specific API.
- **data.gov.in:** [official OGD platform](https://data.gov.in/about) for public government datasets and related APIs; national petroleum statistics are not a substitute for Baghewala telemetry.

Adapters report readiness from current backend environment settings. AIKosh and API Setu currently link to their official catalogues with onboarding guidance; no direct catalogue API is configured. API Setu use requires a specific API subscription and provider approval, not merely an API key. BHASHINI and data.gov.in have credentialed server-side request paths described below; they remain unavailable until credentials are configured.

The PPAC Monthly Indigenous Crude Oil Production resource now has a dedicated data.gov.in adapter on the Real Data & ML page. It requires a data.gov.in API key and resource ID configured as `DATAGOV_API_KEY` and `DATAGOV_CRUDE_RESOURCE_ID`; without both values it reports setup required. This is India-level aggregate data and is never used to train the BGW-001 model. See [REAL_DATA_WORKFLOW.md](REAL_DATA_WORKFLOW.md).

## Synthetic telemetry

The active simulator state drives synthetic oil-rate, tubing-pressure, motor-current and reservoir-temperature values. Random jitter is only a visual live-feed effect. No values are observed field measurements. Scenario inputs and computed outcomes are stored locally in the Dockerized SQLite fallback database.

## Government adapter UI

The AI Copilot integration panel reads `/api/integrations` for configured state and provides per-platform adapter checks and a BHASHINI translation request. AIKosh and API Setu remain discovery abstractions; neither is represented as an authenticated live connector without onboarding. BHASHINI returns the original text when credentials or an approved service configuration are absent. The data.gov.in PPAC adapter can retrieve only the configured public aggregate resource; it does not supply well-level Baghewala history. Platform credentials must be set in the backend environment and must never be exposed to the browser.

### Current live-connection behavior

The AI Copilot adapter panel reports required configuration dynamically. `data.gov.in` can make a real PPAC dataset request after `DATAGOV_API_KEY` and `DATAGOV_CRUDE_RESOURCE_ID` are configured. BHASHINI translation uses the ULCA pipeline-config and pipeline-inference flow when `BHASHINI_USER_ID`, `BHASHINI_API_KEY`, and `BHASHINI_PIPELINE_ID` are present; otherwise it reports setup required and does not claim a translation occurred. AIKosh and API Setu are shown as catalogue/marketplace links with onboarding guidance because this application has no authorized provider search API integration for them. A credential alone never means API Setu subscription or provider approval is complete.
