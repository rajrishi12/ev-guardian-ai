# Demo Video Script

Target length: 3 to 4 minutes.

## Recording setup
- Backend: `cd apps/api`; run `uvicorn app.main:app --reload --port 8000`.
- Frontend: `cd apps/web`; run `npm run dev`.
- Browser: open `http://localhost:3000/executive`.
- Optional prompt for assistant: "Generate a fleet risk and net-zero report."

## Evidence points to emphasize for evaluation
- Battery degradation prediction: highlight the SOH regressor and failure classifier metrics, and say predictions are benchmarked against observed degradation trajectories.
- Supply chain risk detection lead time: show supplier risk surfacing before disruption using material risk, geography, lead time, and quality trends.
- Manufacturing defect detection: show how incoming inspection defect rates and supplier quality signals are turned into early quality-drift warnings.
- Fleet electrification readiness scoring: explain that the readiness score is compared against operational reality and expert-style decision logic, with confidence and rationale.
- Carbon tracking accuracy: point to the Scope 1/2/3 breakdown and the ICE-equivalent baseline as a transparent, auditable measure of emission impact.

## 0:00-0:20 - Opening
Show `/executive`.

Talk track:
"EV Guardian AI is an executive command center for industrial EV fleets and EV manufacturing supply chains. It connects battery asset performance, maintenance operations, procurement readiness, supplier risk, traceability, and carbon intelligence in one AI layer."

## 0:20-0:50 - Executive command center
Stay on `/executive`.

Show:
- Fleet health score
- Battery SOH
- Maintenance due
- Supplier risk
- Procurement savings estimate
- AI insights

Talk track:
"The executive view rolls up live operational data into decision metrics. The same vehicle, supplier, maintenance, and carbon records drive every page, so the platform is consistent from board-level view to asset-level action. This is where we make fleet health, supplier exposure, maintenance urgency, procurement readiness, and net-zero progress visible in one place."

## 0:50-1:20 - Battery APM
Go to `/battery`, then optionally click a high-risk vehicle from `/fleet`.

Show:
- Model performance card
- High-risk vehicle list
- Battery SOH/RUL/failure probability

Talk track:
"The battery APM layer estimates state of health, failure probability, and remaining useful life. It behaves like APM for industrial equipment, but tuned for EV batteries, thermal stress, cycles, and duty pattern. We explicitly surface model transparency and benchmark the degradation forecast against observed battery behavior so the prediction quality is explainable, not just accurate-looking."

## 1:20-1:55 - Maintenance optimizer
Go to `/maintenance`.

Show:
- Immediate/weekly/monthly counts
- Optimizer summary
- Depot capacity
- Optimized maintenance schedule

Talk track:
"Alerts are not enough. The optimizer converts predicted risk into a real workshop plan using bay capacity, shift windows, charger requirements, and charger uptime. This is how predictive maintenance becomes executable operations."

## 1:55-2:30 - Procurement readiness
Go to `/procurement`.

Show:
- Electrification readiness table
- Route profile
- Payload
- Dwell time
- Charger access score
- OEM fit and lead time

Talk track:
"Procurement is scored as a readiness problem, not just a replacement ROI problem. For every asset, the platform evaluates duty cycle, payload, dwell window, charging access, OEM battery fit, and delivery lead time, then recommends whether the asset is ready now, a pilot candidate, or blocked by infrastructure. The output includes a confidence score and rationale, so the readiness assessment can be compared against expert judgment rather than treated as a black box."

## 2:30-3:05 - Supply chain and traceability
Go to `/supply-chain`.

Show:
- Risk by material
- Highest-risk suppliers
- Cell-to-pack-to-vehicle genealogy
- Traceability gaps

Talk track:
"The manufacturing side tracks battery material and supplier risk, then links that risk through cell lot, pack ID, and vehicle assignment. This gives EV makers and fleet operators a shared traceability view across quality, supplier risk, and fielded assets. The system also turns incoming inspection defect rates into early defect-detection signals, helping teams prioritise quality issues before they cascade into field failures."

## 3:05-3:30 - Carbon intelligence
Go to `/carbon`.

Show:
- CO2 saved
- Scope 1/2/3
- Monthly CO2 saved chart

Talk track:
"The carbon layer compares EV operation to an ICE-equivalent baseline and separates Scope 1, Scope 2, and Scope 3 impact. Net-zero progress is tied to real routes and assets, not abstract reporting. That makes the carbon intelligence auditable and directly comparable to measured operational outcomes."

## 3:30-3:55 - Architecture close
Go to `/architecture`.

Show:
- Data ingestion
- Digital twin
- ML intelligence
- Agent layer
- Decision outputs

Talk track:
"The architecture combines data ingestion, digital twins, ML inference, and specialist agents. Each agent contributes structured intelligence, and the reporting layer synthesizes fleet, battery, maintenance, procurement, supply-chain, and carbon outputs for decision makers."

## 3:55-4:00 - Closing
Talk track:
"EV Guardian AI accelerates industrial EV adoption by giving operators and manufacturers the asset intelligence, supply-chain visibility, and net-zero accountability needed to scale with confidence. In short, it turns battery performance, supplier risk, manufacturing quality, electrification readiness, and carbon tracking into one decision-ready AI layer for the industrial EV transition."
