# Nearby Wells Intelligence System (NWIS)

NWIS is a separate drilling knowledge module alongside the CSS/SRP production twin. It retrieves nearby wells and depth-matched event analogues; it does not claim to predict operational incidents.

## Data access and limitations

The application does **not** have OIL eRTMAC credentials or an authenticated OIL/DGH data feed. OIL describes its E&P Databank/DATUM as an internal, GIS-enabled system with permission-based access to well and reservoir data. DGH's National Data Repository is the route to request authorized exploration data; its registration and access conditions must be completed by the data owner/user. This app does not bypass those controls. Public aggregate production datasets are not treated as offset-well records.

Use the DGH portal to register/request relevant well records, or obtain an approved export from OIL's authorized data custodian. The page accepts normalized CSV exports because upstream schemas and export formats vary. Uploading a CSV does not authenticate its source or grant permission to use it.

## Import workflow

1. In NWIS, enter a source record name (for example, the approved export name and date).
2. Load a well survey CSV with columns `well_id,name,latitude,longitude,total_depth_m,active`; optional `formation` is supported. Exactly one row must have `active=true`. Coordinates must be WGS84 decimal degrees. This replaces the active map survey; earlier surveys remain in local SQLite history.
3. Load matching event CSV records using `well_id,event_type,md_m,formation,severity,summary,mitigation`. Supported event types are `mud_loss`, `kick`, `stuck_pipe`, `torque_spike`, `cementing`, `fishing`, and `npt`; severity must be `low`, `medium`, or `high`.
4. Check wells, formations, depths, units, coordinate reference system, and event classifications against the source records. All uploads are marked unverified and for review.

When a survey dataset is active, fabricated demo wells/events are excluded from its map and offset results. Event matching uses uploaded IDs, coordinates, formation labels, and measured depth only. Distances are computed from the uploaded coordinates using a local planar approximation; for very large areas use a geodesic/GIS implementation. Alerts mean “historical analogue found,” not risk probabilities, forecasts, or safe operating instructions. An empty match is not evidence of safety.

Text and searchable-PDF extraction creates human-review drafts only. Scanned PDFs need OCR before ingestion. eRTMAC streaming, LAS parsing, automatic WCR/DDR extraction, production-grade spatial database support, and model training on licensed OIL history are not connected.

## API

- `GET /api/nwis/offsets?radius_km=10&md_m=2400&formation=All&depth_window_m=200`
- `GET /api/nwis/events?q=losses&formation=All&event_type=All`
- `POST /api/nwis/wells/import?filename=well_headers.csv&source_label=approved-export` with raw CSV bytes
- `POST /api/nwis/documents/import?filename=events.csv&source_label=approved-export` with CSV, PDF, or text bytes

The seeded demo data remain clearly synthetic until a well-survey CSV is uploaded. Do not use this prototype for live drilling decisions.

## Official access references

- DGH [National Data Repository registration](https://ndr.dghindia.gov.in/Register)
- OIL [Geology & Reservoir / E&P Databank](https://www.oil-india.com/hi/node/5935)
