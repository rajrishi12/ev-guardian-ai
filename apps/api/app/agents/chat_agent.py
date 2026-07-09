"""
EV Guardian AI — Chat Assistant Agent
=======================================

Implements a function-calling agent using Gemini. The model is given a set
of "tools" that are thin wrappers around the same SQLAlchemy queries used
by the REST API — so answers the assistant gives are grounded in the real
seeded/predicted data, not hallucinated.

This acts as the entry point that the "Chat Agent" delegates to; in the
LangGraph orchestration layer (see app/agents/graph.py) this is one node
among several specialist agents.
"""

import os
import json
import logging
import requests
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import Vehicle, Supplier, CarbonReport
from app.ml.inference import predict_soh_and_risk, estimate_rul_days
from datetime import date

logger = logging.getLogger("ev_guardian.chat_agent")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# gemini-2.0-flash was shut down by Google on 2026-06-01 — do not revert to it.
# gemini-2.5-flash is the current stable, generally-available, cost-efficient
# model with full function-calling support. Override via env var if Google
# changes the lineup again; check https://ai.google.dev/gemini-api/docs/models
# before changing this.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
GEMINI_TIMEOUT_SECONDS = 20

SYSTEM_INSTRUCTION = """You are the EV Guardian AI assistant, embedded in a Fortune-500-grade
fleet intelligence platform for industrial electric vehicles. You help fleet managers, maintenance
engineers, and executives understand fleet health, battery risk, supply chain risk, maintenance
needs, and carbon impact.

Always ground your answers in the tool results provided to you — never invent vehicle IDs, numbers,
or statistics. Be concise, professional, and specific (cite vehicle IDs, percentages, counts).
If a query is ambiguous, make a reasonable assumption and state it briefly.
"""

TOOLS = [
    {
        "function_declarations": [
            {
                "name": "get_high_risk_vehicles",
                "description": "Returns vehicles whose battery failure probability exceeds a threshold, sorted by risk descending. Use for questions like 'which batteries are at risk' or 'show vehicles needing maintenance'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "threshold": {"type": "number", "description": "Minimum failure probability (0-1), default 0.3"},
                        "limit": {"type": "integer", "description": "Max results, default 10"},
                    },
                },
            },
            {
                "name": "get_fleet_overview",
                "description": "Returns aggregate fleet stats: total vehicles, active count, in-maintenance count, avg health score, avg SOH, high risk count, total distance, total CO2 saved.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_carbon_summary",
                "description": "Returns total CO2 saved, scope 1/2/3 emissions, and tree-equivalent for the whole fleet. Use for 'summarize carbon savings' type questions.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_supplier_risk_summary",
                "description": "Returns supply chain risk breakdown across suppliers (high/medium/low risk counts) and the riskiest suppliers. Use for 'recommend supplier' or supply chain risk questions.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_vehicle_detail",
                "description": "Returns full detail and live battery prediction for one specific vehicle by its ID (e.g. EVG-0042).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vehicle_id": {"type": "string", "description": "Vehicle ID, format EVG-XXXX"},
                    },
                    "required": ["vehicle_id"],
                },
            },
        ]
    }
]


def _tool_get_high_risk_vehicles(db: Session, threshold: float = 0.3, limit: int = 10):
    vehicles = (
        db.query(Vehicle)
        .filter(Vehicle.failure_probability > threshold)
        .order_by(Vehicle.failure_probability.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "vehicle_id": v.vehicle_id,
            "model": v.model,
            "depot": v.depot,
            "soh_pct": v.final_soh_pct,
            "failure_probability": v.failure_probability,
            "health_score": v.health_score,
        }
        for v in vehicles
    ]


def _tool_get_fleet_overview(db: Session):
    total = db.query(Vehicle).count()
    active = db.query(Vehicle).filter(Vehicle.status == "active").count()
    maint = db.query(Vehicle).filter(Vehicle.status == "maintenance").count()
    avg_health = db.query(func.avg(Vehicle.health_score)).scalar() or 0
    avg_soh = db.query(func.avg(Vehicle.final_soh_pct)).scalar() or 0
    high_risk = db.query(Vehicle).filter(Vehicle.failure_probability > 0.4).count()
    total_odo = db.query(func.sum(Vehicle.odometer_km)).scalar() or 0
    total_co2 = db.query(func.sum(CarbonReport.co2_saved_kgco2)).scalar() or 0
    return {
        "total_vehicles": total,
        "active_vehicles": active,
        "in_maintenance": maint,
        "avg_health_score": round(avg_health, 1),
        "avg_soh_pct": round(avg_soh, 1),
        "high_risk_count": high_risk,
        "total_odometer_km": round(total_odo, 0),
        "total_co2_saved_kg": round(total_co2, 0),
    }


