"""Dependencias compartidas de FastAPI (inyectables y sustituibles en tests)."""
from repositories.offer_repository import OfferRepository

_repo: OfferRepository | None = None


def get_repo() -> OfferRepository:
    global _repo
    if _repo is None:
        _repo = OfferRepository()
    return _repo
