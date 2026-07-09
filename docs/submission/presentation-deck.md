# EV Guardian AI: Industrial EV Supply Chain and Asset Intelligence

This is the markdown source for `EV_Guardian_AI_Submission_Deck.pptx`. Slide numbers match the PPTX 1:1.

## Slide 1 - Title
EV Guardian AI: Industrial EV Supply Chain and Asset Intelligence

An executive command center that gives fleet operators and EV manufacturers the same asset-performance rigour used on conventional industrial equipment — applied to battery health, procurement, supply-chain risk, quality, and carbon.

## Slide 2 - Problem
India registered 2M+ EVs in FY2025, and FAME-II has disbursed ₹10,000+ crore in incentives — yet industrial adoption still lags far behind consumer EVs.

- 2M+ EVs registered in India, FY2025 (SIAM)
- <7% of total vehicle sales are EVs
- <2.5% penetration in industrial/commercial fleets
- 30% commercial EV target for 2030
- Fleet operators lack asset-intelligence tools for EV procurement, battery lifecycle, and maintenance rigour.
- EV manufacturers face battery-grade lithium/cobalt/nickel sourcing risk and cell-to-pack quality traceability gaps.
- Generic fleet and supply-chain tools handle neither problem well.

## Slide 3 - Solution
One platform, both sides of the industrial EV transition:

- Battery APM — SOH, RUL, and failure-risk prediction from telemetry
- Maintenance Optimizer — turns risk into workshop bay, shift, and charger plans
- Procurement & Readiness — route-level electrification readiness, OEM fit, ROI
- Manufacturing Quality — SPC drift detection + ML defect-risk classifier
- Supply Chain & Traceability — supplier risk, geopolitical exposure, cell-to-vehicle genealogy
- Carbon Intelligence — Scope 1/2/3 tracking vs ICE-equivalent baseline

## Slide 4 - Architecture
Core flow: Data sources -> FastAPI + operational store -> ML inference -> specialist agents (LangGraph) -> Next.js command center -> decision outputs.

Specialist agents: Fleet Agent, Battery APM Agent, Maintenance Optimizer, Procurement Readiness Agent, Supply Chain + Traceability Agent, Manufacturing Quality Agent, Carbon Agent, Reporting Agent (Gemini synthesis with a deterministic offline fallback).

Use `docs/submission/architecture-diagram.mmd` or the in-app `/architecture` page for the visual.

## Slide 5 - Battery Asset Performance Management
Two real, held-out-validated XGBoost models — not hardcoded formulas:

- SOH Regressor — high R², low MAE on unseen vehicles; cumulative cycles and brake wear dominate feature importance
- Failure Classifier — accuracy 99.6%, ROC-AUC 0.999
- Remaining Useful Life estimated via degradation-rate extrapolation to an EOL threshold
- Trained on 13,344 telemetry rows across 100 vehicles with physically-grounded aging curves (calendar + cycle aging, Arrhenius temperature acceleration)

## Slide 6 - Maintenance Operations Optimizer
Predictive risk only matters if it becomes an executable plan:

1. Prioritize — immediate, this-week, and monthly jobs ranked by failure probability
2. Allocate — workshop bays assigned against live capacity
3. Schedule — shift windows chosen to avoid operational conflicts
4. Align charging — charger uptime cross-checked against maintenance windows

## Slide 7 - Electrification Readiness & Procurement
A weighted readiness index, validated against an independent baseline rather than presented as a black box:

- Factors: route profile & daily km, payload, dwell time & charger access, OEM model fit, delivery lead time
- Baseline: range margin + health score only (no charger access, payload, or lead time)
- 0.52 correlation between the weighted model and the simple baseline across the fleet
- Divergence concentrates in borderline cases — where the extra signals should matter most
- Validation exposed live at `/api/procurement/readiness-validation`

## Slide 8 - Manufacturing Quality Intelligence
Two complementary techniques, not a single threshold rule:

- SPC (statistical process control) drift detection: per-supplier, per-parameter control-chart z-scores flag process drift before it shows up as a defect-rate spike
- ML defect-risk classifier (XGBoost) trained on 1,800 inspection batches across 20 suppliers — features: weld temperature, torque, cell voltage variance, moisture, electrode thickness
- Held-out test-set performance: precision 0.66, recall 0.41, F1 0.51, ROC-AUC 0.83, accuracy 0.90 — reported transparently at `/api/manufacturing/qc/model-performance`
- Ground truth reflects whether the underlying process was out of statistical control, not the noisy small-sample realized defect rate
- Example live alert: SUP-002 moisture_ppm 3.85σ out of control

## Slide 9 - Supply Chain Risk and Traceability
The supply-chain module combines:

- Battery material supplier risk and geopolitical/weather exposure
- Quality score and on-time delivery, rolled up from inspection history
- Traceability certificate gaps
- Cell lot -> battery pack -> vehicle genealogy

## Slide 10 - Carbon Intelligence
Carbon module tracks:

- Scope 1: zero tailpipe emissions for the EV fleet
- Scope 2: grid electricity emissions (India grid avg ~0.71 kg CO2/kWh)
- Scope 3: upstream battery/material emissions
- ICE-equivalent baseline, class-specific (3W/Sedan/LCV/Truck/Bus each have distinct diesel emission factors)
- Net CO2 saved by route and fleet, ranked by carbon and operational impact together

## Slide 11 - Engineering: Real Stack, Real Tests, Real Security Hygiene
- Technical Stack: FastAPI/SQLAlchemy backend, Next.js/TypeScript/Tailwind/Recharts/Leaflet frontend, XGBoost ML, LangGraph agent routing
- Automated Testing: 17 pytest tests across all 8 API modules, run against an isolated test database, covering SPC drift + ML defect prediction and readiness-vs-baseline validation
- Security Hardening: no live secrets committed (`.env` removed, `.env.example` only), `.gitignore` added, repo size cut from 924MB to ~6MB, dead scaffolding directories removed

## Slide 12 - Demo Walkthrough
1. `/executive` - command-center KPIs and AI-generated insights
2. `/battery` - model transparency and high-risk batteries
3. `/maintenance` - optimized bay/shift/charger maintenance plan
4. `/procurement` - readiness index, OEM fit, baseline validation
5. `/manufacturing` - SPC drift alerts and defect-risk predictions
6. `/supply-chain` - supplier risk and cell-pack-vehicle genealogy
7. `/carbon` - Scope 1/2/3 and ICE-baseline savings

## Slide 13 - Impact & Next Steps
EV Guardian AI addresses all three gaps of the industrial EV transition:

- Adoption gap: gives fleet operators asset intelligence for genuine EV confidence
- Manufacturing gap: gives EV makers supplier, quality-drift, and traceability intelligence
- Net-zero gap: turns electrification targets into ranked, fundable operational actions

Next steps: live telematics/BMS streams, QMS/MES factory connectors, real OEM & dealer lead-time feeds, charger uptime integrations, certificate-level traceability.
