from pydantic import BaseModel

class ScoreResponse(BaseModel):
    offer_id: int
    score: int
    reason: str