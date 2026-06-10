import pytest

from core.config import settings
from services.scoring_service import ScoringService


@pytest.fixture
def fake_scoring(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "fake-key")

    def fake_score(self, offer):
        offer.score = 77
        offer.score_reason = "encaje alto"
        offer.matched_keywords = ["python"]
        offer.missing_keywords = ["docker"]
        self.repo.update(offer)
        return offer

    monkeypatch.setattr(ScoringService, "score_offer", fake_score)


def test_score_offer_endpoint(client, repo, sample_offers, fake_scoring):
    r = client.post("/scoring/3")
    assert r.status_code == 200
    body = r.json()
    assert body["score"] == 77
    assert body["matched_keywords"] == ["python"]
    assert repo.get(3).score == 77


def test_score_offer_404(client, sample_offers, fake_scoring):
    assert client.post("/scoring/999").status_code == 404


def test_score_without_api_key_returns_503(client, sample_offers, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "")
    r = client.post("/scoring/1")
    assert r.status_code == 503
    assert "GEMINI_API_KEY" in r.json()["detail"]


def test_score_all_without_api_key_returns_503(client, sample_offers, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "")
    assert client.post("/scoring/all").status_code == 503


def test_score_all_endpoint(client, sample_offers, fake_scoring, monkeypatch):
    monkeypatch.setattr("services.scoring_service.time.sleep", lambda s: None)
    r = client.post("/scoring/all")
    assert r.status_code == 200
    scores = {item["offer_id"]: item["score"] for item in r.json()}
    assert scores[3] == 77  # la pendiente se ha puntuado
    assert scores[1] == 85  # la ya puntuada conserva su score