def _tool_get_carbon_summary(db: Session):
    total_saved = db.query(func.sum(CarbonReport.co2_saved_kgco2)).scalar() or 0
    total_s2 = db.query(func.sum(CarbonReport.scope2_kgco2)).scalar() or 0
    total_s3 = db.query(func.sum(CarbonReport.scope3_kgco2)).scalar() or 0
    return {
        "total_co2_saved_kg": round(total_saved, 0),
        "total_scope2_kg": round(total_s2, 0),
        "total_scope3_kg": round(total_s3, 0),
        "trees_equivalent": round(total_saved / 21.0, 0),
    }


def _tool_get_supplier_risk_summary(db: Session):
    suppliers = db.query(Supplier).all()
    high = [s for s in suppliers if s.overall_risk_score > 0.5]
    medium = [s for s in suppliers if 0.25 < s.overall_risk_score <= 0.5]
    low = [s for s in suppliers if s.overall_risk_score <= 0.25]
    top5 = sorted(suppliers, key=lambda x: -x.overall_risk_score)[:5]
    best5 = sorted(suppliers, key=lambda x: x.overall_risk_score)[:5]
    return {
        "high_risk_count": len(high),
        "medium_risk_count": len(medium),
        "low_risk_count": len(low),
        "highest_risk_suppliers": [{"name": s.name, "material": s.material, "risk": s.overall_risk_score} for s in top5],
        "lowest_risk_suppliers": [{"name": s.name, "material": s.material, "risk": s.overall_risk_score} for s in best5],
    }


def _tool_get_vehicle_detail(db: Session, vehicle_id: str):
    v = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not v:
        return {"error": f"No vehicle found with ID {vehicle_id}"}

    from app.models.models import Telemetry
    latest = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == vehicle_id)
        .order_by(Telemetry.date.desc())
        .first()
    )
    result = {
        "vehicle_id": v.vehicle_id,
        "model": v.model,
        "depot": v.depot,
        "soh_pct": v.final_soh_pct,
        "health_score": v.health_score,
        "odometer_km": v.odometer_km,
        "status": v.status,
    }
    if latest:
        days_active = (date.today() - v.commission_date).days
        features = {
            "odometer_km": latest.odometer_km,
            "cumulative_cycles": latest.cumulative_cycles,
            "ambient_temp_c": latest.ambient_temp_c,
            "motor_temp_c": latest.motor_temp_c,
            "brake_wear_pct": latest.brake_wear_pct,
            "tyre_wear_pct": latest.tyre_wear_pct,
            "daily_km": latest.daily_km,
            "days_since_commission": days_active,
        }
        pred = predict_soh_and_risk(features)
        rul = estimate_rul_days(latest.soh_pct, latest.cumulative_cycles, days_active)
        result["prediction"] = pred
        result["estimated_rul_days"] = rul
    return result


TOOL_DISPATCH = {
    "get_high_risk_vehicles": _tool_get_high_risk_vehicles,
    "get_fleet_overview": _tool_get_fleet_overview,
    "get_carbon_summary": _tool_get_carbon_summary,
    "get_supplier_risk_summary": _tool_get_supplier_risk_summary,
    "get_vehicle_detail": _tool_get_vehicle_detail,
}


class GeminiAuthError(Exception):
    pass


class GeminiConfigError(Exception):
    pass


class GeminiRateLimitError(Exception):
    pass


def _call_gemini(contents):
    if not GEMINI_API_KEY:
        return None

    resp = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        json={
            "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
            "contents": contents,
            "tools": TOOLS,
        },
        timeout=GEMINI_TIMEOUT_SECONDS,
    )
    if resp.status_code == 401 or resp.status_code == 403:
        raise GeminiAuthError(f"Gemini API rejected the key (HTTP {resp.status_code}): {resp.text[:300]}")
    if resp.status_code == 404:
        raise GeminiConfigError(
            f"Gemini model '{GEMINI_MODEL}' not found (HTTP 404) — it may have been "
            f"deprecated. Check https://ai.google.dev/gemini-api/docs/models and set "
            f"GEMINI_MODEL to a current model. Response: {resp.text[:300]}"
        )
    if resp.status_code == 429:
        raise GeminiRateLimitError(f"Gemini API rate limit / quota exceeded (HTTP 429): {resp.text[:300]}")
    resp.raise_for_status()
    return resp.json()


