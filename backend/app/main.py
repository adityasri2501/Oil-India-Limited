from datetime import datetime, timezone
import asyncio, random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from .models import WellState, CSSInput, SRPInput, ScenarioInput, SweepInput, OptimizationInput, OptimizationResult
from .engine import simulate, optimize
from . import db
from .integrations import ADAPTERS
from . import real_training, threew_training
from .public_data import baghewala_benchmarks
from . import nwis

app=FastAPI(title="PS120 Baghewala Digital Twin",version="0.1.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])
well=WellState(timestamp=datetime.now(timezone.utc).isoformat())

def current():
 global well
 out=simulate(well.css,well.srp)
 return {**well.model_dump(),**out,"timestamp":datetime.now(timezone.utc).isoformat()}

@app.get("/api/health")
def health(): return {"status":"ok","model":"coupled screening simulator","source":"synthetic / physics-informed"}
@app.get("/api/wells")
def wells(): return [{"id":well.id,"name":well.name,"source":well.source}]
@app.get("/api/wells/{well_id}/state")
def get_state(well_id:str):
 if well_id!=well.id: return {"error":"well not found"}
 return current()
@app.put("/api/wells/{well_id}/state")
def put_state(well_id:str,state:WellState):
 global well
 if well_id!=well.id: return {"error":"well not found"}
 well=state.model_copy(update={"timestamp":datetime.now(timezone.utc).isoformat()})
 return current()
@app.post("/api/css/simulate")
def css_simulate(css:CSSInput): return simulate(css,well.srp)
@app.post("/api/srp/simulate")
def srp_simulate(srp:SRPInput): return simulate(well.css,srp)
@app.post("/api/production/predict")
def production(css:CSSInput|None=None):
 r=simulate(css or well.css,well.srp)
 return {k:r[k] for k in ("oil_rate_m3d","water_rate_m3d","fluid_rate_m3d","sor","energy_kwhd","reservoir_temp_c","oil_viscosity_cp")}
@app.post("/api/risk/analyze")
def risk():
 r=current()
 return {"risk_score":r["risk_score"],"components":{"rod_float":r["rod_float_risk"],"overload":r["overload_risk"],"thermal_exposure":"not scored"},"level":"high" if r["risk_score"]>.65 else "moderate" if r["risk_score"]>.3 else "low","basis":r["risk_basis"]}
@app.post("/api/optimization/run",response_model=OptimizationResult)
def optimization(request:OptimizationInput): return optimize(request.css,request.srp,request.max_risk_score,request.max_sor)
@app.post("/api/surrogate/predict")
def surrogate_predict(payload:dict):
 try: return real_training.predict(payload)
 except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc))
@app.get("/api/scenarios")
def get_scenarios(): return db.list_scenarios()
@app.post("/api/scenarios")
def save_scenario(s:ScenarioInput):
 r=simulate(s.css,s.srp); item={"name":s.name,"css":s.css.model_dump(),"srp":s.srp.model_dump(),"metrics":r};return db.add_scenario(item)
@app.post("/api/scenarios/sweep")
def sweep_scenarios(request:SweepInput):
 bounds={"steam_tonnes":(20,500),"steam_temp_c":(250,320),"soak_hours":(0,252),"production_days":(1,180),"spm":(.5,12),"stroke_m":(.5,5),"pump_diameter_in":(1,3.5),"efficiency":(.2,1)}
 low,high=bounds[request.variable]
 if any(value<low or value>high for value in request.values): raise HTTPException(status_code=422,detail=f"{request.variable} values must be between {low} and {high}")
 results=[]
 for value in request.values:
  css=request.css.model_copy()
  srp=request.srp.model_copy()
  if request.variable in CSSInput.model_fields: setattr(css,request.variable,value)
  else: setattr(srp,request.variable,value)
  results.append({"value":value,"metrics":simulate(css,srp)})
 return {"variable":request.variable,"fixed_css":request.css.model_dump(),"fixed_srp":request.srp.model_dump(),"method":"Deterministic point-by-point evaluation with the coupled screening simulator; no surrogate values used","results":results}
@app.get("/api/telemetry/live")
def telemetry():
 r=current(); wobble=random.uniform(-.04,.04)
 return {"timestamp":datetime.now(timezone.utc).isoformat(),"source":"synthetic live telemetry","oil_rate_m3d":round(max(.1,r['oil_rate_m3d']*(1+wobble)),2),"tubing_pressure_bar":round(5+r['wellbore_pressure_loss_bar']+random.uniform(-.8,.8),1),"motor_current_a":round(23+well.srp.spm*1.8+random.uniform(-1,1),1),"reservoir_temp_c":round(r['reservoir_temp_c']+random.uniform(-.5,.5),1),"risk_score":r['risk_score']}
