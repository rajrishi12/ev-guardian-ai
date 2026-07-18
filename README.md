# EV Guardian AI

EV Guardian AI is an intelligent command center for industrial EV fleets and manufacturing operations. It unifies battery health forecasting, maintenance planning, procurement readiness, supply-chain risk monitoring, manufacturing quality intelligence, and carbon tracking into a single decision-support platform.

The platform features an advanced AI Chat Assistant System that acts as the conversational interface for the command center. Powered by a production-ready LLM integration with rule-based fallback protocols, the assistant allows fleet managers and operators to query real-time database metrics, surface grounded fleet diagnostics, and generate multi-agent executive reporting through natural language.

## Problem Statement
The rapid shift to electrification is creating new operational challenges across fleet management, battery lifecycle planning, supplier resilience, manufacturing quality, and sustainability reporting. Organizations need a system that can turn fragmented operational data into timely, explainable decisions.

## Solution Overview
EV Guardian AI combines a FastAPI backend, a Next.js web experience, and ML-powered analytics to provide:
- Battery degradation prediction and failure-risk detection
- Predictive maintenance prioritization and scheduling
- Electrification readiness scoring for vehicle replacement and deployment decisions
- Supply-chain visibility for supplier risk, lead-time exposure, and traceability gaps
- Manufacturing defect detection and quality drift monitoring
- Carbon accounting against an ICE-equivalent baseline

## What the Platform Does
### 1. Battery Intelligence
- Predicts state of health (SOH) and failure probability
- Identifies high-risk vehicles and assets
- Supports explainable battery lifecycle planning

### 2. Operations and Maintenance
- Converts predicted risk into actionable maintenance workflows
- Optimizes workshop scheduling using capacity, charger constraints, and urgency

### 3. Procurement and Electrification Readiness
- Scores vehicles for readiness to electrify based on route profile, payload, dwell time, charger access, OEM fit, and delivery lead time
- Provides transparent replacement, monitor, and retain recommendations

### 4. Supply Chain and Manufacturing
- Surfaces supplier exposure, material risk, and lead-time pressure
- Trained XGBoost defect-risk classifier over process parameters (weld temperature, torque, cell voltage variance, moisture, electrode thickness), reporting precision/recall/F1/ROC-AUC on a held-out test set
- SPC (statistical process control) drift detection flags out-of-control process parameters per supplier before they show up as a defect-rate spike
- Connects traceability from cell lot and pack ID to the fielded vehicle

### 5. Carbon Intelligence
- Quantifies emissions impact using Scope 1/2/3 logic
- Compares EV operation with ICE-equivalent performance for auditable sustainability reporting

## Technical Stack
- Backend: FastAPI, SQLAlchemy, SQLite or PostgreSQL, Pydantic
- Frontend: Next.js, TypeScript, Tailwind CSS, Recharts, Leaflet, TanStack Query
- ML: XGBoost-based regression and classification models
- AI Assistant: Gemini-powered responses with a rule-based fallback for offline/demo use

## Local Run Guide
### 1. Configure environment variables
Create a local environment file in [apps/api](apps/api) with:

```powershell
$env:GEMINI_API_KEY="your_gemini_api_key_here"
$env:DATABASE_URL="sqlite:///./evguardian.db"
```

For a persistent production-style setup, you can also use PostgreSQL:

```powershell
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/evguardian"
```

### 2. Backend
```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
```

Trained model artifacts already ship in `apps/api/app/ml/artifacts/`. To regenerate the dataset and retrain from scratch:
```powershell
cd apps/ml
python data/generate_dataset.py
python training/train_battery_model.py
python training/train_quality_model.py
```

### 2b. Run the test suite
```powershell
cd apps/api
pytest tests/ -v
```
17 tests cover fleet, battery, procurement (including readiness-vs-baseline validation), carbon, supply-chain, and manufacturing (SPC drift + ML defect prediction) endpoints against an isolated SQLite test database — never the demo `evguardian.db`.

### 3. Frontend
```powershell
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000

### Getting the AI assistant working (Gemini)
Without a key, the assistant runs in **rule-based fallback mode** — pattern matching on a fixed set of intents (greetings, risk/battery, supplier, carbon, fleet overview, direct vehicle lookup). It's honest and functional but not real language understanding.

To get the actual AI-powered assistant:
1. Get a free API key at [Google AI Studio](https://aistudio.google.com/apikey).
2. Add it to `apps/api/.env` (copy from `.env.example` first): `GEMINI_API_KEY=your_key_here`.
3. Restart the backend. Visit `/assistant` in the app — a badge in the top-right of the chat card shows **"AI mode (Gemini)"** vs **"Rule-based mode"** so it's never ambiguous which is answering. You can also check `GET /api/chat/status` directly.

- The app reads both `GEMINI_API_KEY` and `DATABASE_URL` from the environment.
- For demos and local testing, SQLite is the fastest option; for a more persistent deployment-style setup, PostgreSQL is recommended.

