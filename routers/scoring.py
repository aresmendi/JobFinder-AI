from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from core.config import settings
from core.deps import get_repo
from repositories.offer_repository import OfferRepository
from schemas.scoring import ScoreResponse
from services.scoring_service import ScoringService

router = APIRouter(prefix="/scoring", tags=["scoring"])


def _require_api_key():
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY no configurada — añádela al .env para usar el scoring",
        )


@router.post("/all", response_model=list[ScoreResponse])
def score_all(
    pre_filter: Optional[int] = Query(default=None, description="Si se indica, filtra primero con embeddings y solo puntúa las top-N más similares al CV"),
    repo: OfferRepository = Depends(get_repo),
):
    _require_api_key()
    scored = ScoringService(repo).score_all(pre_filter=pre_filter)
    return [
        ScoreResponse(
            offer_id=o.id, score=o.score or 0,
            matched_keywords=o.matched_keywords or [],
            missing_keywords=o.missing_keywords or [],
            reason=o.score_reason or "",
        )
        for o in scored if o.score is not None
    ]


@router.post("/{offer_id}", response_model=ScoreResponse)
def score_offer(offer_id: int, repo: OfferRepository = Depends(get_repo)):
    _require_api_key()
    offer = repo.get(offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    scored = ScoringService(repo).score_offer(offer)
    return ScoreResponse(
        offer_id=scored.id,
        score=scored.score or 0,
        matched_keywords=scored.matched_keywords or [],
        missing_keywords=scored.missing_keywords or [],
        reason=scored.score_reason or "",
    )
