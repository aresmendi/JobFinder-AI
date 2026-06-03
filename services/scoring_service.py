import json
from google import genai
from core.config import settings
from models.offer import Offer
from repositories.offer_repository import OfferRepository

class ScoringService:
    """Llama al LLM para puntuar una oferta contra el CV (0-100)"""

    def __init__(self, repo: OfferRepository|None = None):
        self.repo = repo or OfferRepository()
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def _load_cv(self) -> str:
        try:
            with open(settings.cv_file, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "CV no disponible"

    def score_offer(self, offer: Offer) -> Offer:
        prompt = (
            "Eres un asistente que evalua el encaje entre una oferta de empleo y un CV. "
            "Devuelve SOLO un JSON con las claves 'score' (entero 0-100) y 'reason' (string breve).\n\n"
            f"CV:\n{self._load_cv()}\n\n"
            f"OFERTA:\n{offer.title}\n{offer.company}\n{offer.description}\n"
        )
        resp = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
        data = self._parse(resp.text)
        offer.score = int(data.get("score", 0))
        offer.score_reason = data.get("reason", "")
        #persistimos el resultado
        offers = self.repo.list_all()
        for i, o in enumerate(offers):
            if o.id == offer.id:
                offers[i] = offer
        self.repo.save_all(offers)
        return offer

    @staticmethod
    def _parse(text: str) -> dict:
        text = text.strip().removeprefix("```json").removesuffix("```").removesuffix("```").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"score": 0, "reason": "No se pudo parsear la respuesta del modelo"}