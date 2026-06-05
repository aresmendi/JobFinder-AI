import numpy as np
from sentence_transformers import SentenceTransformer
from repositories.offer_repository import OfferRepository
from models.offer import Offer

MODEL_NAME = "all-MiniLM-L6-v2"


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def _offer_text(offer: Offer) -> str:
    parts = [offer.title or "", offer.company or "", offer.description or ""]
    return " ".join(p for p in parts if p).strip()


class EmbeddingService:
    """Búsqueda semántica sobre ofertas usando sentence-transformers (local, sin API)."""

    def __init__(self, repo: OfferRepository | None = None):
        self.repo = repo or OfferRepository()
        # El modelo se descarga la primera vez (~90 MB) y queda en caché local
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(MODEL_NAME)
        return self._model

    def _load_cv(self) -> str:
        from services.cv_service import cargar_cv, buscar_cv
        ruta = buscar_cv()
        return cargar_cv(ruta) if ruta else ""

    def search(self, query: str, top_k: int = 5) -> list[tuple[Offer, float]]:
        """Devuelve las top_k ofertas más similares semánticamente a la query."""
        offers = self.repo.list_all()
        if not offers:
            return []

        model = self._get_model()
        query_vec = model.encode(query, convert_to_numpy=True)
        offer_texts = [_offer_text(o) for o in offers]
        offer_vecs = model.encode(offer_texts, convert_to_numpy=True, batch_size=32)

        scored = [
            (offer, _cosine_similarity(query_vec, vec))
            for offer, vec in zip(offers, offer_vecs)
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def search_by_cv(self, top_k: int = 10) -> list[tuple[Offer, float]]:
        """Devuelve las ofertas más similares al CV del usuario."""
        cv_text = self._load_cv()
        if not cv_text:
            return []
        return self.search(cv_text, top_k=top_k)
