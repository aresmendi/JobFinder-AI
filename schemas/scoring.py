from pydantic import BaseModel

class ScoreResponse(BaseModel):
    offer_id: int
    score: int
    matched_keywords: list[str] = []
    missing_keywords: list[str] = []
    reason: str