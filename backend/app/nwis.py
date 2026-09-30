"""Offset-well knowledge prototype. Seed records are explicitly synthetic."""
import csv
import io
import math
import re
from typing import Any

from pypdf import PdfReader

from . import db

ACTIVE = {"well_id": "NW-DEMO-A01", "name": "Active Demo Well", "active": True, "source": "synthetic demonstration", "lat": 27.0, "lon": 95.0, "easting_km": 0.0, "northing_km": 0.0, "td_m": 3200}
OFFSETS = [
    {"well_id":"NW-DEMO-O02","name":"Offset Demo O02","active":False,"source":"synthetic demonstration","easting_km":1.8,"northing_km":1.2,"td_m":3150},
    {"well_id":"NW-DEMO-O03","name":"Offset Demo O03","active":False,"source":"synthetic demonstration","easting_km":4.3,"northing_km":-0.8,"td_m":3400},
    {"well_id":"NW-DEMO-O04","name":"Offset Demo O04","active":False,"source":"synthetic demonstration","easting_km":-3.4,"northing_km":-4.0,"td_m":2980},
    {"well_id":"NW-DEMO-O05","name":"Offset Demo O05","active":False,"source":"synthetic demonstration","easting_km":-8.5,"northing_km":2.9,"td_m":3300},
    {"well_id":"NW-DEMO-O06","name":"Offset Demo O06","active":False,"source":"synthetic demonstration","easting_km":10.2,"northing_km":-5.8,"td_m":3050},
    {"well_id":"NW-DEMO-O07","name":"Offset Demo O07","active":False,"source":"synthetic demonstration","easting_km":-12.5,"northing_km":-7.4,"td_m":3500},
]
WELLS = [ACTIVE, *OFFSETS]
SEED_EVENTS = [
    {"event_id":"DEMO-E01","well_id":"NW-DEMO-O02","md_m":1825,"formation":"Demo Sand B","event_type":"mud_loss","severity":"high","summary":"Synthetic loss-of-circulation example while drilling Demo Sand B.","mitigation":"Demo lesson: check the approved loss-response procedure and verify ECD / returns before action.","source":"synthetic demonstration","source_document":"Seeded demo case","review_required":True},
    {"event_id":"DEMO-E02","well_id":"NW-DEMO-O02","md_m":2360,"formation":"Demo Shale C","event_type":"stuck_pipe","severity":"medium","summary":"Synthetic elevated drag and stuck-pipe event example.","mitigation":"Demo lesson: review trip practice, hole cleaning indicators and the approved well plan.","source":"synthetic demonstration","source_document":"Seeded demo case","review_required":True},
    {"event_id":"DEMO-E03","well_id":"NW-DEMO-O03","md_m":2425,"formation":"Demo Shale C","event_type":"torque_spike","severity":"medium","summary":"Synthetic torque increase near a formation boundary.","mitigation":"Demo lesson: compare torque trend, survey and lithology with the drilling team.","source":"synthetic demonstration","source_document":"Seeded demo case","review_required":True},
    {"event_id":"DEMO-E04","well_id":"NW-DEMO-O04","md_m":2410,"formation":"Demo Shale C","event_type":"kick","severity":"high","summary":"Synthetic kick indicator scenario for interface demonstration.","mitigation":"Demo lesson: follow approved well-control procedures; this application does not direct well control.","source":"synthetic demonstration","source_document":"Seeded demo case","review_required":True},
    {"event_id":"DEMO-E05","well_id":"NW-DEMO-O05","md_m":2055,"formation":"Demo Sand B","event_type":"cementing","severity":"low","summary":"Synthetic cementing quality / remediation record example.","mitigation":"Demo lesson: review cement job design, lab data and verified post-job evaluation.","source":"synthetic demonstration","source_document":"Seeded demo case","review_required":True},
    {"event_id":"DEMO-E06","well_id":"NW-DEMO-O06","md_m":2690,"formation":"Demo Shale C","event_type":"npt","severity":"medium","summary":"Synthetic non-productive time event associated with hole cleaning.","mitigation":"Demo lesson: correlate cuttings transport observations with the approved hydraulics plan.","source":"synthetic demonstration","source_document":"Seeded demo case","review_required":True},
    {"event_id":"DEMO-E07","well_id":"NW-DEMO-O07","md_m":2950,"formation":"Demo Carbonate D","event_type":"mud_loss","severity":"medium","summary":"Synthetic partial-loss example in Demo Carbonate D.","mitigation":"Demo lesson: consult the approved loss contingency and offset evidence.","source":"synthetic demonstration","source_document":"Seeded demo case","review_required":True},
]
EVENT_TYPES = {"losses":"mud_loss", "loss":"mud_loss", "mud loss":"mud_loss", "kick":"kick", "stuck pipe":"stuck_pipe", "stuck":"stuck_pipe", "torque":"torque_spike", "cement":"cementing", "fishing":"fishing", "npt":"npt", "non productive":"npt"}
REQUIRED_CSV = {"well_id", "event_type", "md_m", "formation", "severity", "summary", "mitigation"}


