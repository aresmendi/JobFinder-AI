from importlib.util import find_spec

from repositories.offer_repository import OfferRepository
from models.offer import Offer

MODEL_NAME = "all-MiniLM-L6-v2"

# Singleton del modelo + caché de vectores por texto: encodear es lo caro,
# así cada oferta solo se encodea una vez por proceso.
_model = None
_vector_cache: dict[str, "object"] = {}


def embeddings_available() -> bool:
    """True si sentence-transformers está instalado (es opcional y pesado)."""
    return find_spec("sentence_transformers") is not None


def _get_model():
    global _model
    if _model is None:
        # Import perezoso: arrastra torch (~GBs); así la app arranca sin él
        from sentence_transformers import SentenceTransformer
        # El modelo se descarga la primera vez (~90 MB) y queda en caché local
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _cosine_similarity(a, b) -> float:
    import numpy as np
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def _offer_text(offer: Offer) -> str:
    parts = [offer.title or "", offer.company or "", offer.description or ""]
    return " ".join(p for p in parts if p).strip()


def _encode_cached(texts: list[str]) -> list:
    """Encodea solo los textos que no están en caché."""
    missing = [t for t in texts if t not in _vector_cache]
    if missing:
        vecs = _get_model().encode(missing, convert_to_numpy=True, batch_size=32)
        for t, v in zip(missing, vecs):
            _vector_cache[t] = v
    return [_vector_cache[t] for t in texts]


class EmbeddingService:
    """Búsqueda semántica sobre ofertas usando sentence-transformers (local, sin API)."""

    def __init__(self, repo: OfferRepository | None = None):
        self.repo = repo or OfferRepository()

    def _load_cv(self) -> str:
        from services.cv_service import cargar_cv, buscar_cv
        ruta = buscar_cv()
        return cargar_cv(ruta) if ruta else ""

    def search(self, query: str, top_k: int = 5) -> list[tuple[Offer, float]]:
        """Devuelve las top_k ofertas más similares semánticamente a la query."""
        offers = self.repo.list_all()
        if not offers:
            return []

        query_vec = _encode_cached([query])[0]
        offer_vecs = _encode_cached([_offer_text(o) for o in offers])

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
