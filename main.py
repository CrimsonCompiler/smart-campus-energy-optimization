from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

# Member 1 এর তৈরি করা Optimizer ইম্পোর্ট করা
from optimizer import GridWiseOptimizer

load_dotenv()

app = FastAPI(title="GridWise LLM Energy Optimizer")

# ==========================================
# 1. Request & Response Schema (Pydantic Models)
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
    battery_action: str  # "charge", "discharge", or "idle"
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
# 2. API Endpoints
# ==========================================
@app.get("/health")
def health_check():
    """জাজ চেক করবে সার্ভার চালু আছে কিনা"""
    return {"status": "ok"}

@app.post("/optimize-energy", response_model=OptimizeResponse)
def optimize_energy(request: OptimizeRequest):
    """মেইন এন্ডপয়েন্ট: LLM ইন্টারপ্রিটেশন + অপ্টিমাইজেশন"""
    try:
        # ধাপ ১: LLM ইন্টারপ্রিটেশন (Member 2 এর মূল কাজ)
        # আপাতত একটি Mock ফাংশন ব্যবহার করা হচ্ছে। পরে এটি OpenAI/Gemini API কল দিয়ে রিপ্লেস করতে হবে।
        directives = mock_llm_interpretation(request.operator_notes)
        
        # ধাপ ২: Guardrail Validation (Member 2 এর কাজ)
        validated_directives = validate_directives(directives, request.battery.capacity_kwh)
        
        # ধাপ ৩: অপ্টিমাইজেশন (Member 1 এর কাজ - যা ইতিমধ্যে পারফেক্ট!)
        optimizer = GridWiseOptimizer(
            hours_data=[h.model_dump() for h in request.hours],
            battery_data=request.battery.model_dump(),
            directives=validated_directives
        )
        
        # ধাপ ৪: ফাইনাল রেসপন্স জেনারেট করা
        result = optimizer.solve_and_build_response(request.scenario_id)
        return result
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Validation Error: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# ==========================================
# 3. Helper Functions (Member 2 এগুলো ইমপ্লিমেন্ট করবে)
# ==========================================
def mock_llm_interpretation(notes: List[str]) -> List[Dict[str, Any]]:
    """
    TODO: Member 2 এখানে OpenAI/Gemini API কল করবে। 
    টেস্টিংয়ের জন্য আপাতত সব নোটকে 'no_op' ধরা হচ্ছে।
    """
    return [
        {
            "note_index": i,
            "applies": False,
            "directive_type": "no_op",
            "structured_adjustment": None,
            "explanation": "Mock: LLM not connected yet. Treated as no_op."
        }
        for i in range(len(notes))
    ]

def validate_directives(directives: List[Dict[str, Any]], battery_capacity: float) -> List[Dict[str, Any]]:
    """
    TODO: Member 2 এখানে LLM আউটপুটের কড়া ভ্যালিডেশন (Guardrails) করবে।
    """
    allowed_types = ["solar_reduction", "minimum_battery_reserve", "no_charge_window", 
                     "no_discharge_window", "max_grid_window", "no_op"]
    
    for d in directives:
        if d["directive_type"] not in allowed_types:
            raise ValueError(f"Invalid directive_type: {d['directive_type']}")
        
        if d["applies"] and d.get("structured_adjustment") and "hours" in d["structured_adjustment"]:
            hrs = d["structured_adjustment"]["hours"]
            if not all(0 <= h <= 23 for h in hrs):
                raise ValueError(f"Hours must be 0-23. Got: {hrs}")
            if hrs != sorted(list(set(hrs))):
                raise ValueError(f"Hours must be unique and ascending. Got: {hrs}")
                
    return directives

if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0 তে বাইন্ড করা জরুরি যাতে Docker বা বাইরে থেকে এক্সেস করা যায়
    uvicorn.run(app, host="0.0.0.0", port=8000)