def all_events() -> list[dict[str, Any]]:
    uploaded = db.list_nwis_events()
    # Once customer survey data is active, never mix fabricated demo incidents into it.
    return uploaded if db.list_nwis_wells() else [*SEED_EVENTS, *uploaded]


def _with_coordinates(well: dict) -> dict:
    if "latitude" in well and "longitude" in well:
        lat, lon = float(well["latitude"]), float(well["longitude"])
        active = next((item for item in db.list_nwis_wells() if item.get("active")), None)
        if active and not well.get("active"):
            northing = (lat - active["latitude"]) * 111.32
            easting = (lon - active["longitude"]) * 111.32 * math.cos(math.radians(active["latitude"]))
            distance = math.hypot(easting, northing)
        else:
            northing = easting = distance = 0.0
        return {**well, "lat": lat, "lon": lon, "easting_km": round(easting, 3), "northing_km": round(northing, 3), "distance_km": round(distance, 2), "td_m": well.get("total_depth_m")}
    lat = ACTIVE["lat"] + well["northing_km"] / 111.32
    lon = ACTIVE["lon"] + well["easting_km"] / (111.32 * math.cos(math.radians(ACTIVE["lat"])))
    return {**well, "lat": round(lat, 6), "lon": round(lon, 6), "distance_km": round(math.hypot(well["easting_km"], well["northing_km"]), 2)}


def offset_analysis(radius_km: float = 10, md_m: float = 2400, formation: str = "All", depth_window_m: float = 200):
    imported = db.list_nwis_wells()
    base_wells = imported or WELLS
    active_base = next((well for well in base_wells if well.get("active")), ACTIVE)
    if imported:
        # Include authoritative coordinates only from the uploaded well-header survey.
        wells = []
        for well in imported:
            item = _with_coordinates(well)
            if not item.get("active"):
                northing = (item["lat"] - active_base["latitude"]) * 111.32
                easting = (item["lon"] - active_base["longitude"]) * 111.32 * math.cos(math.radians(active_base["latitude"]))
                item.update(easting_km=round(easting, 3), northing_km=round(northing, 3), distance_km=round(math.hypot(easting, northing), 2))
            wells.append(item)
    else:
        wells = [_with_coordinates(well) for well in base_wells]
    offsets = [well for well in wells if not well["active"] and well["distance_km"] <= radius_km]
    ids = {well["well_id"] for well in offsets}
    events = [event for event in all_events() if event["well_id"] in ids and (formation == "All" or event["formation"].casefold() == formation.casefold())]
    related = [event for event in events if abs(float(event["md_m"]) - md_m) <= depth_window_m]
    rank = {"low": 1, "medium": 2, "high": 3}
    for event in related:
        event["depth_delta_m"] = round(float(event["md_m"]) - md_m, 1)
        event["offset_distance_km"] = next((well["distance_km"] for well in offsets if well["well_id"] == event["well_id"]), None)
    alerts = []
    for event in sorted(related, key=lambda item: (rank.get(item["severity"], 0), -abs(item["depth_delta_m"])), reverse=True):
        alerts.append({"level": event["severity"], "event_type": event["event_type"], "well_id": event["well_id"], "formation": event["formation"], "md_m": event["md_m"], "message": f"{event['severity'].title()} {event['event_type'].replace('_', ' ')} analogue in {event['well_id']} at {event['md_m']} m MD ({event['offset_distance_km']} km offset; {event['depth_delta_m']:+} m from current depth)."})
    real_data_active = bool(imported)
    source_label = imported[0].get("source_label") if imported else None
    active_well = next((well for well in wells if well.get("active")), wells[0] if wells else _with_coordinates(ACTIVE))
    provenance = (f"Uploaded survey data · source declared as: {source_label or 'unspecified'} · provenance not independently verified. Distances use uploaded coordinates; analogue flags are not risk probabilities or operational instructions." if real_data_active else "Synthetic NWIS demo records and arbitrary local map coordinates. Replace with authorized OIL well/survey/event records; proximity flags are not risk probabilities or operational instructions.")
    return {"active_well": active_well, "real_data_active": real_data_active, "source_label": source_label, "radius_km": radius_km, "active_md_m": md_m, "formation": formation, "depth_window_m": depth_window_m, "wells": wells, "offsets": offsets, "events": events, "related_events": related, "alerts": alerts, "provenance": provenance}


