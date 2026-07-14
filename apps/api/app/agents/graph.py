"""
EV Guardian AI — Multi-Agent Orchestration Graph (LangGraph)
================================================================

Defines a graph of specialist agents that collaborate to answer complex
fleet-intelligence questions. A lightweight "Router" node classifies the
incoming question and dispatches to one or more specialist nodes; a final
"Reporting" node synthesizes their outputs into a single coherent answer.

Specialist agents (each a thin wrapper around real backend queries/ML):
  - FleetAgent        -> fleet overview & vehicle status
  - BatteryAgent       -> SOH/RUL/failure-risk predictions (XGBoost-backed)
  - MaintenanceAgent   -> maintenance alerts & scheduling
  - SupplyChainAgent   -> supplier risk scoring
  - CarbonAgent        -> emissions & carbon savings
  - ProcurementAgent   -> replacement ROI recommendations
  - ReportingAgent     -> synthesizes a final natural-language answer (Gemini)

This graph is exposed via POST /api/agents/run and is intentionally
separate from the simpler single-agent /api/chat endpoint: the chat
endpoint is optimized for fast conversational Q&A, while this graph is
used for "Generate fleet report" style requests that benefit from
multiple specialists contributing structured data before a final
narrative is composed.
"""

import os
import logging
import requests
from typing import TypedDict, Optional
from sqlalchemy.orm import Session

from langgraph.graph import StateGraph, END
from app.agents.chat_agent import (
    _tool_get_fleet_overview,
    _tool_get_high_risk_vehicles,
    _tool_get_carbon_summary,
    _tool_get_supplier_risk_summary,
)
from app.models.models import Vehicle, MaintenanceEvent
from app.routers.procurement import _build_recommendation

logger = logging.getLogger("ev_guardian.graph")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# See app/agents/chat_agent.py for why this isn't gemini-2.0-flash anymore
# (shut down by Google 2026-06-01). Keep these two in sync.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


class AgentState(TypedDict):
    query: str
    db: object  # Session, not serializable but fine within a single process run
    route: list[str]
    fleet_data: Optional[dict]
    battery_data: Optional[dict]
    maintenance_data: Optional[dict]
    supply_chain_data: Optional[dict]
    carbon_data: Optional[dict]
    procurement_data: Optional[dict]
    final_report: Optional[str]


def router_node(state: AgentState) -> AgentState:
    q = state["query"].lower()
    route = []
    if any(k in q for k in ["fleet", "overview", "status", "vehicles"]):
        route.append("fleet")
    if any(k in q for k in ["battery", "soh", "degradation", "rul"]):
        route.append("battery")
    if any(k in q for k in ["maintenance", "repair", "failure", "risk"]):
        route.append("maintenance")
    if any(k in q for k in ["supplier", "supply chain", "lithium", "cobalt", "nickel"]):
        route.append("supply_chain")
    if any(k in q for k in ["carbon", "co2", "emission", "net zero", "sustainab"]):
        route.append("carbon")
    if any(k in q for k in ["procure", "replace", "roi", "investment", "buy"]):
        route.append("procurement")

    # "generate fleet report" / generic broad request -> run everything
    if not route or "report" in q or "summar" in q:
        route = ["fleet", "battery", "maintenance", "supply_chain", "carbon", "procurement"]

    state["route"] = route
    return state


def fleet_agent_node(state: AgentState) -> AgentState:
    if "fleet" in state["route"]:
        state["fleet_data"] = _tool_get_fleet_overview(state["db"])
    return state


def battery_agent_node(state: AgentState) -> AgentState:
    if "battery" in state["route"]:
        state["battery_data"] = {
            "high_risk_vehicles": _tool_get_high_risk_vehicles(state["db"], threshold=0.3, limit=10)
        }
    return state


def maintenance_agent_node(state: AgentState) -> AgentState:
    if "maintenance" in state["route"]:
        db = state["db"]
        high_risk = _tool_get_high_risk_vehicles(db, threshold=0.35, limit=10)
        recent_events = (
            db.query(MaintenanceEvent)
            .order_by(MaintenanceEvent.date.desc())
            .limit(10)
            .all()
        )
        state["maintenance_data"] = {
            "vehicles_needing_attention": high_risk,
            "recent_events": [
                {"vehicle_id": e.vehicle_id, "issue": e.issue_type, "date": str(e.date), "status": e.status}
                for e in recent_events
            ],
        }
    return state


def supply_chain_agent_node(state: AgentState) -> AgentState:
    if "supply_chain" in state["route"]:
        state["supply_chain_data"] = _tool_get_supplier_risk_summary(state["db"])
    return state


def carbon_agent_node(state: AgentState) -> AgentState:
    if "carbon" in state["route"]:
        state["carbon_data"] = _tool_get_carbon_summary(state["db"])
    return state


