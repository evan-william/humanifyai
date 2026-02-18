"""
/transform endpoint: apply humanization transformations and return
before/after scores so the caller can see what changed.
"""

import logging
from fastapi import APIRouter, Request, HTTPException

from api.models.schemas import TransformRequest, TransformResponse, AnalysisResponse
from core.transformer import TextTransformer

router = APIRouter()
logger = logging.getLogger(__name__)


def _build_analysis_response(result) -> AnalysisResponse:
    return AnalysisResponse(
        score=result.score,
        grade=result.grade,
        word_count=result.word_count,
        sentence_count=result.sentence_count,
        features=result.features,
        suggestions=result.suggestions,
    )


@router.post("/transform", response_model=TransformResponse, summary="Humanize AI-generated text")
async def transform_text(request: Request, body: TransformRequest) -> TransformResponse:
    """
    Transforms the supplied text to sound more human and returns the result
    alongside before/after human-likeness scores. Text is processed in memory
    and never persisted.
    """
    analyzer = request.app.state.analyzer
    opts = body.options

    transformer = TextTransformer(
        use_contractions=opts.use_contractions,
        simplify_formal=opts.simplify_formal,
        vary_sentences=opts.vary_sentences,
    )

    try:
        before_result = analyzer.score(body.text)
        transformed = transformer.transform(body.text)
        after_result = analyzer.score(transformed)
    except Exception as exc:
        logger.error("Transform error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Transformation failed. Please try again.")

    return TransformResponse(
        original_text=body.text,
        transformed_text=transformed,
        before_score=_build_analysis_response(before_result),
        after_score=_build_analysis_response(after_result),
        improvement=round(after_result.score - before_result.score, 1),
    )