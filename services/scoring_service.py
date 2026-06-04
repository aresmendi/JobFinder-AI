import json
import time
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
        from services.cv_service import cargar_cv, buscar_cv
        ruta = buscar_cv()  # busca data/cv.pdf, cv.docx o cv.txt
        return cargar_cv(ruta) if ruta else "CV no disponible."

    def score_offer(self, offer: Offer) -> Offer:
        prompt = (
            "Eres un experto en ATS (Applicant Tracking Systems). "
            "Evalúa el encaje entre una OFERTA de empleo y un CV. "
            "Devuelve SOLO un JSON con estas claves:\n"
            '- "score": entero 0-100 (encaje global)\n'
            '- "matched_keywords": lista de tecnologías/keywords clave de la oferta que SÍ aparecen en el CV\n'
            '- "missing_keywords": lista de tecnologías/keywords clave de la oferta que FALTAN en el CV\n'
            '- "reason": string breve con el encaje y qué mejorar\n\n'
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
        offer.matched_keywords = data.get("matched_keywords", [])
        offer.missing_keywords = data.get("missing_keywords", [])
        #persistimos el resultado
        offers = self.repo.list_all()
        for i, o in enumerate(offers):
            if o.id == offer.id:
                offers[i] = offer
        self.repo.save_all(offers)
        return offer

    def score_all(self, pausa: float = 4.0) -> list[Offer]:
        pendientes = [o for o in self.repo.list_all() if o.score is None]
        for i, offer in enumerate(pendientes):
            try:
                self.score_offer(offer)            # puntúa y persiste
            except Exception as e:
                print(f"⚠️ Error en oferta {offer.id}: {e}")
            if i < len(pendientes) - 1:
                time.sleep(pausa)                  # respeta el rate limit free tier
        return sorted(self.repo.list_all(),
                      key=lambda o: (o.score or -1), reverse=True)


    @staticmethod
    def _parse(text: str) -> dict:
        text = text.strip().removeprefix("```json").removesuffix("```").removesuffix("```").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"score": 0, "reason": "No se pudo parsear la respuesta del modelo"}