# Smart Campus Energy Optimization
**Team:** It worked Yesterday  
**Competition:** BUP CSE Fest 2026 · Smart Campus Energy Optimization Challenge  
**Round:** Online Preliminary

[![Docker Image](https://img.shields.io/badge/docker-nondi06/smartenergy:latest-blue)](https://hub.docker.com/r/nondi06/smartenergy)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)


## 📖 Project Overview

This project provides a robust, LLM-assisted HTTP API service for the **GridWise Smart Campus Energy Optimization Challenge**. The system interprets natural-language operator notes using a Large Language Model (Qwen 3.8 via Groq API), validates them through deterministic guardrails, and generates a cost-optimized 24-hour energy schedule using Linear Programming (PuLP with CBC solver).

### Key Features
✅ **LLM-Powered Interpretation** - Converts natural language operator notes into structured directives  
✅ **Deterministic Guardrails** - Validates all LLM outputs before optimization  
✅ **Mathematical Optimization** - Minimizes grid electricity cost using PuLP/CBC  
✅ **Full Compliance** - Meets all BUP CSE Fest 2026 requirements  
✅ **Production-Ready** - Dockerized with <5s p95 latency  


## 🏗️ Architecture Overview

The system follows a strict, secure **3-stage pipeline**:

```
┌─────────────────────────┐   ┌────────────────────────────┐   ┌─────────────────────┐
│  1. LLM Interpretation  │ → │ 2. Guardrails & Validation │ → │ 3. PuLP Optimizer   │
│  (Qwen 3.8 via Groq)    │   │  (Pydantic + Python)       │   │  (CBC Solver)       │
└─────────────────────────┘   └────────────────────────────┘   └─────────────────────┘
```

### Stage 1: LLM Interpretation
- **Model:** `qwen/qwen3.8-27b` via Groq API
- **Task:** Analyzes 1-3 natural language operator notes
- **Output:** Structured JSON directives (`solar_reduction`, `no_charge_window`, `minimum_battery_reserve`, etc.)

### Stage 2: Deterministic Guardrails
- **Validation:** Hours (0-23), factor (0-1), schema compliance
- **Safety:** Prevents hallucinated constraints from breaking optimization
- **Error Handling:** Controlled failures for malformed inputs

### Stage 3: Mathematical Optimizer
- **Library:** PuLP with CBC solver
- **Objective:** Minimize total grid electricity cost
- **Constraints:** Energy balance, battery physics, end-of-day neutrality, operator directives


## ️ Tech Stack

| Component             | Technology        | Version            |
|:----------------------|:------------------|:-------------------|
| **Backend Framework** | FastAPI + Uvicorn | 0.110+             |
| **LLM Provider**      | Groq API          | -                  |
| **LLM Model**         | Qwen 3.8 27B      | `qwen/qwen3.8-27b` |
| **Optimizer**         | PuLP              | 2.8+               |
| **Solver**            | CBC (Coin-or)     | -                  |
| **Validation**        | Pydantic          | 2.6+               |
| **Python**            | CPython           | 3.11+              |


## 🔐 Environment Variables

Create a `.env` file in the root directory:

```env
# LLM Configuration (REQUIRED)
GROQ_API_KEY=your_groq_api_key_here
MODEL_NAME=qwen/qwen3.8-27b

# Server Configuration (Optional)
HOST=0.0.0.0
PORT=8000
```

**⚠️ Important:** Never commit `.env` files to version control. The `.gitignore` file is configured to exclude them.


## 🚀 Local Setup & Quickstart

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Git

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd smart-campus-energy-optimization
```

### 2. Create and Activate Virtual Environment

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```


## 📡 API Endpoints & Testing

### Interactive API Documentation
Once the server is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Health Check Endpoint
```bash
curl -X GET "http://localhost:8000/health"
```

**Expected Response:**
```json
{
  "status": "ok"
}
```

### Main Optimization Endpoint

**Using cURL:**
```bash
curl -X POST "http://localhost:8000/optimize-energy" \
  -H "Content-Type: application/json" \
  -d @sample_request.json
```

**Using Python:**
```python
import requests
import json

# Load a sample case
with open('BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json', 'r') as f:
    data = json.load(f)

# Extract first case input
sample_input = data['cases'][0]['input']

# Send request
response = requests.post(
    'http://localhost:8000/optimize-energy',
    json=sample_input
)

# Print response
print(json.dumps(response.json(), indent=2))
```

**Sample Request Structure:**
```json
{
  "scenario_id": "SAMPLE-01",
  "operator_notes": [
    "Facilities will wash the rooftop solar panels from noon until 2 PM.",
    "The sports office moved next month's registration deadline."
  ],
  "hours": [
    {
      "hour": 0,
      "demand_kwh": 90,
      "solar_kwh": 0,
      "tariff_bdt_per_kwh": 6
    }
    // ... 23 more hours
  ],
  "battery": {
    "capacity_kwh": 220,
    "initial_energy_kwh": 110,
    "minimum_energy_kwh": 40,
    "max_charge_kwh_per_hour": 50,
    "max_discharge_kwh_per_hour": 50
  }
}
```


## 🧪 Testing with Public Sample Cases

### Run All Test Cases
We provide a comprehensive test script to validate all 10 public sample cases:

```bash
python test_all_samples.py
```

**Expected Output:**
```
🎯 GRIDWISE HACKATHON - COMPLETE TEST SUITE
🏥 Testing /health endpoint...
✅ /health endpoint is working!

Loaded 10 sample cases

Testing: SAMPLE-01 - Solar cleaning + distractor
⏱️  Response time: 2.34s
📊 Expected cost: 38365 BDT
 Actual cost:   38365.0 BDT
✅ PASSED - All checks passed!

...

📈 Total: 10/10 cases passed (100.0%)
 PERFECT SCORE! All tests passed!
```

### Test Individual Cases
```bash
python test_api.py
```


## 🐳 Docker Deployment

### Option 1: Pull from Docker Hub (Recommended)

**Pull the Image:**
```bash
docker pull nondi06/smartenergy:latest
```

**Run the Container:**
```bash
docker run -d -p 8000:8000 \
  --env-file .env \
  --name smartenergy-service \
  nondi06/smartenergy:latest
```

**Verify:**
```bash
curl http://localhost:8000/health
```

**Stop and Remove:**
```bash
docker stop smartenergy-service
docker rm smartenergy-service
```

### Option 2: Build Locally

**Build the Image:**
```bash
docker build -t smart-campus-energy-optimization .
```

**Run the Container:**
```bash
docker run -d -p 8000:8000 \
  --env-file .env \
  --name smartenergy-local \
  smart-campus-energy-optimization
```

### Docker Image Details
- **Registry:** Docker Hub
- **Image:** `nondi06/smartenergy:latest`
- **Size:** ~550 MB
- **Exposed Port:** 8000
- **Base Image:** python:3.11-slim


## 📊 Performance Metrics

| Metric              | Target   | Achieved              |
|:--------------------|:---------|:----------------------|
| **p95 Latency**     | ≤ 5s     | ~2-3s                 |
| **Health Check**    | < 60s    | < 1s                  |
| **Request Timeout** | < 30s    | ~2-12s                |
| **Success Rate**    | > 95%    | 100% (public samples) |
| **Memory Usage**    | < 512 MB | ~200 MB               |


## 📦 Dependencies

### Core Dependencies
```txt
fastapi>=0.110.0
uvicorn>=0.27.1
pulp>=2.8.0
pydantic>=2.6.1
openai>=1.12.0  # Groq API compatible
python-dotenv>=1.0.1
httpx>=0.27.0
```

### Development Dependencies
```txt
pytest>=7.0.0
black>=23.0.0
flake8>=6.0.0
```


## 🎯 Supported Directive Types

| Directive Type | Description | Example Note |
|----------------|-------------|--------------|
| `solar_reduction` | Reduce usable solar during specific hours | "Solar output will drop to 20% from 1 PM to 3 PM" |
| `minimum_battery_reserve` | Keep battery at minimum level | "Keep at least 100 kWh from 6 PM to 9 PM" |
| `no_charge_window` | Battery charging disabled | "Do not charge between 2 PM and 4 PM" |
| `no_discharge_window` | Battery discharging disabled | "Do not discharge from 6 PM to 8 PM" |
| `max_grid_window` | Grid import cap | "Grid must not exceed 155 kWh from 6 PM to 9 PM" |
| `no_op` | Irrelevant note (ignored) | "The cafeteria menu changes tomorrow" |


## 🔍 Validation & Guardrails

The system implements strict validation to ensure correctness:

### LLM Output Validation
✅ **Directive Type:** Must be one of 6 supported types  
✅ **Hours Range:** All hours must be 0-23  
✅ **Hours Order:** Must be unique and ascending  
✅ **Factor Range:** Solar reduction factor must be 0-1  
✅ **Battery Reserve:** Must not exceed capacity  
✅ **Applies Semantics:** `no_op` → `applies=false`, others → `applies=true`

### Energy Constraints Validation
✅ **Energy Balance:** `grid + solar + discharge = demand + charge` (every hour)  
✅ **Battery Bounds:** `minimum ≤ energy ≤ capacity`  
✅ **Rate Limits:** Charge/discharge ≤ max per hour  
✅ **Solar Usage:** `solar_used ≤ effective_solar`  
✅ **End-of-Day Neutrality:** `energy_after[23] = initial_energy`


## ⚠️ Known Limitations

1. **LLM Rate Limits:** The system relies on Groq API. If the API experiences downtime or strict rate limiting, the service returns a controlled 500 error without crashing.

2. **Latency Variance:** While Groq inference is typically fast (0.5-2s), complex cases with multiple directives might take up to 10-12s for LLM inference + optimization, keeping the total p95 latency well under the 30s timeout.

3. **Floating Point Tolerance:** The optimizer uses standard floating-point arithmetic. Minor discrepancies (within 0.01 kWh/BDT) are expected and handled as per the official judge tolerance.

4. **Contradictory Constraints:** As per the problem statement, organizer scoring scenarios will not require mutually contradictory hard directives.

5. **External API Dependency:** Requires valid Groq API credentials. No local model fallback is included in this submission.


## 🏆 Submission Checklist

- [x] **Working API Endpoints:** `/health` and `/optimize-energy`
- [x] **LLM Integration:** Qwen 3.8 via Groq API
- [x] **Deterministic Guardrails:** Full validation implemented
- [x] **Mathematical Optimizer:** PuLP with CBC solver
- [x] **Docker Image:** `nondi06/smartenergy:latest` on Docker Hub
- [x] **README Documentation:** Complete setup and testing instructions
- [x] **Public Sample Tests:** All 10 cases passing
- [x] **Environment Variables:** Properly documented (no secrets committed)
- [x] **Error Handling:** Controlled failures for invalid inputs
- [x] **Performance:** p95 latency < 5s for most cases


## 📞 Team Information

**Team Name:** It worked Yesterday  
**Members:** 
- Tousif Tasrik (Optimizer & Backend Lead)
- Anika Binta Azad Shifa (LLM Integration & API Lead)

**Contact:** tasrik49@gmail.com


## 📄 License

This project is submitted for BUP CSE Fest 2026 Hackathon Preliminary Round.  
All rights reserved.


## 🙏 Acknowledgments

- **BUP CSE Fest 2026** for organizing this challenge
- **Groq** for providing fast LLM inference
- **PuLP** team for the optimization library
- **FastAPI** team for the excellent web framework

---

*Built with ❤️ for the BUP CSE Fest 2026 Hackathon Preliminary Round.*  
*Last Updated: September 2026*

