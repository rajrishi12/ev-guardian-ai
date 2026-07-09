from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, fleet, battery, maintenance, supply_chain, carbon, procurement, chat, agents, executive, manufacturing

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-agent digital twin platform for industrial EV fleet & supply chain intelligence.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(fleet.router)
app.include_router(battery.router)
app.include_router(maintenance.router)
app.include_router(supply_chain.router)
app.include_router(carbon.router)
app.include_router(procurement.router)
app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(executive.router)
app.include_router(manufacturing.router)


@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {"status": "healthy"}
