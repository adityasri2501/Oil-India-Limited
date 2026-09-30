"""Small set of factual public Baghewala test summaries; not ML training rows."""
import csv
from pathlib import Path

DATASET = Path(__file__).resolve().parents[1] / "public_data" / "baghewala_public_test_benchmarks.csv"
SOURCE = "OIL India, Tender CJG3289P15, section 8.2, printed page 69 (PDF page 68)"

def baghewala_benchmarks():
    with DATASET.resolve().open(newline="", encoding="utf-8-sig") as handle:
        rows=list(csv.DictReader(handle))
    for row in rows:
        row["reported_rate_min_klpd"]=float(row["reported_rate_min_klpd"])
        row["reported_rate_max_klpd"]=float(row["reported_rate_max_klpd"])
        row["training_eligible"]=row["training_eligible"].lower()=="true"
    return {"source":SOURCE,"source_url":"https://www.oil-india.com/files/oldtender/global/Doc_CJG3289P15.pdf",
      "scope":"Published historical production-test summaries; one row groups BGW-1 and BGW-4; Punam-1 is a different nearby structure.",
      "data_limit":"No per-well split for grouped rates and no paired CSS steam-cycle inputs. These values are context/validation references, not ML training observations. OIL also reports BOPD alongside KLPD; the unit pairs are reproduced as published, not reconciled here.",
      "production_tests":rows,
      "reported_field_properties":{"reservoir_depth_m":"1050–1300","pay_thickness_m":"5–23","bottom_hole_temperature_c":"50–52","porosity_percent":"18–20","permeability_md":"<1000","oil_viscosity_cp_at_50c":"13650","source_page":"69","source_url":"https://www.oil-india.com/files/oldtender/global/Doc_CJG3289P15.pdf"}}
