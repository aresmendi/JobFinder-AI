# JobFinder AI 🔎🤖

Asistente que **recoge ofertas de empleo**, las guarda y las **puntúa (0-100) contra tu CV**
usando un LLM vía API. Backend en **FastAPI** con arquitectura por capas.

## Stack
Python · FastAPI · Pydantic · Google Gemini (API) · scraping (requests/bs4)

## Arquitectura por capas
| Capa | Carpeta | Rol (equivalente Spring) |
|------|---------|--------------------------|
| Dominio | `models/` | Entidades (`@Entity`) |
| API I/O | `schemas/` | DTOs |
| Datos | `repositories/` | `@Repository` |
| Negocio | `services/` | `@Service` |
| Endpoints | `routers/` | `@RestController` |
| Config | `core/` | configuración / settings |
| Arranque | `main.py` | clase `Application` |

Flujo: `router → service → repository → model`.

## Puesta en marcha
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env .env             # y pon tu GEMINI_API_KEY
uvicorn main:app --reload
```
Abre la documentación interactiva en **http://127.0.0.1:8000/docs**

## Endpoints
- `GET /health` — estado del servicio
- `GET /offers` — lista ofertas guardadas
- `GET /offers/{id}` — una oferta
- `POST /offers/scrape` — recoge ofertas (de momento datos de ejemplo)
- `POST /scoring/{id}` — puntúa una oferta contra el CV con el LLM

## Datos
- `data/offers.json` — cache de ofertas
- `data/cv.txt` — tu CV en texto (para el match)

## Roadmap
- [X] Scraping real de un portal de empleo
- [ ] Búsqueda semántica con embeddings
- [ ] Persistencia en BD
- [ ] Dockerizar

---
Proyecto personal de aprendizaje (backend + IA).
