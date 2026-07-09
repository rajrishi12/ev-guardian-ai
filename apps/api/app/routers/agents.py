from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.agents.graph import run_agent_graph

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentRunRequest(BaseModel):
    query: str


@router.post("/run")
def run_agents(payload: AgentRunRequest, db: Session = Depends(get_db)):
    """
    Runs the LangGraph multi-agent pipeline: routes the query to relevant
    specialist agents (Fleet, Battery, Maintenance, Supply Chain, Carbon,
    Procurement), then synthesizes a final report via the Reporting Agent.

    Use for: "Generate fleet report", "Summarize fleet risk and recommend actions", etc.
    """
    return run_agent_graph(db, payload.query)
