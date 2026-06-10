import json
import time
from google import genai
from google.genai.errors import ClientError
from core.config import settings
from models.offer import Offer
from repositories.offer_repository import OfferRepository

# Chain de fallback: se intenta en orden hasta que uno responda sin error de quota/deprecación
FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]


class ScoringService:
    """Llama al LLM para puntuar una oferta contra el CV (0-100)"""

    def __init__(self, repo: OfferRepository | None = None, retry_wait: float = 10.0):
        self.repo = repo or OfferRepository()
        self.retry_wait = retry_wait
        self._client: genai.Client | None = None
        self._cv_cache: str | None = None

    @property
    def client(self) -> genai.Client:
        # Perezoso: permite instanciar el servicio (y arrancar la app) sin API key
        if self._client is None:
            if not settings.gemini_api_key:
                raise RuntimeError("GEMINI_API_KEY no configurada (revisa el .env)")
            self._client = genai.Client(api_key=settings.gemini_api_key)
        return self._client

    def _load_cv(self) -> str:
        if self._cv_cache is None:
            from services.cv_service import cargar_cv, buscar_cv
            ruta = buscar_cv()
            self._cv_cache = cargar_cv(ruta) if ruta else "CV no disponible."
        return self._cv_cache

    def _generate_with_fallback(self, prompt: str) -> str:
        last_error = None
        for model in FALLBACK_MODELS:
            try:
                resp = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                if model != FALLBACK_MODELS[0]:
                    print(f"ℹ️  Usando modelo de fallback: {model}")
                return resp.text
            except ClientError as e:
                # OJO: e.status es un string ("UNAVAILABLE"); el código HTTP está en e.code
                err_str = str(e)
                # 503 = sobrecarga temporal → esperar y reintentar el mismo modelo una vez
                if e.code == 503 or "UNAVAILABLE" in err_str:
                    print(f"⚠️  {model} sobrecargado (503), esperando {self.retry_wait}s...")
                    time.sleep(self.retry_wait)
                    try:
                        resp = self.client.models.generate_content(model=model, contents=prompt)
                        return resp.text
                    except Exception:
                        pass  # si falla de nuevo, cae al siguiente modelo
                # 429 = quota agotada, 404 = modelo deprecado/no disponible → probar siguiente
                if e.code in (429, 404, 503) or "RESOURCE_EXHAUSTED" in err_str or "NOT_FOUND" in err_str or "UNAVAILABLE" in err_str:
                    print(f"⚠️  {model} no disponible ({e.code} {e.status}), probando siguiente...")
                    last_error = e
                    continue
                raise
        raise last_error

    def score_offer(self, offer: Offer) -> Offer:
        if not offer.description and not offer.title:
            offer.score = 0
            offer.score_reason = "Oferta sin descripción ni título — no se puede scorear."
            return offer

        cv_text = self._load_cv()
        desc_block = offer.description or "(sin descripción disponible — evalúa solo por título y empresa)"
        prompt = (
            "Eres un experto en ATS (Applicant Tracking Systems). "
            "Evalúa el encaje entre una OFERTA de empleo y un CV. "
            "Devuelve SOLO un JSON con estas claves:\n"
            '- "score": entero 0-100 (encaje global)\n'
            '- "matched_keywords": lista de tecnologías/keywords clave de la oferta que SÍ aparecen en el CV\n'
            '- "missing_keywords": lista de tecnologías/keywords clave de la oferta que FALTAN en el CV\n'
            '- "reason": string breve con el encaje y qué mejorar\n\n'
            f"CV:\n{cv_text}\n\n"
            f"OFERTA:\nTítulo: {offer.title}\nEmpresa: {offer.company}\nDescripción: {desc_block}\n"
        )
        text = self._generate_with_fallback(prompt)
        data = self._parse(text)
        try:
            score = int(data.get("score", 0))
        except (TypeError, ValueError):
            score = 0
        offer.score = max(0, min(100, score))
        offer.score_reason = data.get("reason", "")
        offer.matched_keywords = data.get("matched_keywords", [])
        offer.missing_keywords = data.get("missing_keywords", [])
        self.repo.update(offer)
        return offer

    def score_all(self, pausa: float = 4.0, pre_filter: int | None = None) -> list[Offer]:
        if pre_filter is not None:
            from services.embedding_service import EmbeddingService
            candidatas = {o.id for o, _ in EmbeddingService(self.repo).search_by_cv(top_k=pre_filter)}
            pendientes = [o for o in self.repo.list_all() if o.score is None and o.id in candidatas]
            print(f"ℹ️  pre_filter={pre_filter}: {len(pendientes)} ofertas pasan el filtro semántico")
        else:
            pendientes = [o for o in self.repo.list_all() if o.score is None]
        for i, offer in enumerate(pendientes):
            try:
                self.score_offer(offer)
            except Exception as e:
                print(f"⚠️ Error en oferta {offer.id}: {e}")
            if i < len(pendientes) - 1:
                time.sleep(pausa)
        return sorted(self.repo.list_all(),
                      key=lambda o: (o.score or -1), reverse=True)

    @staticmethod
    def _parse(text: str) -> dict:
        text = text.strip().removeprefix("```json").removesuffix("```").removesuffix("```").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"score": 0, "reason": "No se pudo parsear la respuesta del modelo"}