WELL_CSV_REQUIRED = {"well_id", "name", "latitude", "longitude", "total_depth_m", "active"}

def ingest_well_headers(filename: str, raw: bytes, source_label: str):
    if len(raw) > 15_000_000: raise ValueError("Well survey CSV exceeds 15 MB")
    if not source_label.strip(): raise ValueError("Enter the source system or document for provenance tracking")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        fields = {str(field).strip() for field in (reader.fieldnames or [])}
        if not WELL_CSV_REQUIRED.issubset(fields):
            raise ValueError("Well CSV must include: " + ", ".join(sorted(WELL_CSV_REQUIRED)))
        records=[]
        for row in reader:
            item={str(key).strip(): (value or "").strip() for key,value in row.items() if key}
            try: lat,lon,td=float(item["latitude"]),float(item["longitude"]),float(item["total_depth_m"])
            except (ValueError,KeyError): continue
            if not item.get("well_id") or not item.get("name") or not -90<=lat<=90 or not -180<=lon<=180 or not 0<td<=20000: continue
            active=item["active"].casefold() in {"true","1","yes","active"}
            records.append({"well_id":item["well_id"][:80],"name":item["name"][:120],"latitude":lat,"longitude":lon,"total_depth_m":td,"td_m":td,"active":active,"formation":item.get("formation","Unknown")[:120],"source":"user-uploaded well survey; unverified","source_label":source_label.strip()[:200],"source_document":filename,"review_required":True})
    except UnicodeDecodeError as exc: raise ValueError("CSV must be UTF-8 encoded") from exc
    if not records: raise ValueError("No valid well header rows found")
    if sum(1 for item in records if item["active"]) != 1: raise ValueError("Mark exactly one well as active=true in the CSV")
    if len({item["well_id"] for item in records}) != len(records): raise ValueError("Well IDs must be unique")
    dataset_id=db.replace_nwis_wells(records)
    return {"filename":filename,"wells_added":len(records),"dataset_id":dataset_id,"active_well":next(x["well_id"] for x in records if x["active"]),"source_label":source_label,"provenance_verified":False,"message":"Survey loaded. Source credentials and data provenance are not verified. Upload matching event CSV records to enable event search and depth analogues."}


def search_events(q: str = "", formation: str = "All", event_type: str = "All"):
    events = all_events()
    if db.list_nwis_wells():
        well_ids={item["well_id"] for item in db.list_nwis_wells()}
        events=[event for event in events if event.get("well_id") in well_ids]
    if formation != "All":
        events = [event for event in events if event["formation"].casefold() == formation.casefold()]
    if event_type != "All":
        events = [event for event in events if event["event_type"] == event_type]
    term = q.strip().casefold()
    if term:
        if term in {"loss", "losses", "lost circulation"}:
            events = [event for event in events if event["event_type"] == "mud_loss" or term in " ".join(str(value) for value in event.values()).casefold()]
        else:
            events = [event for event in events if term in " ".join(str(value) for value in event.values()).casefold()]
    return {"records": events, "count": len(events), "formations": sorted({event["formation"] for event in all_events()}), "event_types": sorted({event["event_type"] for event in all_events()})}


