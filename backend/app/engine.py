import numpy as np
from scipy.optimize import brentq

BASE_TEMP=47.0  # midpoint of the publicly reported 46–48 °C Baghewala range
BASE_VISC=12000.0

def viscosity(temp_c: float) -> float:
    # Andrade-type screening correlation calibrated only to the stated 50 C field range.
    return float(np.clip(BASE_VISC*np.exp(-0.055*(temp_c-50)), 20, 50000))

def simulate(css, srp):
    steam=css.steam_tonnes; soak=css.soak_hours; st=css.steam_temp_c
    # Lumped screening heat balance; coefficients are assumptions pending cycle-history calibration.
    heat_capacity=steam*0.72
    thermal_gain=heat_capacity*(st-BASE_TEMP)/(heat_capacity+1100)
    soak_maturity=.55+.45*(1-np.exp(-soak/168))
    temp_after_soak=float(np.clip(BASE_TEMP+thermal_gain*soak_maturity,BASE_TEMP,300))
    # Illustrative exponential cooling time constant; not fitted to a Baghewala cycle.
    cooling_tau_days=60.0
    production_days=css.production_days
    average_cooling_factor=cooling_tau_days/production_days*(1-np.exp(-production_days/cooling_tau_days))
    reservoir_temp=float(BASE_TEMP+(temp_after_soak-BASE_TEMP)*average_cooling_factor)
    end_cycle_temp=float(BASE_TEMP+(temp_after_soak-BASE_TEMP)*np.exp(-production_days/cooling_tau_days))
    # Evaluate a period profile from the same model. This is a synthetic forecast curve, not history.
    displacement=0.0005067*(srp.pump_diameter_in**2)*srp.stroke_m*srp.spm*1440
    productivity=0.38
    drawdown=18.0
    def state_at_temperature(temp):
        mu_at_temp=viscosity(temp)
        mobility_at_temp=np.sqrt(BASE_VISC/max(mu_at_temp,20))
        def inflow_balance(q):
            friction=0.025*q*q+0.20*q
            return q-productivity*mobility_at_temp*max(drawdown-friction,0)
        inflow_at_temp=float(brentq(inflow_balance,0,productivity*mobility_at_temp*drawdown))
        friction_at_temp=0.025*inflow_at_temp*inflow_at_temp+0.20*inflow_at_temp
        fillage_at_temp=float(np.clip(0.86-0.12*np.log1p(mu_at_temp/1800)+0.12*mobility_at_temp,.18,.96))
        capacity_at_temp=displacement*srp.efficiency*fillage_at_temp
        fluid_at_temp=min(inflow_at_temp,capacity_at_temp)
        water_cut_at_temp=float(np.clip(.28+.0015*(temp-90),.18,.55))
        return {"temperature":temp,"viscosity":mu_at_temp,"mobility":mobility_at_temp,"inflow":inflow_at_temp,"wellbore_loss":friction_at_temp,"fillage":fillage_at_temp,"capacity":capacity_at_temp,"fluid":fluid_at_temp,"water_cut":water_cut_at_temp,"oil":fluid_at_temp*(1-water_cut_at_temp),"water":fluid_at_temp*water_cut_at_temp}
    average=state_at_temperature(reservoir_temp)
    profile=[]
    for day in np.linspace(0,production_days,17):
        temp=float(BASE_TEMP+(temp_after_soak-BASE_TEMP)*np.exp(-day/cooling_tau_days))
        point=state_at_temperature(temp)
        profile.append({"production_day":round(float(day),2),"reservoir_temp_c":round(temp,1),"oil_rate_m3d":round(point["oil"],2),"viscosity_cp":round(point["viscosity"],1)})
    mu=average["viscosity"]
    mobility=average["mobility"]
    inflow=average["inflow"]
    wellbore_loss=average["wellbore_loss"]
    fillage=average["fillage"]
    capacity=average["capacity"]
    fluid=average["fluid"]
    water_cut=average["water_cut"]
    oil=average["oil"]
    water=average["water"]
    sor=steam/max(oil*css.production_days, .05)
    energy=steam*2.15+srp.spm*srp.stroke_m*118
    # Empirical screening load proxy; not an API TR 11L design calculation.
    polished_load=3.2+0.11*fluid*mu**.12+0.32*srp.stroke_m
    rod_load=polished_load*(.72+.035*srp.spm)
    rod_float=float(np.clip((.5-fillage)*1.25 + max(0,srp.spm-6)*.035,0,1))
    overload=float(np.clip((polished_load-8.5)/5,0,1))
    # No well-specific equipment/formation temperature rating is available, so thermal exposure is not scored.
    thermal_risk=None
    risk=float(np.clip((.45*rod_float+.40*overload)/.85,0,1))
    impact_load=(polished_load-rod_load)/max(polished_load,0.1)
    reliability_index=float(np.clip(1-risk,0,1))
    failure_screen=float(np.clip(.55*overload+.45*rod_float,0,1))
    energy_per_oil=energy/max(oil,.05)
    # Transparent demo economics only; replace with OIL tariffs and steam costs before use.
    assumed_energy_cost_inr_kwh=8.0
    assumed_steam_cost_inr_tonne=1200.0
    daily_cost=energy*assumed_energy_cost_inr_kwh + steam/css.production_days*assumed_steam_cost_inr_tonne
    # Synthetic card shape for visualization, normalized to the computed load proxies.
    x=np.linspace(0,1,81); card_load=rod_load+(polished_load-rod_load)*(.5-.5*np.cos(2*np.pi*x))
    card_load += .15*np.sin(4*np.pi*x)
    return {"reservoir_temp_c":round(reservoir_temp,1),"reservoir_temp_after_soak_c":round(temp_after_soak,1),"reservoir_temp_end_cycle_c":round(end_cycle_temp,1),"thermal_profile":profile,"cooling_time_constant_days":cooling_tau_days,"oil_viscosity_cp":round(mu,1),"mobility_index":round(mobility,3),
      "reservoir_inflow_m3d":round(inflow,2),"wellbore_pressure_loss_bar":round(wellbore_loss,2),"pump_capacity_m3d":round(capacity,2),"pump_fillage":round(fillage,3),
      "fluid_rate_m3d":round(fluid,2),"oil_rate_m3d":round(oil,2),"water_rate_m3d":round(water,2),"water_cut":round(water_cut,3),
      "sor":round(sor,2),"energy_kwhd":round(energy,1),"polished_rod_load_kn":round(polished_load,2),"minimum_rod_load_kn":round(rod_load,2),
      "rod_float_risk":round(rod_float,3),"overload_risk":round(overload,3),"thermal_risk":thermal_risk,"risk_score":round(risk,3),"risk_basis":"normalized rod-float and load screening proxies only; thermal exposure not scored without approved equipment temperature limits",
      "impact_load_index":round(float(np.clip(impact_load,0,1)),3),"failure_screen_index":round(failure_screen,3),"reliability_index":round(reliability_index,3),
      "energy_kwh_per_m3_oil":round(energy_per_oil,1),"estimated_cost_inr_d":round(daily_cost,0),"economics_assumptions":{"energy_cost_inr_kwh":assumed_energy_cost_inr_kwh,"steam_cost_inr_tonne":assumed_steam_cost_inr_tonne,"note":"Illustrative assumptions only; replace with approved field tariffs and steam costs."},
      "dynacard":{"position":x.round(3).tolist(),"load_kn":card_load.round(2).tolist()},
      "assumption_note":"Screening-level, physics-informed synthetic model. Steam injection pressure is retained as an input but excluded from calculations until calibrated pressure/steam-quality, injectivity, and well-integrity data are available. Validate against measured well tests and API-approved design software before operations."}

