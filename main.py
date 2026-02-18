"""
HumanifyAI - Main application entry point.
Initializes FastAPI app, middleware, routers, and startup events.
"""

import sys
import os

# Ensure the project root is in sys.path regardless of how the file is run.
# This is needed when running `python main.py` directly instead of via uvicorn.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.routers import transform, analyze, health
from api.middleware.rate_limit import RateLimitMiddleware
from api.middleware.security import SecurityHeadersMiddleware
from core.config import settings
from core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting HumanifyAI...")
    # Warm up the analyzer model on startup
    from core.analyzer import HumanLikenessAnalyzer
    app.state.analyzer = HumanLikenessAnalyzer()
    app.state.analyzer.load()
    logger.info("Analyzer ready.")
    yield
    logger.info("Shutting down HumanifyAI.")


app = FastAPI(
    title="HumanifyAI",
    description="Transform AI-generated text to sound more human.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# --- Middleware ---
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=60, window_seconds=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# --- Static files & templates ---
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

# --- Routers ---
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(transform.router, prefix="/api/v1", tags=["transform"])
app.include_router(analyze.router, prefix="/api/v1", tags=["analyze"])

# --- Dashboard (web UI) ---
from api.routers import dashboard as dashboard_router
app.include_router(dashboard_router.router, tags=["dashboard"])