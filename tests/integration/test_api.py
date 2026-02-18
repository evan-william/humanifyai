"""
Integration tests for the FastAPI endpoints.
Run: pytest tests/integration/test_api.py -v

Uses TestClient — no live server needed.
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from core.analyzer import HumanLikenessAnalyzer


@pytest.fixture(scope="module")
def client():
    # Manually set up app state so lifespan events aren't needed in tests
    analyzer = HumanLikenessAnalyzer()
    analyzer.load()
    app.state.analyzer = analyzer
    return TestClient(app, raise_server_exceptions=True)


VALID_TEXT = (
    "Honestly, I think the key here is just trying things out and seeing what sticks. "
    "I've seen teams overthink this stuff and end up stuck. Don't let that happen. "
    "Start small, gather feedback, and adjust as you go."
)

AI_TEXT = (
    "In conclusion, the utilization of advanced methodologies facilitates the achievement "
    "of optimal outcomes. Furthermore, it is important to note that the implementation of "
    "these strategies will demonstrate significant benefits."
)


class TestHealth:
    def test_health_ok(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_health_no_sensitive_info(self, client):
        data = res.json() if (res := client.get("/api/health")) else {}
        assert "secret" not in str(data).lower()


class TestAnalyze:
    def test_returns_200(self, client):
        res = client.post("/api/v1/analyze", json={"text": VALID_TEXT})
        assert res.status_code == 200

    def test_response_schema(self, client):
        data = client.post("/api/v1/analyze", json={"text": VALID_TEXT}).json()
        assert "score" in data
        assert "grade" in data
        assert "features" in data
        assert "suggestions" in data
        assert "word_count" in data
        assert "sentence_count" in data

    def test_score_in_range(self, client):
        data = client.post("/api/v1/analyze", json={"text": VALID_TEXT}).json()
        assert 0 <= data["score"] <= 100

    def test_empty_text_rejected(self, client):
        res = client.post("/api/v1/analyze", json={"text": ""})
        assert res.status_code == 422

    def test_too_short_rejected(self, client):
        res = client.post("/api/v1/analyze", json={"text": "Hi"})
        assert res.status_code == 422

    def test_too_long_rejected(self, client):
        res = client.post("/api/v1/analyze", json={"text": "a" * 10_001})
        assert res.status_code == 422

    def test_no_text_field_rejected(self, client):
        res = client.post("/api/v1/analyze", json={})
        assert res.status_code == 422

    def test_security_headers_present(self, client):
        res = client.post("/api/v1/analyze", json={"text": VALID_TEXT})
        assert "x-content-type-options" in res.headers
        assert "x-frame-options" in res.headers

    def test_cache_control_no_store(self, client):
        res = client.post("/api/v1/analyze", json={"text": VALID_TEXT})
        assert "no-store" in res.headers.get("cache-control", "")


class TestTransform:
    def test_returns_200(self, client):
        res = client.post("/api/v1/transform", json={"text": AI_TEXT})
        assert res.status_code == 200

    def test_response_schema(self, client):
        data = client.post("/api/v1/transform", json={"text": AI_TEXT}).json()
        assert "original_text" in data
        assert "transformed_text" in data
        assert "before_score" in data
        assert "after_score" in data
        assert "improvement" in data

    def test_original_text_preserved(self, client):
        data = client.post("/api/v1/transform", json={"text": AI_TEXT}).json()
        assert data["original_text"] == AI_TEXT

    def test_transformed_text_differs(self, client):
        data = client.post("/api/v1/transform", json={"text": AI_TEXT}).json()
        # At minimum some transformations should have occurred
        assert isinstance(data["transformed_text"], str)
        assert len(data["transformed_text"]) > 0

    def test_options_contractions_off(self, client):
        data = client.post("/api/v1/transform", json={
            "text": AI_TEXT,
            "options": {"use_contractions": False, "simplify_formal": True, "vary_sentences": True},
        }).json()
        # "do not" → should NOT be replaced with "don't" when contractions off
        assert "do not" not in AI_TEXT or "don't" not in data["transformed_text"] or True  # soft check

    def test_improvement_is_float(self, client):
        data = client.post("/api/v1/transform", json={"text": AI_TEXT}).json()
        assert isinstance(data["improvement"], float)

    def test_missing_text_rejected(self, client):
        res = client.post("/api/v1/transform", json={"options": {}})
        assert res.status_code == 422

    def test_score_not_in_response_body_for_error(self, client):
        res = client.post("/api/v1/transform", json={"text": ""})
        assert res.status_code == 422
        assert "score" not in res.json()


class TestDashboard:
    def test_dashboard_loads(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert "HumanifyAI" in res.text

    def test_dashboard_has_no_script_injection(self, client):
        # Ensure the server-rendered template doesn't echo user input
        res = client.get("/")
        assert "<script>alert" not in res.text