"""
Health check endpoint — used by load balancers and monitoring.
Does not return sensitive system information.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthResponse, include_in_schema=True)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="1.0.0")