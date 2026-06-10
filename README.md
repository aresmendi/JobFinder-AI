# JobFinder AI

Backend en **FastAPI** que scrapea ofertas de empleo de múltiples portales, las indexa con **embeddings** para búsqueda semántica y las **puntúa automáticamente contra tu CV** usando un LLM (Google Gemini).

Construido para aprender y demostrar: FastAPI, scraping, prompt engineering, RAG y embeddings — todo en un proyecto que sirve de verdad para buscar trabajo.

---

## Stack

| Tecnología | Uso |
|---|---|
| Python + FastAPI | Backend y API REST |
| Google Gemini API | Scoring LLM (match 0-100 + keywords) |
| sentence-transformers | Embeddings + búsqueda semántica (RAG) |
| Playwright + BeautifulSoup | Scraping multi-portal |
| Pydantic + pydantic-settings | Validación y configuración |

---

## Arquitectura por capas

```
models/        → entidades de dominio (Offer)
schemas/       → DTOs de entrada/salida (Pydantic)
repositories/  → acceso a datos (JSON store)
services/      → lógica de negocio (scraping, scoring, embeddings)
  scrapers/    → un scraper por portal (Tecnoempleo, Infojobs, Indeed, LinkedIn)
routers/       → endpoints FastAPI
core/          → configuración (.env)
```

Flujo: `router → service → repository → model`

---

## Puesta en marcha

```bash
# 1. Clonar y crear entorno virtual
git clone https://github.com/aresmendi/JobFinder-AI.git
cd JobFinder-AI
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt
playwright install chromium      # necesario para scraping con JS

# 3. Configurar variables de entorno
cp .env.example .env
# Edita .env y añade tu GEMINI_API_KEY

# 4. Añadir tu CV
# Copia tu CV en PDF o texto a: data/cv.pdf  (o data/cv.txt)

# 5. Arrancar
uvicorn main:app --reload
```

API docs interactiva en **http://127.0.0.1:8000/docs**

### Con Docker

```bash
cp .env.example .env      # añade tu GEMINI_API_KEY
cp tu_cv.pdf data/cv.pdf  # tu CV para el matching
docker compose up -d --build
```

La app queda en **http://localhost:8000**. `data/` se monta como volumen: ofertas y CV persisten fuera del contenedor.

---

## Endpoints

### Ofertas

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/offers` | Lista ofertas ordenadas por score; filtros: `status`, `source`, `min_score` |
| `GET` | `/offers/{id}` | Detalle de una oferta |
| `PATCH` | `/offers/{id}/status` | Marca la oferta como `aplicada`, `descartada` o `nueva` |
| `DELETE` | `/offers/{id}` | Elimina una oferta |
| `POST` | `/offers/scrape` | Scrapea ofertas de uno o varios portales |

**Parámetros de `/offers/scrape`:**
- `q` — búsqueda (ej. `python`, `backend developer`)
- `location` — ciudad o país (ej. `Valencia`, `España`)
- `portal` — `all` · `tecnoempleo` · `infojobs` · `indeed` · `linkedin`

### Scoring LLM

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/scoring/{id}` | Puntúa una oferta contra el CV (0-100) |
| `POST` | `/scoring/all` | Puntúa todas las ofertas pendientes en lote |

**Parámetros de `/scoring/all`:**
- `pre_filter` — si se indica (ej. `20`), aplica pre-filtro semántico antes de llamar al LLM (reduce coste de API)

**Ejemplo de respuesta:**
```json
{
  "offer_id": 5,
  "score": 82,
  "matched_keywords": ["Python", "FastAPI", "REST"],
  "missing_keywords": ["Kubernetes", "AWS"],
  "reason": "Buen encaje técnico en backend Python/FastAPI. Falta experiencia cloud."
}
```

### Búsqueda semántica

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/search?q=...` | Busca ofertas por significado, no por palabra exacta |
| `GET` | `/search/cv` | Devuelve las ofertas más similares a tu CV |

Parámetro `top_k` en ambos (1-50, por defecto 5/10).

### Sistema

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servicio |

---

## Flujo típico

```bash
# 1. Scrapear ofertas de python en Valencia de todos los portales
POST /offers/scrape?q=python&location=Valencia&portal=all

# 2. Ver las más similares al CV (semántico, sin coste de LLM)
GET /search/cv?top_k=10

# 3. Puntuar las top-20 más relevantes con el LLM
POST /scoring/all?pre_filter=20

# 4. Ver resultados ordenados por score
GET /offers

# 5. Llevar el seguimiento de candidaturas
PATCH /offers/12/status   {"status": "aplicada"}
GET /offers?status=aplicada
```

---

## Portales soportados

| Portal | Método | Estado |
|---|---|---|
| Tecnoempleo | requests + BS4 (fallback Playwright) | ✅ Estable |
| Infojobs | Playwright | ✅ Requiere Playwright |
| Indeed | Playwright | ✅ Requiere Playwright |
| LinkedIn | Playwright | ⚠️ Sin descripción (listado público) |

---

## Conceptos aplicados

- **Prompt engineering** — prompt estructurado para extraer score, keywords y razonamiento en JSON
- **RAG** — embeddings para pre-filtrar ofertas relevantes antes de llamar al LLM (ahorra tokens y coste)
- **Embeddings + búsqueda semántica** — `sentence-transformers/all-MiniLM-L6-v2`, similitud coseno
- **Fallback chain de modelos** — si Gemini falla (quota/deprecado/sobrecarga), prueba el siguiente automáticamente
- **Scraping multi-portal** — arquitectura extensible: una clase base + un scraper por portal

---

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

56 tests sobre repositorio, servicios (scoring, scraping, embeddings, CV) y todos los endpoints. El LLM y el modelo de embeddings van mockeados: la suite corre en ~1s sin red ni API key.

---

## Datos

- `data/offers.json` — caché local de ofertas (deduplicación automática por URL, escritura atómica)
- `data/cv.pdf` / `data/cv.txt` — tu CV para el matching

---

*Ares Caballero · [github.com/aresmendi](https://github.com/aresmendi) · [linkedin.com/in/ares-caballero](https://linkedin.com/in/ares-caballero)*