@app.get("/api/integrations")
def integrations(): return {name:adapter.readiness() for name,adapter in ADAPTERS.items()}
@app.get("/api/data-sources/ppac")
def ppac_data(): return ADAPTERS["data.gov.in"].crude_production()
@app.get("/api/data-sources/baghewala-public")
def baghewala_public_data(): return baghewala_benchmarks()
@app.get("/api/models/measured")
def measured_model_status(): return real_training.status()
@app.get("/api/models/measured/records")
def measured_records():
 if not real_training.DATA_PATH.exists(): return {"records":[],"source":"No uploaded measured records"}
 import pandas as pd
 frame=pd.read_csv(real_training.DATA_PATH)
 return {"records":frame.tail(300).to_dict(orient="records"),"source":"User-uploaded measured well records","rows":len(frame)}
@app.post("/api/models/measured/train")
async def train_measured_model(request:Request):
 raw=await request.body()
 if len(raw)>25_000_000: raise HTTPException(status_code=413,detail="CSV upload exceeds 25 MB")
 try: return real_training.train(raw.decode("utf-8-sig"))
 except (ValueError,UnicodeDecodeError) as exc: raise HTTPException(status_code=422,detail=str(exc))
@app.get("/api/models/3w/status")
def threew_model_status(): return threew_training.status()
@app.post("/api/models/3w/train")
def train_threew_model():
 try: return threew_training.train()
 except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc))
@app.post("/api/models/3w/predict")
async def predict_threew_episode(request:Request,filename:str="WELL-upload.parquet"):
 raw=await request.body()
 if len(raw)>50_000_000: raise HTTPException(status_code=413,detail="Episode upload exceeds 50 MB")
 try: return threew_training.predict_episode(raw,filename)
 except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc))
@app.post("/api/models/measured/predict")
def predict_measured(payload:dict):
 try: return real_training.predict(payload)
 except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc))
@app.get("/api/integrations/{platform}/discover")
def discover(platform:str,q:str=""):
 adapter=ADAPTERS.get(platform)
 if not adapter: raise HTTPException(status_code=404,detail="Unknown integration platform")
 return adapter.discover(q)
@app.post("/api/integrations/BHASHINI/translate")
def translate(payload:dict):
 text=str(payload.get("text",""))[:5000]
 target=str(payload.get("target_language","hi"))
 source=str(payload.get("source_language","en"))
 allowed={"as","bn","en","gu","hi","kn","ml","mr","or","pa","ta","te"}
 if target not in allowed or source not in allowed: raise HTTPException(status_code=422,detail="Use a supported ISO language code (as, bn, en, gu, hi, kn, ml, mr, or, pa, ta, te)")
 return ADAPTERS["BHASHINI"].translate(text,target,source)
@app.get("/api/nwis/offsets")
def nwis_offsets(radius_km:float=10,md_m:float=2400,formation:str="All",depth_window_m:float=200):
 if not 0.5<=radius_km<=50 or not 0<=md_m<=20000 or not 25<=depth_window_m<=1000: raise HTTPException(status_code=422,detail="Radius, depth, or depth window is outside supported bounds")
 return nwis.offset_analysis(radius_km,md_m,formation,depth_window_m)
@app.get("/api/nwis/events")
def nwis_events(q:str="",formation:str="All",event_type:str="All"):
 return nwis.search_events(q[:150],formation[:80],event_type[:40])
@app.post("/api/nwis/documents/import")
async def nwis_import(request:Request,filename:str="report.txt",source_label:str=""):
 raw=await request.body()
 try: return nwis.ingest_document(filename,raw,source_label)
 except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc))
@app.post("/api/nwis/wells/import")
async def nwis_import_wells(request:Request,filename:str="well_headers.csv",source_label:str=""):
 raw=await request.body()
 try: return nwis.ingest_well_headers(filename,raw,source_label)
 except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc))
@app.post("/api/explain")
def explain(payload:dict):
 r=payload or current()
 return {"summary":f"The coupled screening model estimates {r.get('oil_rate_m3d',0)} m³/d oil at {r.get('reservoir_temp_c',0)} °C reservoir temperature and {r.get('oil_viscosity_cp',0)} cP oil viscosity.","drivers":["CSS steam mass, temperature and soak duration set the lumped reservoir thermal response.","Temperature enters the viscosity correlation, which changes mobility and inflow.","Pump displacement and fillage cap produced fluid; water cut partitions oil and water.","Risk score combines rod-float and load screening proxies; thermal exposure is not scored."],"caveat":"Computed simulator explanation; not an operational recommendation or field-validated prediction."}
@app.websocket("/api/telemetry/ws")
async def ws(websocket:WebSocket):
 await websocket.accept()
 try:
  while True: await websocket.send_json(telemetry()); await asyncio.sleep(2)
 except WebSocketDisconnect: pass