def _extract_text_events(text: str, filename: str):
    drafts = []
    depth_re = re.compile(r"(?:MD|measured\s+depth|depth)\s*(?:[:=]|at)?\s*(\d{3,5}(?:\.\d+)?)\s*m?", re.I)
    for match in re.finditer(r"loss(?:es| of circulation)?|kick|stuck\s+pipe|torque|cement(?:ing)?|fishing|NPT|non[ -]productive time", text, re.I):
        start, end = max(0, match.start() - 240), min(len(text), match.end() + 300)
        excerpt = re.sub(r"\s+", " ", text[start:end]).strip()
        depth = depth_re.search(excerpt)
        token = match.group(0).casefold()
        event_type = next((kind for key, kind in EVENT_TYPES.items() if key in token), "npt")
        formation_match = re.search(r"(?:formation|zone)\s*[:=]?\s*([A-Za-z0-9 _-]{2,40})", excerpt, re.I)
        well_match = re.search(r"\b([A-Z]{1,6}[- ]?[A-Z0-9]{2,12})\b", excerpt)
        drafts.append({"well_id": well_match.group(1).replace(" ", "-") if well_match else "UPLOADED-REVIEW", "md_m": float(depth.group(1)) if depth else None, "formation": formation_match.group(1).strip(" .,:;") if formation_match else "Unclassified - review", "event_type": event_type, "severity": "medium", "summary": excerpt[:500], "mitigation": "Review the source report and enter a verified mitigation before operational use.", "source": "user-uploaded document; extracted draft", "source_document": filename, "review_required": True, "extraction_confidence": "low; human validation required"})
    return drafts


def ingest_document(filename: str, raw: bytes, source_label: str = ""):
    if len(raw) > 15_000_000:
        raise ValueError("Document exceeds 15 MB")
    lower = filename.casefold()
    if lower.endswith(".csv"):
        try:
            reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
            if not reader.fieldnames or not REQUIRED_CSV.issubset({field.strip() for field in reader.fieldnames}):
                raise ValueError("CSV must include columns: " + ", ".join(sorted(REQUIRED_CSV)))
            records = []
            for row in reader:
                item = {str(key).strip(): (value or "").strip() for key, value in row.items() if key}
                if not item.get("well_id") or not item.get("formation") or not item.get("summary"):
                    continue
                try:
                    md = float(item["md_m"])
                except (ValueError, KeyError):
                    continue
                if not 0 <= md <= 20000:
                    continue
                event_type = item["event_type"].casefold().replace(" ", "_")
                severity = item["severity"].casefold()
                if event_type not in {"mud_loss", "kick", "stuck_pipe", "torque_spike", "cementing", "fishing", "npt"} or severity not in {"low", "medium", "high"}:
                    continue
                records.append({"well_id": item["well_id"], "md_m": md, "formation": item["formation"], "event_type": event_type, "severity": severity, "summary": item["summary"][:1000], "mitigation": item.get("mitigation", "")[:1000], "source": f"user-uploaded CSV; unverified; {source_label}" if source_label else "user-uploaded CSV; unverified", "source_label": source_label or "unspecified", "source_document": filename, "review_required": True})
        except UnicodeDecodeError as exc:
            raise ValueError("CSV must be UTF-8 encoded") from exc
        if not records:
            raise ValueError("No valid event rows found in the CSV")
        ids = db.add_nwis_events(records)
        return {"filename": filename, "records_added": len(ids), "records": [{**record, "id": event_id} for record, event_id in zip(records, ids)], "extraction": "structured CSV import", "review_required": True, "message": "Imported as unverified records. Review source, depth, formation, severity and mitigation before using them."}

    if lower.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(raw), strict=False)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise ValueError(f"Could not read PDF ({type(exc).__name__})") from exc
    elif lower.endswith((".txt", ".md")):
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("Text document must be UTF-8 encoded") from exc
    else:
        raise ValueError("Supported uploads are text, Markdown, searchable PDF, and structured CSV")
    drafts = _extract_text_events(text, filename)
    if not text.strip():
        raise ValueError("No selectable text found. Scanned PDFs need OCR before they can be ingested.")
    if not drafts:
        return {"filename": filename, "records_added": 0, "drafts": [], "extraction": "keyword-assisted text extraction", "review_required": True, "message": "Text was read but no supported event keywords were found. Nothing was saved."}
    return {"filename": filename, "records_added": 0, "drafts": drafts, "extraction": "keyword-assisted draft extraction", "review_required": True, "message": "Extracted draft events only. Review and import them as structured CSV; the system does not auto-save unverified NLP output."}