def optimize(base_css, base_srp, max_risk_score=.55, max_sor=60):
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study=optuna.create_study(directions=["maximize","minimize","minimize"],sampler=optuna.samplers.TPESampler(seed=120))
    def objective(trial):
      steam=trial.suggest_float("steam_tonnes",80,320)
      temp=trial.suggest_float("steam_temp_c",250,320)
      soak=trial.suggest_float("soak_hours",0,252)
      spm=trial.suggest_float("spm",.5,12)
      stroke=trial.suggest_float("stroke_m",.5,5)
      css=base_css.model_copy(update={"steam_tonnes":steam,"steam_temp_c":temp,"soak_hours":soak})
      srp=base_srp.model_copy(update={"spm":spm,"stroke_m":stroke})
      result=simulate(css,srp)
      trial.set_user_attr("computed_risk",result["risk_score"])
      return float(result["oil_rate_m3d"]),float(result["sor"]),float(result["energy_kwhd"])
    study.optimize(objective,n_trials=64)
    candidates=[]
    for trial in study.trials:
      if trial.state != optuna.trial.TrialState.COMPLETE: continue
      p=trial.params
      css=base_css.model_copy(update={"steam_tonnes":p["steam_tonnes"],"steam_temp_c":p["steam_temp_c"],"soak_hours":p["soak_hours"]})
      srp=base_srp.model_copy(update={"spm":p["spm"],"stroke_m":p["stroke_m"]})
      r=simulate(css,srp)
      if r["risk_score"]<=max_risk_score and r["sor"]<=max_sor:
        candidates.append({"oil":r["oil_rate_m3d"],"sor":r["sor"],"energy":r["energy_kwhd"],"params":p,"metrics":r,"css":css.model_dump(),"srp":srp.model_dump()})
    front=[]
    for c in candidates:
      if not any((o["oil"]>=c["oil"] and o["sor"]<=c["sor"] and o["energy"]<=c["energy"] and (o["oil"]>c["oil"] or o["sor"]<c["sor"] or o["energy"]<c["energy"])) for o in candidates): front.append(c)
    candidates.sort(key=lambda x:(-x["oil"],x["sor"],x["energy"]))
    winner=candidates[0] if candidates else None
    return {"recommended":{"css":winner["css"],"srp":winner["srp"]} if winner else {},"metrics":winner["metrics"] if winner else {},
      "pareto":[{"oil_rate_m3d":x["oil"],"sor":x["sor"],"energy_kwhd":x["energy"],**x["params"]} for x in sorted(front,key=lambda x:-x["oil"])[:18]],
      "objective":f"maximize modeled oil rate; minimize SOR and energy; retain only points at or below the user-selected screening filters (risk ≤ {max_risk_score:g}, SOR ≤ {max_sor:g})","method":"Optuna TPE multi-objective search (64 trials); all evaluations use the coupled screening simulator and current fixed well settings.","feasible":winner is not None,"evaluation":{"method":"direct coupled simulator","provenance":"physics-informed synthetic assumptions; not calibrated to field records","fixed_inputs":{"production_days":base_css.production_days,"steam_injection_pressure_bar":base_css.injection_pressure_bar,"pump_diameter_in":base_srp.pump_diameter_in,"pump_efficiency":base_srp.efficiency},"constraint_type":"user-selected exploration filters, not engineering or safety limits"}}