def run_chat_agent(db: Session, user_message: str, history: list[dict] | None = None) -> dict:
    """
    Runs a tool-calling loop against Gemini. Returns {"reply": str, "data": dict|None, "mode": str}.
    Falls back to a deterministic rule-based responder if no Gemini key is configured
    or if the Gemini call fails, so the demo still works without live API access —
    but unlike before, failures are logged with their real cause instead of being
    silently swallowed, so a bad key / wrong model / rate limit is diagnosable.
    """
    if not GEMINI_API_KEY:
        result = _fallback_response(db, user_message)
        result["mode"] = "fallback_no_key"
        return result

    contents = list(history or [])
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    last_tool_data = None

    for _ in range(4):  # cap tool-call loop
        try:
            result = _call_gemini(contents)
        except GeminiAuthError as e:
            logger.error("Gemini auth failed, falling back to rule-based responder: %s", e)
            fb = _fallback_response(db, user_message)
            fb["mode"] = "fallback_auth_error"
            return fb
        except GeminiConfigError as e:
            logger.error("Gemini config/model error, falling back to rule-based responder: %s", e)
            fb = _fallback_response(db, user_message)
            fb["mode"] = "fallback_config_error"
            return fb
        except GeminiRateLimitError as e:
            logger.warning("Gemini rate limited, falling back to rule-based responder: %s", e)
            fb = _fallback_response(db, user_message)
            fb["mode"] = "fallback_rate_limited"
            return fb
        except requests.exceptions.Timeout:
            logger.warning("Gemini request timed out after %ss, falling back.", GEMINI_TIMEOUT_SECONDS)
            fb = _fallback_response(db, user_message)
            fb["mode"] = "fallback_timeout"
            return fb
        except Exception as e:
            logger.exception("Unexpected error calling Gemini, falling back to rule-based responder")
            fb = _fallback_response(db, user_message)
            fb["mode"] = "fallback_error"
            return fb

        if not result or "candidates" not in result:
            logger.warning("Gemini returned no candidates: %s", result)
            fb = _fallback_response(db, user_message)
            fb["mode"] = "fallback_empty_response"
            return fb

        candidate = result["candidates"][0]
        parts = candidate["content"]["parts"]

        function_call_part = next((p for p in parts if "functionCall" in p), None)

        if function_call_part:
            fn = function_call_part["functionCall"]
            fn_name = fn["name"]
            fn_args = fn.get("args", {})

            contents.append({"role": "model", "parts": [{"functionCall": fn}]})

            tool_fn = TOOL_DISPATCH.get(fn_name)
            try:
                tool_result = tool_fn(db, **fn_args) if tool_fn else {"error": "Unknown tool"}
            except Exception as e:
                logger.exception("Tool '%s' raised an exception", fn_name)
                tool_result = {"error": f"Tool '{fn_name}' failed: {e}"}
            last_tool_data = tool_result

            # Gemini's current API expects the function result back as a
            # non-model turn; the generateContent REST API accepts this as
            # role "user" (matches the current official SDK examples).
            contents.append({
                "role": "user",
                "parts": [{"functionResponse": {"name": fn_name, "response": {"result": tool_result}}}],
            })
            continue

        text_part = next((p for p in parts if "text" in p), None)
        reply_text = text_part["text"] if text_part else "I wasn't able to generate a response."
        return {"reply": reply_text, "data": last_tool_data, "mode": "gemini"}

    return {
        "reply": "I gathered the data but ran out of reasoning steps — please rephrase your question.",
        "data": last_tool_data,
        "mode": "gemini_max_steps",
    }


import re

GREETING_PATTERNS = re.compile(
    r"^\s*(hi+|hello+|hey+|yo|sup|good\s?(morning|afternoon|evening)|namaste|howdy)\b[\s!.?]*$",
    re.IGNORECASE,
)
HELP_PATTERNS = re.compile(
    r"(what can you do|help|capabilities|how do you work|who are you|what are you)",
    re.IGNORECASE,
)
VEHICLE_ID_PATTERN = re.compile(r"\bEVG-?[A-Z0-9]+(?:-[A-Z0-9]+)*\b", re.IGNORECASE)
THANKS_PATTERNS = re.compile(
    r"^\s*(thanks?|thank you|thx|ty|cheers|bye|goodbye|see ya)\b[\s!.?]*$", re.IGNORECASE,
)

