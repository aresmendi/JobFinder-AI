import pytest
from fastapi.testclient import TestClient

from models.offer import Offer
from repositories.offer_repository import OfferRepository


@pytest.fixture
def repo(tmp_path):
    """Repositorio sobre un JSON temporal, aislado por test."""
    return OfferRepository(path=str(tmp_path / "offers.json"))


@pytest.fixture
def sample_offers(repo):
    offers = [
        Offer(id=1, title="Backend Python", url="https://example.com/1",
              company="Acme", location="Valencia", description="FastAPI y SQL",
              score=85, source="tecnoempleo"),
        Offer(id=2, title="Frontend Angular", url="https://example.com/2",
              company="Globex", location="Madrid", description="Angular y TypeScript",
              score=40, source="infojobs", status="descartada"),
        Offer(id=3, title="Full Stack Java", url="https://example.com/3",
              company="Initech", location="Remoto", description="Spring Boot",
              source="linkedin"),
    ]
    repo.save_all(offers)
    return offers


@pytest.fixture
def client(repo):
    from main import app
    from core.deps import get_repo

    app.dependency_overrides[get_repo] = lambda: repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
