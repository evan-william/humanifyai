"""
API data models. All user-supplied strings are validated and length-bounded
here so no raw input ever reaches core logic unchecked.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from core.config import settings


class TextRequest(BaseModel):
    text: str = Field(..., description="Input text to process.")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        v = v.strip()
        if len(v) < settings.MIN_TEXT_LENGTH:
            raise ValueError(f"Text must be at least {settings.MIN_TEXT_LENGTH} characters.")
        if len(v) > settings.MAX_TEXT_LENGTH:
            raise ValueError(f"Text exceeds maximum length of {settings.MAX_TEXT_LENGTH} characters.")
        return v


class TransformOptions(BaseModel):
    use_contractions: bool = True
    simplify_formal: bool = True
    vary_sentences: bool = True


class TransformRequest(TextRequest):
    options: TransformOptions = Field(default_factory=TransformOptions)


class AnalysisResponse(BaseModel):
    score: float = Field(..., description="Human-likeness score, 0–100.")
    grade: str = Field(..., description="Letter grade: A, B, C, D, or F.")
    word_count: int
    sentence_count: int
    features: Dict[str, float] = Field(..., description="Per-feature component scores.")
    suggestions: List[str] = Field(..., description="Actionable improvement tips.")


class TransformResponse(BaseModel):
    original_text: str
    transformed_text: str
    before_score: AnalysisResponse
    after_score: AnalysisResponse
    improvement: float = Field(..., description="Score delta after transformation.")


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None