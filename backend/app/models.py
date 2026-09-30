from pydantic import BaseModel, Field

class CSSInput(BaseModel):
    steam_tonnes: float = Field(180, ge=20, le=500)
    steam_temp_c: float = Field(300, ge=250, le=320)
    # Logged for traceability only until a well-specific pressure/steam-quality relation is calibrated.
    injection_pressure_bar: float = Field(0, ge=0, le=250)
    soak_hours: float = Field(200, ge=0, le=252)
    production_days: float = Field(30, ge=1, le=180)

class SRPInput(BaseModel):
    spm: float = Field(3.5, ge=0.5, le=12)
    # Set to zero when the field setting is not supplied; no drive-to-SPM calibration is assumed.
    vfd_frequency_hz: float = Field(0, ge=0, le=60)
    stroke_m: float = Field(2.8, ge=0.5, le=5)
    pump_diameter_in: float = Field(2.0, ge=1, le=3.5)
    efficiency: float = Field(.78, ge=.2, le=1)

class CSSState(CSSInput):
    cycle_phase: str = "production"

class ReservoirState(BaseModel):
    temperature_c: float
    viscosity_cp: float
    mobility_index: float
    inflow_m3d: float

class WellboreState(BaseModel):
    inflow_m3d: float
    produced_fluid_m3d: float
    tubing_pressure_bar: float

class SRPState(SRPInput):
    displacement_m3d: float
    pump_capacity_m3d: float
    fillage: float
    polished_rod_load_kn: float
    minimum_rod_load_kn: float

class ProductionState(BaseModel):
    oil_rate_m3d: float
    water_rate_m3d: float
    fluid_rate_m3d: float
    water_cut: float
    sor: float
    energy_kwhd: float

class RiskState(BaseModel):
    score: float
    rod_float: float
    overload: float
    thermal_exposure: float | None = None
    level: str

class OptimizationResult(BaseModel):
    recommended: dict
    metrics: dict
    pareto: list[dict]
    feasible: bool
    objective: str
    method: str
    evaluation: dict

class WellState(BaseModel):
    id: str = "BGW-001"
    name: str = "Baghewala demonstration well 001"
    source: str = "synthetic / physics-informed"
    css: CSSState = CSSState()
    srp: SRPInput = SRPInput()
    reservoir_temp_c: float = 120
    oil_viscosity_cp: float = 12000
    oil_rate_m3d: float = 4
    water_rate_m3d: float = 2
    sor: float = 2.8
    energy_kwhd: float = 650
    risk_score: float = .2
    timestamp: str = ""

class ScenarioInput(BaseModel):
    name: str = "Scenario"
    css: CSSInput
    srp: SRPInput

class SweepInput(BaseModel):
    variable: str = Field("steam_tonnes", pattern="^(steam_tonnes|steam_temp_c|soak_hours|production_days|spm|stroke_m|pump_diameter_in|efficiency)$")
    values: list[float] = Field(min_length=2, max_length=31)
    css: CSSInput
    srp: SRPInput

class OptimizationInput(BaseModel):
    css: CSSInput
    srp: SRPInput
    max_risk_score: float = Field(.55, ge=0, le=1)
    max_sor: float = Field(60, gt=0, le=1000)

