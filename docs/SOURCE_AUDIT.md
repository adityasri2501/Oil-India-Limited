# Source audit: publicly verifiable Baghewala data

**Reviewed 28 September 2026.** This audit distinguishes well-level measurements from field/company aggregates and public platform catalogs. No open BGW-001 time-series, steam log, pressure survey, SRP dynamometer card or rod-failure table was located. Keep the seeded well and its telemetry synthetic until OIL supplies measured records or the data is licensed through the DGH National Data Repository (NDR).

An additional real, public, third-party training dataset is now supported separately: Petrobras 3W v2.0.0 contains 27 variables across real offshore well-event episodes (42 anonymized real wells in the published release), alongside simulated/hand-drawn records. The PS120 event benchmark filters to real `WELL-*` instances. It is not Baghewala data and does not contain paired CSS settings and oil-rate response; it must not be used to train the Baghewala thermal/production model. Dataset and license: [official Figshare record](https://figshare.com/articles/dataset/3W_Dataset_2_0_0/29205836), CC BY 4.0.

### Additional public historical test summaries located

OIL's public tender CJG3289P15, section 8.2, reports grouped BGW-1/BGW-4 test-rate ranges for 1995 (3–4 KLPD with bottom-hole heater/PCP) and 2009–10 (4.5–5.5 KLPD with chemical stimulation/SRP), plus a 2012 Punam-1 rate (1.4 KLPD). Punam-1 is a neighboring structure, not a Baghewala well. The document also publishes selected reservoir/fluid properties. The ranges are available in `backend/public_data/baghewala_public_test_benchmarks.csv` and displayed in the Real Data & ML page with their source. OIL's paired BOPD figures are retained as stated; at least one pair is not a consistent unit conversion, so the app does not reconcile or convert them. These are public historical test summaries, not raw cycle data: no per-well split for the grouped BGW-1/BGW-4 rates, nor matched steam/SRP inputs, timestamped production, or dynacards are supplied. They are not ML training rows.

## Verified field and operating context

| Variable / fact | Publicly supportable value | Scope and use |
|---|---|---|
| Producing formation | Jodhpur Sandstone, Baghewala heavy-oil project | Field context, from OIL India. |
| Average depth | About 1,150 m | Field average; not a BGW-001 completion depth. OIL drilling documents also describe Jodhpur Sandstone target intervals around 1,050–1,100 m and discovery well BGW-1 in the 1,104 m formation. |
| Oil viscosity | 10,000–13,000 cP at 50 °C | OIL field description. Preserve the reference temperature; do not treat 12,000 cP as a measured BGW-001 PVT curve. |
| Crude gravity | OIL procurement material describes Baghewala crude at about 14–17° API (some documents use an approximate 14–18° range). | Prefer the OIL tender range over challenge-page summaries that say 17–19°; do not put API gravity into well state without fluid analysis. |
| CSS injection steam temperature | 250–320 °C | OIL's CSS technology description. The frontend/API upper bound is now 320 °C. |
| CSS injection phase duration | About 14–21 days, based on injectivity | OIL operating description; a field practice range, not a fixed well setting. |
| CSS soak duration | A few days, approximately 50% of injection days | OIL operating description. 7–10.5 days (168–252 hours) is an arithmetic implication of the cited injection window, not a published BGW-001 record. The prototype's 200-hour default is a representative midpoint assumption. |
| CSS stages | Injection → soak → production; SRP may be installed when initial self-flow ceases | OIL operating description. |
| Production uplift | OIL reports 40–60% enhancement over cold production in its Rajasthan CSS overview. | Field/program-level reported range; not a per-well prediction. Do not use to force computed dashboard rates. |
| CSS program | OIL's technology page, updated March 2026, reports 66 cycles executed to date, CSS on 24 wells, and 24 thermally completed wells with VIT/thermal wellheads; FY 2025–26 had 19 cycles and the same page reports 11 cycles in FY 2024–25. | Program aggregates, use only as dated contextual facts. |
| FY 2024–25 CSS result | OIL's annual report: 10 CSS cycles in that year contributed 51,347 bbl (7,674 t) from total Rajasthan-field crude production of 219,381 bbl (32,786 t); OIL reports 23.4% and 39.5% uplift at wells where CSS was applied. | Historical annual/program aggregate. Not per-well cycle response. Annual report's 38 cumulative / 10 annual cycles do not reconcile with the later technology page's 66 cumulative / 11 in FY 2024–25; do not combine those published counts as one validated time series. |

Primary references: [OIL India, Cyclic Steam Stimulation in Rajasthan Fields](https://www.oil-india.com/leveraging-technology); [OIL India, Rajasthan Fields / Baghewala](https://www.oil-india.com/hi/node/4588); [OIL India Annual Report 2024–25](https://www.oil-india.com/files/financial_results_documents/OIL_India_Annual_Report_2024_25_0.pdf); [OIL India Baghewala development tender](https://www.oil-india.com/files/oldtender/global/NIT_CDG4898P21.pdf).

## Conflicting and non-transferable numbers

OIL's Rajasthan Fields web page contains separate count statements: 56 wells drilled / 34 producing in one section, and 35 drilled / production above 1,100 bbl/d in another Baghewala PML section. Treat them as unresolved scope/date differences. The 1,100 bbl/d statement is field/project-wide, not a well rate. OIL also cites 1,200 bbl/d as the Rajasthan Fields' highest daily production in FY 2025–26; that is a regional aggregate, not Baghewala production. CSS cycle counts also conflict between the FY 2024–25 annual report and the later technology page. The challenge brief's 17–19° API description differs from OIL tender values; retain the official OIL crude description in field notes and leave per-well fluid properties unknown.

## What the government platforms actually contribute

| Platform | Verified data/use | Not a substitute for |
|---|---|---|
| AIKosh | Hosts PPAC's *Oil and Gas Snapshot of States FY 2025–26 Edition IV*, covering state/UT infrastructure, production, consumption and prices (as of 31 March 2026). | Baghewala well tests, CSS cycle logs, SCADA or SRP dynacards. |
| PPAC | State snapshots and monthly India oil/gas ready-reckoners; the current monthly publication includes national/historical aggregates. | Individual OIL well data. |
| data.gov.in | Government open-data catalogs include national monthly crude production and other sector statistics; access to some APIs uses portal registration/API keys. | A field or well historian. |
| API Setu | A platform for discovering and onboarding government APIs; no Baghewala operations API was identified in its catalog review. | A ready-made telemetry connector. |
| BHASHINI | Language services/APIs after organization registration/onboarding; useful for multilingual UI. | Petroleum engineering measurements or model validation. |
| DGH National Data Repository | DGH says its NDR hosts exploration/production information including seismic and well data and provides a registration/access process. This is the best public route to request relevant subsurface/well records; availability and permissions for Baghewala-specific records must be confirmed with DGH/OIL. | An open, anonymous download of operational CSS/SRP history; the portal does not promise those records are publicly accessible. |

Platform references: [AIKosh PPAC state snapshot](https://aikosh.indiaai.gov.in/home/datasets/details/oil_and_gas_snapshot_of_states_fy_2025_26_edition_iv_1.html); [PPAC snapshots](https://ppac.gov.in/); [data.gov.in oil catalog](https://data.gov.in/keywords/oil); [API Setu](https://apisetu.gov.in/); [BHASHINI](https://bhashini.gov.in/); [DGH National Data Repository](https://dghindia.gov.in/ndr).

## Engineering standards and next data request

[API's Exploration & Production catalog](https://www.api.org/-/media/files/publications/2024-catalog/2024-exploration-and-production.pdf) identifies TR 11L as *Design Calculations for Sucker Rod Pumping Systems*. Obtain the licensed report and measured completion/pump/well fluid data before implementing a standard-based SRP design; a catalog entry is not the full method. The prototype's load outputs remain explicitly screening proxies.

To make the twin data-driven with real measurements, request from OIL: well header/completion and trajectory; dated CSS injection steam mass, quality, pressure and temperature; soak start/end and production restart; daily oil/water/gas; wellhead and downhole pressure/temperature; fluid PVT/viscosity vs temperature; SRP model/geometry, stroke/SPM, pump depth, motor current and calibrated up/down dynamometer cards; workover/failure and downtime history. Request data dictionary, units, timestamps/timezone, measurement uncertainty, well IDs and redistribution permission. DGH NDR is a potential access pathway for well/seismic records, subject to registration and applicable licenses; OIL remains the authoritative source for operating/SCADA history.
