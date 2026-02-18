"""
Unit tests for TextTransformer.
Run: pytest tests/unit/test_transformer.py -v
"""

import pytest
from core.transformer import TextTransformer


@pytest.fixture
def transformer():
    return TextTransformer(seed=42)


class TestContractions:
    def test_do_not_becomes_dont(self, transformer):
        result = transformer.transform("We do not want to go.")
        assert "don't" in result

    def test_it_is_becomes_its(self, transformer):
        result = transformer.transform("It is very clear.")
        assert "it's" in result or "It's" in result

    def test_cannot_becomes_cant(self, transformer):
        result = transformer.transform("We cannot continue like this.")
        assert "can't" in result

    def test_contractions_disabled(self):
        t = TextTransformer(use_contractions=False, simplify_formal=False, vary_sentences=False)
        result = t.transform("We do not want to go.")
        assert "do not" in result
        assert "don't" not in result


class TestFormalSimplification:
    def test_furthermore_replaced(self, transformer):
        result = transformer.transform("Furthermore, this is important.")
        assert "Furthermore" not in result

    def test_utilize_replaced(self, transformer):
        result = transformer.transform("Please utilize the available resources.")
        assert "utilize" not in result
        assert "use" in result

    def test_in_conclusion_replaced(self, transformer):
        result = transformer.transform("In conclusion, we have done well.")
        assert "In conclusion" not in result

    def test_formal_simplification_disabled(self):
        t = TextTransformer(use_contractions=False, simplify_formal=False, vary_sentences=False)
        result = t.transform("Furthermore, this is important.")
        assert "Furthermore" in result


class TestEdgeCases:
    def test_empty_string(self, transformer):
        assert transformer.transform("") == ""

    def test_whitespace_only(self, transformer):
        result = transformer.transform("   ")
        assert result.strip() == ""

    def test_no_double_spaces(self, transformer):
        result = transformer.transform("It is very important. We do not need more.")
        assert "  " not in result

    def test_output_is_string(self, transformer):
        result = transformer.transform("This is a test sentence.")
        assert isinstance(result, str)

    def test_long_text_preserves_content(self, transformer):
        original = "The team did not complete the task. " * 20
        result = transformer.transform(original)
        # Core meaning should still be present even after transformation
        assert len(result) > 50

    def test_deterministic_with_seed(self):
        t1 = TextTransformer(seed=1)
        t2 = TextTransformer(seed=1)
        text = "This is a test. " * 10
        assert t1.transform(text) == t2.transform(text)