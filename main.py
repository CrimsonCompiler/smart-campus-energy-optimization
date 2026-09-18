from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

from optimizer import GridWiseOptimizer

from llm_service import interpret_notes

load_dotenv()

app = FastAPI(title="smart-campus-energy-optimization")

# ==========================================
# Pydantic Models (Request & Response Schema)
# ==========================================
class HourData(BaseModel):
    hour: int
    demand_kwh: float
    solar_kwh: float
    tariff_bdt_per_kwh: float

class BatteryData(BaseModel):
    capacity_kwh: float
    initial_energy_kwh: float
    minimum_energy_kwh: float
    max_charge_kwh_per_hour: float
    max_discharge_kwh_per_hour: float

class OptimizeRequest(BaseModel):
    scenario_id: str
    operator_notes: List[str]
    hours: List[HourData]
    battery: BatteryData

class DirectiveInterpretation(BaseModel):
    note_index: int
    applies: bool
    directive_type: str
    structured_adjustment: Optional[Dict[str, Any]] = None
    explanation: str

class HourlyPlanEntry(BaseModel):
    hour: int
    grid_kwh: float
    solar_used_kwh: float
    battery_action: str
    battery_kwh: float
    battery_energy_after_kwh: float

class OptimizeResponse(BaseModel):
    scenario_id: str
    directive_interpretation: List[DirectiveInterpretation]
    hourly_plan: List[HourlyPlanEntry]
    total_grid_kwh: float
    total_cost_bdt: float
    peak_grid_kwh: float
    plan_summary: str

# ==========================================
# Guardrail Validation
# ==========================================
def validate_directives(directives: List[Dict[str, Any]], battery_capacity: float) -> List[Dict[str, Any]]:
    allowed_types = [
        "solar_reduction", "minimum_battery_reserve", "no_charge_window", 
        "no_discharge_window", "max_grid_window", "no_op"
    ]
    
    for d in directives:
        # Check directive_type
        if d.get("directive_type") not in allowed_types:
            raise ValueError(f"Invalid directive_type: {d.get('directive_type')}")
        
        # Check applies semantics
        if d["directive_type"] == "no_op":
            if d.get("applies") != False:
                raise ValueError("no_op must have applies=false")
            if d.get("structured_adjustment") is not None:
                raise ValueError("no_op must have structured_adjustment=null")
        else:
            if d.get("applies") != True:
                raise ValueError(f"Non-no_op directive must have applies=true")
        
        # Validate structured_adjustment
        adj = d.get("structured_adjustment")
        if adj and "hours" in adj:
            hrs = adj["hours"]
            if not all(isinstance(h, int) and 0 <= h <= 23 for h in hrs):
                raise ValueError(f"Hours must be integers 0-23. Got: {hrs}")
            if hrs != sorted(list(set(hrs))):
                raise ValueError(f"Hours must be unique and ascending. Got: {hrs}")
            
            # Solar factor check
            if d["directive_type"] == "solar_reduction":
                factor = adj.get("factor")
                if factor is None or not (0 <= factor <= 1):
                    raise ValueError(f"Solar factor must be 0-1. Got: {factor}")
            
            # Battery reserve check
            if d["directive_type"] == "minimum_battery_reserve":
                min_e = adj.get("minimum_energy_kwh")
                if min_e is None or min_e < 0 or min_e > battery_capacity:
                    raise ValueError(f"Battery reserve must be 0-{battery_capacity}. Got: {min_e}")
            
            # Max grid check
            if d["directive_type"] == "max_grid_window":
                max_g = adj.get("max_grid_kwh")
                if max_g is None or max_g < 0:
                    raise ValueError(f"Max grid must be non-negative. Got: {max_g}")
                
    return directives

# ==========================================
# API Endpoints
# ==========================================
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/optimize-energy", response_model=OptimizeResponse)
async def optimize_energy(request: OptimizeRequest):
    try:
        raw_directives = interpret_notes(
            notes=request.operator_notes, 
            battery_capacity=request.battery.capacity_kwh
        )
        
        validated_directives = validate_directives(raw_directives, request.battery.capacity_kwh)
        
        optimizer = GridWiseOptimizer(
            hours_data=[h.model_dump() for h in request.hours],
            battery_data=request.battery.model_dump(),
            directives=validated_directives
        )
        
        result = optimizer.solve_and_build_response(request.scenario_id)
        return result
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Validation Error: {str(ve)}")
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(re)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)