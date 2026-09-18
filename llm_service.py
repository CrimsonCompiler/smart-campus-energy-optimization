import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1" 
)
MODEL_NAME = "qwen/qwen3.8-27b"

# ==========================================
# 1. MASTER SYSTEM PROMPT
# ==========================================
SYSTEM_PROMPT = """
You are an expert energy management system interpreter for a smart campus. 
Your task is to analyze 1 to 3 natural-language operator notes and convert them into a strict JSON array of structured directives.

### SUPPORTED DIRECTIVE TYPES & SCHEMAS:
1. solar_reduction: {"directive_type": "solar_reduction", "structured_adjustment": {"hours": [...], "factor": number}}
2. minimum_battery_reserve: {"directive_type": "minimum_battery_reserve", "structured_adjustment": {"hours": [...], "minimum_energy_kwh": number}}
3. no_charge_window: {"directive_type": "no_charge_window", "structured_adjustment": {"hours": [...]}}
4. no_discharge_window: {"directive_type": "no_discharge_window", "structured_adjustment": {"hours": [...]}}
5. max_grid_window: {"directive_type": "max_grid_window", "structured_adjustment": {"hours": [...], "max_grid_kwh": number}}
6. no_op: {"directive_type": "no_op", "structured_adjustment": null} (For irrelevant notes like cafeteria menus, library hours, etc.)

### CRITICAL RULES (MUST FOLLOW STRICTLY):
1. TIME WINDOWS: Start-inclusive, end-exclusive. 
   - "1 PM to 3 PM" means hours [13, 14]. 
   - "6 PM until 9 PM" means hours [18, 19, 20].
   - "2 AM until 5 AM" means hours [2, 3, 4].
2. SOLAR FACTOR: 'factor' is the USABLE fraction remaining. 
   - "80% reduction" means factor = 0.2. 
   - "drop to 20%" means factor = 0.2. 
   - "leave about half" means factor = 0.5.
3. BATTERY RESERVE: If a note says "50% of battery capacity", calculate it using the provided battery capacity (e.g., 50% of 200 kWh = 100 kWh).
4. HOURS FORMAT: Hours must be unique integers from 0 to 23, sorted in ascending order.
5. APPLIES SEMANTICS: 
   - If directive_type is "no_op", "applies" MUST be false.
   - For ALL other directives, "applies" MUST be true.
6. NO INVENTION: Do not invent demand, tariff, or battery limits. Only interpret the notes.

### OUTPUT FORMAT:
Return a JSON object with a single key "interpretations" containing an array of objects. 
Each object MUST have exactly these keys: "note_index", "applies", "directive_type", "structured_adjustment", "explanation".

Example Output:
{
  "interpretations": [
    {
      "note_index": 0,
      "applies": true,
      "directive_type": "solar_reduction",
      "structured_adjustment": {"hours": [13, 14], "factor": 0.2},
      "explanation": "Solar availability is reduced to 20% during the stated window."
    },
    {
      "note_index": 1,
      "applies": false,
      "directive_type": "no_op",
      "structured_adjustment": null,
      "explanation": "This note does not affect today's energy schedule."
    }
  ]
}
"""

# ==========================================
# 2. LLM API CALL FUNCTION
# ==========================================
def interpret_notes(notes: List[str], battery_capacity: float) -> List[Dict[str, Any]]:
    """
    Takes operator notes and battery capacity, calls LLM, and returns structured directives.
    """
    user_prompt = f"""
    Battery Capacity: {battery_capacity} kWh
    
    Operator Notes:
    {json.dumps([{"index": i, "text": note} for i, note in enumerate(notes)], indent=2)}
    
    Analyze the notes and return the JSON output exactly as specified in the system prompt.
    """

    try:
        # OpenAI API Call with JSON Forcing
        response = client.chat.completions.create(
            model=MODEL_NAME,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1 #
        )
        
        # Parse the JSON response
        raw_content = response.choices[0].message.content
        parsed_json = json.loads(raw_content)
        
        # Extract the interpretations array
        if "interpretations" in parsed_json:
            return parsed_json["interpretations"]
        else:
            raise ValueError("LLM response missing 'interpretations' key.")
            
    except json.JSONDecodeError as e:
        print(f"❌ LLM JSON Parse Error: {e}")
        raise ValueError("LLM returned invalid JSON structure.")
    except Exception as e:
        print(f"❌ LLM API Error: {e}")
        raise RuntimeError(f"Failed to get interpretation from LLM: {str(e)}")