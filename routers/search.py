from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from repositories.offer_repository import OfferRepository
from services.embedding_service import EmbeddingService
from schemas.offer import OfferResponse

router = APIRouter(prefix="/search", tags=["search"])
repo = OfferRepository()


class SearchResult(BaseModel):
    offer: OfferResponse
    similarity: float


@router.get("", response_model=list[SearchResult])
def semantic_search(
    q: str = Query(..., description="Texto libre o descripción del puesto buscado"),
    top_k: int = Query(default=5, ge=1, le=50),
):
    """Búsqueda semántica: devuelve las ofertas más parecidas a la query."""
    results = EmbeddingService(repo).search(q, top_k=top_k)
    return [
        SearchResult(offer=OfferResponse.model_validate(o.__dict__, from_attributes=True), similarity=round(sim, 4))
        for o, sim in results
    ]


@router.get("/cv", response_model=list[SearchResult])
def search_by_cv(top_k: int = Query(default=10, ge=1, le=50)):
    """Devuelve las ofertas más similares al CV del usuario."""
    results = EmbeddingService(repo).search_by_cv(top_k=top_k)
    return [
        SearchResult(offer=OfferResponse.model_validate(o.__dict__, from_attributes=True), similarity=round(sim, 4))
        for o, sim in results
    ]