CAPABILITIES_TEXT = (
    "I'm the EV Guardian AI assistant. I can help with:\n"
    "- Battery risk & maintenance — \"which vehicles are highest risk?\"\n"
    "- A specific vehicle — \"show me EVG-0042\"\n"
    "- Supply chain — \"which suppliers are highest risk?\"\n"
    "- Carbon savings — \"how much CO2 have we saved?\"\n"
    "- Fleet overview — \"give me a fleet snapshot\"\n\n"
    "What would you like to know?"
)


def _fallback_response(db: Session, message: str) -> dict:
    """Rule-based fallback when GEMINI_API_KEY isn't set, so the chat still demos."""
    msg = message.strip()
    msg_lower = msg.lower()

    if GREETING_PATTERNS.match(msg_lower):
        return {"reply": "Hey! " + CAPABILITIES_TEXT, "data": None}

    if THANKS_PATTERNS.match(msg_lower):
        return {"reply": "You're welcome! Let me know if you need anything else.", "data": None}

    if HELP_PATTERNS.search(msg_lower):
        return {"reply": CAPABILITIES_TEXT, "data": None}

    vehicle_match = VEHICLE_ID_PATTERN.search(msg)
    if vehicle_match:
        raw_id = vehicle_match.group(0).upper()
        suffix = raw_id[3:].lstrip("-")
        vehicle_id = f"EVG-{suffix}"
        data = _tool_get_vehicle_detail(db, vehicle_id)
        if "error" in data:
            reply = data["error"]
        else:
            pred = data.get("prediction", {})
            reply = (
                f"{data['vehicle_id']} ({data['model']}, {data['depot']}): "
                f"SOH {data['soh_pct']}%, health score {round(data['health_score'], 1)}, status {data['status']}."
            )
            if pred:
                reply += f" Predicted failure probability: {pred.get('failure_probability', 0) * 100:.1f}%."
            if data.get("estimated_rul_days") is not None:
                reply += f" Estimated remaining useful life: {data['estimated_rul_days']} days."
        return {"reply": reply, "data": data}

    if "supplier" in msg_lower or "supply chain" in msg_lower:
        data = _tool_get_supplier_risk_summary(db)
        reply = (
            f"Supply chain risk: {data['high_risk_count']} high-risk, {data['medium_risk_count']} medium-risk suppliers. "
            f"Highest risk: {data['highest_risk_suppliers'][0]['name']} ({data['highest_risk_suppliers'][0]['material']})."
        )
        return {"reply": reply, "data": data}

    if "carbon" in msg_lower or "co2" in msg_lower or "emission" in msg_lower:
        data = _tool_get_carbon_summary(db)
        reply = (
            f"The fleet has saved approximately {data['total_co2_saved_kg']:,.0f} kg of CO2 "
            f"compared to equivalent ICE vehicles — equivalent to roughly {data['trees_equivalent']:,.0f} trees planted per year."
        )
        return {"reply": reply, "data": data}

    if "risk" in msg_lower or "maintenance" in msg_lower or "failure" in msg_lower or "battery" in msg_lower:
        data = _tool_get_high_risk_vehicles(db, threshold=0.3, limit=8)
        if data:
            lines = [f"- {d['vehicle_id']} ({d['model']}): {d['failure_probability']*100:.1f}% failure risk, SOH {d['soh_pct']}%" for d in data]
            reply = "Here are the highest-risk vehicles in the fleet:\n" + "\n".join(lines)
        else:
            reply = "No vehicles currently exceed the risk threshold — fleet is in good health."
        return {"reply": reply, "data": data}

    if "fleet" in msg_lower or "overview" in msg_lower or "snapshot" in msg_lower or "summary" in msg_lower:
        data = _tool_get_fleet_overview(db)
        reply = (
            f"Fleet snapshot: {data['active_vehicles']}/{data['total_vehicles']} vehicles active, "
            f"avg health score {data['avg_health_score']}, {data['high_risk_count']} vehicles flagged high-risk."
        )
        return {"reply": reply, "data": data}

    return {
        "reply": (
            "I didn't quite catch that. " + CAPABILITIES_TEXT
        ),
        "data": None,
    }
