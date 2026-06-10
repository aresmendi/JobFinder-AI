from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.deps import get_repo
from repositories.offer_repository import OfferRepository
from services.embedding_service import EmbeddingService, embeddings_available
from schemas.offer import OfferResponse

router = APIRouter(prefix="/search", tags=["search"])


class SearchResult(BaseModel):
    offer: OfferResponse
    similarity: float


def _require_embeddings():
    if not embeddings_available():
        raise HTTPException(
            status_code=503,
            detail="sentence-transformers no está instalado — instala las dependencias de embeddings",
        )


@router.get("", response_model=list[SearchResult])
def semantic_search(
    q: str = Query(..., description="Texto libre o descripción del puesto buscado"),
    top_k: int = Query(default=5, ge=1, le=50),
    repo: OfferRepository = Depends(get_repo),
):
    """Búsqueda semántica: devuelve las ofertas más parecidas a la query."""
    _require_embeddings()
    results = EmbeddingService(repo).search(q, top_k=top_k)
    return [
        SearchResult(offer=OfferResponse.model_validate(o.__dict__, from_attributes=True), similarity=round(sim, 4))
        for o, sim in results
    ]


@router.get("/cv", response_model=list[SearchResult])
def search_by_cv(
    top_k: int = Query(default=10, ge=1, le=50),
    repo: OfferRepository = Depends(get_repo),
):
    """Devuelve las ofertas más similares al CV del usuario."""
    _require_embeddings()
    results = EmbeddingService(repo).search_by_cv(top_k=top_k)
    return [
        SearchResult(offer=OfferResponse.model_validate(o.__dict__, from_attributes=True), similarity=round(sim, 4))
        for o, sim in results
    ]
