from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.telemetry.middleware import RequestTelemetryMiddleware


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Backend API for CAT Cost Intelligence "
        "opportunity analysis and recommendation workflows."
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5432",
        "http://127.0.0.1:4321",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestTelemetryMiddleware)


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "environment": settings.app_env,
        "docs": "/docs",
    }


app.include_router(
    api_router,
    prefix=settings.api_v1_prefix,
)
