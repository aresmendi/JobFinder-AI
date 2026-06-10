import json

import pytest
from google.genai.errors import ClientError

from core.config import settings
from models.offer import Offer
from services.scoring_service import ScoringService, FALLBACK_MODELS


def make_service(repo, monkeypatch, response_text):
    svc = ScoringService(repo, retry_wait=0)
    monkeypatch.setattr(svc, "_load_cv", lambda: "CV: Python, FastAPI")
    monkeypatch.setattr(svc, "_generate_with_fallback", lambda prompt: response_text)
    return svc


def test_parse_plain_json():
    assert ScoringService._parse('{"score": 90}') == {"score": 90}


def test_parse_fenced_json():
    text = '```json\n{"score": 75, "reason": "ok"}\n```'
    assert ScoringService._parse(text)["score"] == 75


def test_parse_garbage_returns_zero():
    data = ScoringService._parse("esto no es JSON")
    assert data["score"] == 0
    assert "reason" in data


def test_score_offer_persists(repo, sample_offers, monkeypatch):
    svc = make_service(repo, monkeypatch, json.dumps({
        "score": 88, "reason": "buen encaje",
        "matched_keywords": ["python"], "missing_keywords": ["docker"],
    }))
    offer = repo.get(3)
    scored = svc.score_offer(offer)
    assert scored.score == 88
    assert repo.get(3).score == 88
    assert repo.get(3).matched_keywords == ["python"]


def test_score_offer_clamps_out_of_range(repo, sample_offers, monkeypatch):
    svc = make_service(repo, monkeypatch, '{"score": 150}')
    assert svc.score_offer(repo.get(3)).score == 100


def test_score_offer_invalid_score_value(repo, sample_offers, monkeypatch):
    svc = make_service(repo, monkeypatch, '{"score": "alto"}')
    assert svc.score_offer(repo.get(3)).score == 0


def test_score_offer_without_title_or_description(repo):
    svc = ScoringService(repo, retry_wait=0)
    offer = Offer(id=99, title="", url="https://x.com", description=None)
    scored = svc.score_offer(offer)
    assert scored.score == 0
    assert "sin descripción" in scored.score_reason


def test_score_all_only_scores_pending(repo, sample_offers, monkeypatch):
    svc = make_service(repo, monkeypatch, '{"score": 70, "reason": "ok"}')
    scored_ids = []
    original = svc.score_offer
    monkeypatch.setattr(svc, "score_offer", lambda o: scored_ids.append(o.id) or original(o))
    monkeypatch.setattr("services.scoring_service.time.sleep", lambda s: None)
    result = svc.score_all()
    assert scored_ids == [3]  # solo la oferta sin score previo
    assert [o.id for o in result[:2]] == [1, 3]  # ordenado por score desc (85, 70)


def test_client_requires_api_key(repo, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "")
    svc = ScoringService(repo)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        _ = svc.client


def test_fallback_chain_on_quota_error(repo, sample_offers, monkeypatch):
    """Si el primer modelo da 429, se prueba el siguiente (usando e.code, no e.status)."""
    svc = ScoringService(repo, retry_wait=0)
    calls = []

    class FakeResp:
        text = '{"score": 50, "reason": "ok"}'

    def fake_generate(model, contents):
        calls.append(model)
        if model == FALLBACK_MODELS[0]:
            raise ClientError(429, {"error": {"message": "quota", "status": "RESOURCE_EXHAUSTED"}})
        return FakeResp()

    monkeypatch.setattr(settings, "gemini_api_key", "fake-key")
    svc._client = type("C", (), {"models": type("M", (), {"generate_content": staticmethod(fake_generate)})()})()
    assert svc._generate_with_fallback("prompt") == FakeResp.text
    assert calls == [FALLBACK_MODELS[0], FALLBACK_MODELS[1]]


def test_fallback_exhausted_raises(repo, monkeypatch):
    svc = ScoringService(repo, retry_wait=0)

    def always_quota(model, contents):
        raise ClientError(429, {"error": {"message": "quota", "status": "RESOURCE_EXHAUSTED"}})

    svc._client = type("C", (), {"models": type("M", (), {"generate_content": staticmethod(always_quota)})()})()
    with pytest.raises(ClientError):
        svc._generate_with_fallback("prompt")


def test_unexpected_error_propagates(repo, monkeypatch):
    """Un 400 (p.ej. key inválida) no debe silenciarse con el fallback."""
    svc = ScoringService(repo, retry_wait=0)
    calls = []

    def bad_request(model, contents):
        calls.append(model)
        raise ClientError(400, {"error": {"message": "API key not valid", "status": "INVALID_ARGUMENT"}})

    svc._client = type("C", (), {"models": type("M", (), {"generate_content": staticmethod(bad_request)})()})()
    with pytest.raises(ClientError):
        svc._generate_with_fallback("prompt")
    assert calls == [FALLBACK_MODELS[0]]  # no siguió probando modelos
