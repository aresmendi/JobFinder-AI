import numpy as np
import pytest

from services import embedding_service
from services.embedding_service import EmbeddingService


@pytest.fixture(autouse=True)
def clean_cache():
    embedding_service._vector_cache.clear()
    yield
    embedding_service._vector_cache.clear()


@pytest.fixture
def fake_model(monkeypatch):
    """Modelo falso: vectoriza contando keywords (determinista y sin torch)."""
    calls = {"n": 0}

    class Fake:
        def encode(self, texts, **kwargs):
            calls["n"] += len(texts)
            return np.array(
                [[t.lower().count("python"), t.lower().count("angular")] for t in texts],
                dtype=float,
            )

    monkeypatch.setattr(embedding_service, "_get_model", lambda: Fake())
    return calls


def test_search_ranks_by_similarity(repo, sample_offers, fake_model):
    results = EmbeddingService(repo).search("python", top_k=2)
    assert results[0][0].id == 1  # la oferta Python es la más similar
    assert results[0][1] > results[1][1]


def test_search_empty_repo(repo, fake_model):
    assert EmbeddingService(repo).search("python") == []


def test_search_uses_vector_cache(repo, sample_offers, fake_model):
    svc = EmbeddingService(repo)
    svc.search("python")
    first = fake_model["n"]
    svc.search("python")
    assert fake_model["n"] == first  # segunda búsqueda: todo cacheado


def test_search_by_cv(repo, sample_offers, fake_model, monkeypatch):
    monkeypatch.setattr(EmbeddingService, "_load_cv", lambda self: "backend python")
    results = EmbeddingService(repo).search_by_cv(top_k=1)
    assert results[0][0].id == 1


def test_search_by_cv_without_cv(repo, sample_offers, fake_model, monkeypatch):
    monkeypatch.setattr(EmbeddingService, "_load_cv", lambda self: "")
    assert EmbeddingService(repo).search_by_cv() == []


# --- Endpoints ---

@pytest.fixture
def embeddings_on(monkeypatch):
    # El modelo real está mockeado; el guard de disponibilidad no aplica
    monkeypatch.setattr("routers.search.embeddings_available", lambda: True)


def test_search_endpoint(client, repo, sample_offers, fake_model, embeddings_on):
    r = client.get("/search", params={"q": "python", "top_k": 2})
    assert r.status_code == 200
    body = r.json()
    assert body[0]["offer"]["id"] == 1
    assert 0 <= body[0]["similarity"] <= 1


def test_search_endpoint_503_without_embeddings(client, sample_offers, monkeypatch):
    monkeypatch.setattr("routers.search.embeddings_available", lambda: False)
    assert client.get("/search", params={"q": "python"}).status_code == 503


def test_search_cv_endpoint(client, repo, sample_offers, fake_model, embeddings_on, monkeypatch):
    monkeypatch.setattr(EmbeddingService, "_load_cv", lambda self: "backend python")
    r = client.get("/search/cv", params={"top_k": 1})
    assert r.status_code == 200
    assert r.json()[0]["offer"]["id"] == 1
