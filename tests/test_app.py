"""
tests/test_app.py — pytest unit tests for KrishiBot
Run: pytest tests/ -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app, _soil_tips, translate_crop, predict_crops_distance


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with flask_app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Soil tips logic
# ---------------------------------------------------------------------------
class TestSoilTips:
    def test_low_nitrogen(self):
        tips = _soil_tips(40, 30, 30, 6.5)
        assert any("Nitrogen" in t and "low" in t.lower() for t in tips)

    def test_high_nitrogen(self):
        tips = _soil_tips(150, 30, 30, 6.5)
        assert any("Nitrogen" in t and "high" in t.lower() for t in tips)

    def test_adequate_nitrogen(self):
        tips = _soil_tips(90, 30, 30, 6.5)
        assert any("adequate" in t.lower() or "ok" in t.lower() for t in tips)

    def test_acidic_ph(self):
        tips = _soil_tips(90, 30, 30, 4.5)
        assert any("acidic" in t.lower() or "lime" in t.lower() for t in tips)

    def test_alkaline_ph(self):
        tips = _soil_tips(90, 30, 30, 8.5)
        assert any("alkaline" in t.lower() or "gypsum" in t.lower() for t in tips)

    def test_optimal_ph(self):
        tips = _soil_tips(90, 30, 30, 6.5)
        assert any("optimal" in t.lower() for t in tips)

    def test_returns_four_tips(self):
        tips = _soil_tips(90, 30, 30, 6.5)
        assert len(tips) == 4


# ---------------------------------------------------------------------------
# Crop translation
# ---------------------------------------------------------------------------
class TestTranslateCrop:
    def test_english_passthrough(self):
        assert translate_crop("Rice", "english") == "Rice"

    def test_unknown_lang_returns_original(self):
        assert translate_crop("Rice", "klingon") == "Rice"

    def test_unknown_crop_returns_original(self):
        assert translate_crop("MarsianPlant", "hindi") == "MarsianPlant"


# ---------------------------------------------------------------------------
# Crop distance prediction
# ---------------------------------------------------------------------------
class TestPredictCropsDistance:
    def test_returns_list(self):
        result = predict_crops_distance(90, 42, 43, 6.5, 20.0, 82.0, 200.0)
        assert isinstance(result, list)

    def test_returns_up_to_5(self):
        result = predict_crops_distance(90, 42, 43, 6.5, 20.0, 82.0, 200.0)
        assert len(result) <= 5

    def test_scores_between_0_and_100(self):
        result = predict_crops_distance(90, 42, 43, 6.5, 20.0, 82.0, 200.0)
        for r in result:
            assert 0 <= r["match_score"] <= 100

    def test_has_expected_keys(self):
        result = predict_crops_distance(90, 42, 43, 6.5, 20.0, 82.0, 200.0)
        for r in result:
            assert "crop" in r
            assert "match_score" in r
            assert "ideal_conditions" in r

    def test_sorted_descending(self):
        result = predict_crops_distance(90, 42, 43, 6.5, 20.0, 82.0, 200.0)
        scores = [r["match_score"] for r in result]
        assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------
class TestApiStates:
    def test_returns_200(self, client):
        resp = client.get("/api/states")
        assert resp.status_code == 200

    def test_response_has_states_key(self, client):
        resp = client.get("/api/states")
        data = resp.get_json()
        assert "states" in data
        assert isinstance(data["states"], list)

    def test_states_not_empty(self, client):
        resp = client.get("/api/states")
        data = resp.get_json()
        assert len(data["states"]) > 0


class TestApiValidation:
    def test_advice_missing_state(self, client):
        resp = client.get("/api/advice")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_advice_with_state(self, client):
        resp = client.get("/api/advice?state=Maharashtra&district=Pune")
        # Should succeed (200) or fail gracefully (not 500)
        assert resp.status_code in (200, 404)

    def test_soil_health_missing_state(self, client):
        resp = client.get("/api/soil-health")
        assert resp.status_code == 400

    def test_pesticides_missing_state(self, client):
        resp = client.get("/api/pesticides")
        assert resp.status_code == 400

    def test_invalid_state_too_short(self, client):
        resp = client.get("/api/advice?state=X")
        assert resp.status_code == 400

    def test_404_unknown_endpoint(self, client):
        resp = client.get("/api/nonexistent")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["code"] == "NOT_FOUND"


class TestApiDistricts:
    def test_districts_for_maharashtra(self, client):
        resp = client.get("/api/districts?state=Maharashtra")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "districts" in data

    def test_market_prices(self, client):
        resp = client.get("/api/market-prices")
        assert resp.status_code in (200, 500)

    def test_ml_status(self, client):
        resp = client.get("/api/ml-status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "ml_loaded" in data
        assert "accuracy_pct" in data
