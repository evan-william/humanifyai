"""
/analyze endpoint: score a text sample without modifying it.
"""

import logging
from fastapi import APIRouter, Request, HTTPException

from api.models.schemas import TextRequest, AnalysisResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=AnalysisResponse, summary="Score text human-likeness")
async def analyze_text(request: Request, body: TextRequest) -> AnalysisResponse:
    """
    Returns a human-likeness score (0–100) and detailed feature breakdown
    for the supplied text. The text is never stored or logged.
    """
    analyzer = request.app.state.analyzer

    try:
        result = analyzer.score(body.text)
    except Exception as exc:
        logger.error("Analyzer error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again.")

    return AnalysisResponse(
        score=result.score,
        grade=result.grade,
        word_count=result.word_count,
        sentence_count=result.sentence_count,
        features=result.features,
        suggestions=result.suggestions,
    )