def procurement_agent_node(state: AgentState) -> AgentState:
    if "procurement" in state["route"]:
        db = state["db"]
        vehicles = db.query(Vehicle).order_by(Vehicle.failure_probability.desc()).limit(15).all()
        recs = [_build_recommendation(v) for v in vehicles]
        replace_recs = [r for r in recs if r.recommendation == "replace"]
        state["procurement_data"] = {
            "replace_recommended_count": len(replace_recs),
            "top_recommendations": [r.model_dump() for r in replace_recs[:5]],
        }
    return state


def reporting_agent_node(state: AgentState) -> AgentState:
    """Synthesizes all specialist outputs into one narrative using Gemini.
    Falls back to a structured deterministic summary if no API key is set."""
    sections = {
        "fleet": state.get("fleet_data"),
        "battery": state.get("battery_data"),
        "maintenance": state.get("maintenance_data"),
        "supply_chain": state.get("supply_chain_data"),
        "carbon": state.get("carbon_data"),
        "procurement": state.get("procurement_data"),
    }
    sections = {k: v for k, v in sections.items() if v is not None}

    if GEMINI_API_KEY:
        try:
            prompt = (
                "You are the Reporting Agent in a multi-agent EV fleet intelligence system. "
                "Specialist agents have returned the following structured data (JSON). "
                "Write a concise executive summary (max 200 words) synthesizing the key findings, "
                "highlighting risks and recommended actions. Be specific with numbers and vehicle IDs.\n\n"
                f"Original question: {state['query']}\n\nData:\n{sections}"
            )
            resp = requests.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json={"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
                timeout=30,
            )
            if resp.status_code == 404:
                logger.error(
                    "Reporting agent: Gemini model '%s' not found (HTTP 404) — it may "
                    "have been deprecated. Check https://ai.google.dev/gemini-api/docs/models. "
                    "Falling back to deterministic summary.",
                    GEMINI_MODEL,
                )
                raise RuntimeError("gemini model not found")
            resp.raise_for_status()
            result = resp.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            state["final_report"] = text
            return state
        except Exception:
            logger.exception("Reporting agent: Gemini synthesis failed, falling back to deterministic summary")

    # Deterministic fallback synthesis
    lines = ["Executive Summary (rule-based synthesis — connect Gemini key for full narrative):"]
    if "fleet" in sections:
        f = sections["fleet"]
        lines.append(f"- Fleet: {f['active_vehicles']}/{f['total_vehicles']} active, avg health {f['avg_health_score']}, {f['high_risk_count']} high-risk.")
    if "battery" in sections:
        hv = sections["battery"]["high_risk_vehicles"]
        lines.append(f"- Battery: {len(hv)} vehicles above risk threshold" + (f", top concern {hv[0]['vehicle_id']}" if hv else "."))
    if "carbon" in sections:
        c = sections["carbon"]
        lines.append(f"- Carbon: {c['total_co2_saved_kg']:,.0f} kg CO2 saved (~{c['trees_equivalent']:,.0f} trees/yr equivalent).")
    if "supply_chain" in sections:
        s = sections["supply_chain"]
        lines.append(f"- Supply Chain: {s['high_risk_count']} high-risk suppliers identified.")
    if "procurement" in sections:
        p = sections["procurement"]
        lines.append(f"- Procurement: {p['replace_recommended_count']} vehicles recommended for replacement.")

    state["final_report"] = "\n".join(lines)
    return state


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("router", router_node)
    graph.add_node("fleet_agent", fleet_agent_node)
    graph.add_node("battery_agent", battery_agent_node)
    graph.add_node("maintenance_agent", maintenance_agent_node)
    graph.add_node("supply_chain_agent", supply_chain_agent_node)
    graph.add_node("carbon_agent", carbon_agent_node)
    graph.add_node("procurement_agent", procurement_agent_node)
    graph.add_node("reporting_agent", reporting_agent_node)

    graph.set_entry_point("router")
    # specialists run sequentially (each is a no-op if not in route) then converge on reporting
    graph.add_edge("router", "fleet_agent")
    graph.add_edge("fleet_agent", "battery_agent")
    graph.add_edge("battery_agent", "maintenance_agent")
    graph.add_edge("maintenance_agent", "supply_chain_agent")
    graph.add_edge("supply_chain_agent", "carbon_agent")
    graph.add_edge("carbon_agent", "procurement_agent")
    graph.add_edge("procurement_agent", "reporting_agent")
    graph.add_edge("reporting_agent", END)

    return graph.compile()


_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_agent_graph(db: Session, query: str) -> dict:
    graph = get_compiled_graph()
    result = graph.invoke({
        "query": query,
        "db": db,
        "route": [],
        "fleet_data": None,
        "battery_data": None,
        "maintenance_data": None,
        "supply_chain_data": None,
        "carbon_data": None,
        "procurement_data": None,
        "final_report": None,
    })
    return {
        "route": result["route"],
        "report": result["final_report"],
        "data": {
            "fleet": result.get("fleet_data"),
            "battery": result.get("battery_data"),
            "maintenance": result.get("maintenance_data"),
            "supply_chain": result.get("supply_chain_data"),
            "carbon": result.get("carbon_data"),
            "procurement": result.get("procurement_data"),
        },
    }
