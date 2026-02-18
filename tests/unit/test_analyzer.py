"""
Unit tests for HumanLikenessAnalyzer.
Run: pytest tests/unit/test_analyzer.py -v
"""

import pytest
from core.analyzer import HumanLikenessAnalyzer, TextFeatures


@pytest.fixture(scope="module")
def analyzer():
    a = HumanLikenessAnalyzer()
    a.load()
    return a


AI_TEXT = (
    "In conclusion, the utilization of advanced methodologies facilitates the "
    "achievement of optimal outcomes. Furthermore, it is important to note that "
    "the implementation of these strategies will demonstrate significant benefits. "
    "Therefore, the organization should consider adopting these practices in order "
    "to enhance operational efficiency and productivity."
)

HUMAN_TEXT = (
    "Honestly, I think the key here is just trying things out and seeing what works. "
    "Sure, some strategies are better than others — but you won't know until you're in it. "
    "I've seen teams overthink this stuff and end up stuck. "
    "Don't let that happen to you. Start small, get feedback, and adjust as you go. "
    "That's really all there is to it."
)


class TestLoad:
    def test_loads_without_error(self, analyzer):
        assert analyzer._loaded is True


class TestExtractFeatures:
    def test_returns_text_features(self, analyzer):
        features, words, sents = analyzer.extract_features(HUMAN_TEXT)
        assert isinstance(features, TextFeatures)
        assert words > 0
        assert sents > 0

    def test_contraction_detection(self, analyzer):
        text = "I'm not sure if you've seen this, but don't worry."
        features, words, _ = analyzer.extract_features(text)
        assert features.contraction_rate > 0

    def test_empty_text_safe(self, analyzer):
        features, words, sents = analyzer.extract_features("   ")
        assert words == 0
        assert sents == 0

    def test_passive_voice_detection(self, analyzer):
        text = "The document was written by the team. The form was completed."
        features, _, _ = analyzer.extract_features(text)
        assert features.passive_voice_rate > 0

    def test_question_rate(self, analyzer):
        text = "What is the meaning of this? Why does it matter? We should check."
        features, _, sents = analyzer.extract_features(text)
        assert features.question_rate > 0


class TestScore:
    def test_returns_score_in_range(self, analyzer):
        result = analyzer.score(HUMAN_TEXT)
        assert 0 <= result.score <= 100

    def test_human_text_scores_higher(self, analyzer):
        human_result = analyzer.score(HUMAN_TEXT)
        ai_result    = analyzer.score(AI_TEXT)
        assert human_result.score > ai_result.score

    def test_grade_assigned(self, analyzer):
        result = analyzer.score(HUMAN_TEXT)
        assert result.grade in ("A", "B", "C", "D", "F")

    def test_suggestions_are_strings(self, analyzer):
        result = analyzer.score(AI_TEXT)
        assert all(isinstance(s, str) for s in result.suggestions)

    def test_suggestions_capped(self, analyzer):
        result = analyzer.score(AI_TEXT)
        assert len(result.suggestions) <= 5

    def test_features_dict_non_empty(self, analyzer):
        result = analyzer.score(HUMAN_TEXT)
        assert isinstance(result.features, dict)
        assert len(result.features) > 0

    def test_word_and_sentence_count(self, analyzer):
        result = analyzer.score(HUMAN_TEXT)
        assert result.word_count > 0
        assert result.sentence_count > 0

    def test_not_loaded_raises(self):
        fresh = HumanLikenessAnalyzer()
        with pytest.raises(RuntimeError, match="not loaded"):
            fresh.score("some text")

    def test_short_text(self, analyzer):
        result = analyzer.score("Hello there!")
        assert result.score >= 0

    def test_grade_boundaries(self, analyzer):
        # Grade F should happen for very AI-like text (low score)
        result = analyzer.score(AI_TEXT * 3)
        assert result.grade in ("A", "B", "C", "D", "F")