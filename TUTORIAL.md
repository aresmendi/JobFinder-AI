# Tutorial: JobFinder AI

Guía de uso paso a paso de JobFinder AI — un backend FastAPI que scrapea ofertas de empleo, las indexa con embeddings y las puntúa automáticamente contra tu CV usando Google Gemini.

---

## Índice

1. [Requisitos previos](#1-requisitos-previos)
2. [Instalación](#2-instalación)
3. [Configuración](#3-configuración)
4. [Arrancar la aplicación](#4-arrancar-la-aplicación)
5. [Interfaz web](#5-interfaz-web)
6. [Flujo de uso recomendado](#6-flujo-de-uso-recomendado)
7. [Endpoints de la API](#7-endpoints-de-la-api)
8. [Scoring LLM](#8-scoring-llm)
9. [Búsqueda semántica](#9-búsqueda-semántica)
10. [Gestión del estado de ofertas](#10-gestión-del-estado-de-ofertas)
11. [Docker](#11-docker)
12. [Tests](#12-tests)
13. [Preguntas frecuentes](#13-preguntas-frecuentes)

---

## 1. Requisitos previos

- Python 3.10+
- Una **API key de Google Gemini** (gratuita): [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- Tu CV en PDF o texto plano

Para Docker:
- Docker + Docker Compose

---

## 2. Instalación

```bash
git clone https://github.com/aresmendi/JobFinder-AI.git
cd JobFinder-AI

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
playwright install chromium       # necesario para scraping con JavaScript
```

---

## 3. Configuración

```bash
cp .env.example .env
```

Abre `.env` y rellena:

```env
GEMINI_API_KEY=tu_api_key_aqui

# Opcional — modelo a usar (por defecto gemini-2.5-flash)
GEMINI_MODEL=gemini-2.5-flash
```

**Añade tu CV:**

```bash
# Copia tu CV al directorio data/
cp /ruta/a/tu/cv.pdf data/cv.pdf
# o en texto plano:
cp /ruta/a/tu/cv.txt data/cv.txt
```

El app busca automáticamente `data/cv.pdf` o `data/cv.txt`. El PDF tiene prioridad.

---

## 4. Arrancar la aplicación

```bash
uvicorn main:app --reload
```

La API queda disponible en:
- **Frontend web:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Docs interactivos (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 5. Interfaz web

Al abrir [http://127.0.0.1:8000](http://127.0.0.1:8000) verás tres paneles:

### Panel "Buscar ofertas" (scraping)
- **Puesto:** término de búsqueda (ej. `python developer`, `backend`)
- **Ubicación:** ciudad o país (ej. `Valencia`, `España`, `Madrid`)
- **Portal:** `Todos los portales`, Tecnoempleo, Infojobs, Indeed o LinkedIn
- Pulsa **Scrapear** — puede tardar 30-90 segundos según el portal

### Panel "Búsqueda semántica"
- Escribe en lenguaje natural lo que buscas (ej. `"trabajo de backend con FastAPI y microservicios"`)
- **Buscar** — filtra las ofertas ya descargadas por similitud semántica
- **Mi CV** — muestra las ofertas más parecidas a tu CV automáticamente

### Panel "Scoring LLM"
- **Pre-filtro:** número de ofertas a seleccionar previamente con embeddings antes de llamar al LLM (reduce coste de API; recomendado: 20)
- Pulsa **Scorear todo** — el LLM puntúa cada oferta de 0 a 100 y explica el resultado (Posibilidad de fallo por falta de tokens)

### Cards de ofertas
Cada tarjeta muestra:
- Título enlazado a la oferta original
- Empresa y ubicación
- Badge de score: verde ≥ 70, amarillo ≥ 40, rojo < 40, gris sin puntuar
- Keywords encontradas en tu CV (verde) y las que faltan (rojo)
- Razón del score
- Botones: **Puntuar** (individual), **He aplicado**, **Descartar**

### Filtros disponibles
- **Todas** — todas las ofertas excepto descartadas
- **Con score** — solo las puntuadas
- **Score ≥ 70** — las más relevantes
- **Mis aplicaciones** — a las que has marcado como aplicada
- **Descartadas** — las que has descartado

---

## 6. Flujo de uso recomendado

```
1. Scrapear → 2. Buscar por CV → 3. Scorear top → 4. Revisar → 5. Marcar aplicadas
```

**Paso a paso:**

```bash
# 1. Scrapear ofertas de tu perfil en todos los portales
POST /offers/scrape?q=java+backend&location=Valencia&portal=all

# 2. Ver cuáles encajan mejor con tu CV (sin coste de LLM)
GET /search/cv?top_k=15

# 3. Puntuar solo las 20 más similares al CV con el LLM (más eficiente)
POST /scoring/all?pre_filter=20

# 4. Consultar resultados ordenados por score
GET /offers

# 5. Marcar las que te interesan
PATCH /offers/12/status   body: {"status": "aplicada"}
```

---

## 7. Endpoints de la API

### Ofertas — `/offers`

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/offers` | Lista todas las ofertas ordenadas por score |
| `GET` | `/offers/{id}` | Detalle de una oferta |
| `POST` | `/offers/scrape` | Scrapea nuevas ofertas |
| `PATCH` | `/offers/{id}/status` | Cambia el estado de una oferta |
| `DELETE` | `/offers/{id}` | Elimina una oferta |

**Filtros de `GET /offers`:**

| Parámetro | Valores | Ejemplo |
|-----------|---------|---------|
| `status` | `nueva`, `aplicada`, `descartada` | `?status=aplicada` |
| `source` | `tecnoempleo`, `infojobs`, `indeed`, `linkedin` | `?source=tecnoempleo` |
| `min_score` | 0-100 | `?min_score=60` |

**Parámetros de `POST /offers/scrape`:**

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `q` | Término de búsqueda | `python` |
| `location` | Ciudad o país | `Valencia` |
| `portal` | Portal o `all` | `tecnoempleo` |

**Ejemplo de respuesta de una oferta:**

```json
{
  "id": 5,
  "title": "Backend Developer Python",
  "company": "Tech SL",
  "location": "Valencia",
  "url": "https://...",
  "description": "Buscamos desarrollador...",
  "source": "tecnoempleo",
  "status": "nueva",
  "score": 82,
  "score_reason": "Buen encaje técnico en backend Python/FastAPI.",
  "matched_keywords": ["Python", "FastAPI", "REST"],
  "missing_keywords": ["Kubernetes", "AWS"]
}
```

---

## 8. Scoring LLM

El scoring usa **Google Gemini** para analizar el encaje entre la oferta y tu CV.

### Puntuar una sola oferta

```http
POST /scoring/5
```

### Puntuar todas las ofertas pendientes

```http
POST /scoring/all
```

### Puntuar con pre-filtro semántico (recomendado)

El parámetro `pre_filter` selecciona primero las N ofertas más similares al CV usando embeddings (gratuito, sin API) y solo llama al LLM para esas. Ahorra tokens y dinero.

```http
POST /scoring/all?pre_filter=20
```

**Respuesta del scoring:**

```json
{
  "offer_id": 5,
  "score": 82,
  "matched_keywords": ["Python", "FastAPI", "REST API"],
  "missing_keywords": ["Kubernetes", "AWS"],
  "reason": "Buen encaje técnico en backend Python/FastAPI. Falta experiencia cloud."
}
```

**Sistema de fallback automático:** si el modelo principal falla (quota agotada, sobrecarga), prueba automáticamente `gemini-2.5-flash` → `gemini-2.0-flash` → `gemini-2.0-flash-lite`.

---

## 9. Búsqueda semántica

La búsqueda semántica usa `sentence-transformers` (modelo `all-MiniLM-L6-v2`) y similitud coseno. Funciona **sin coste de API**.

### Buscar por texto libre

```http
GET /search?q=trabajo+de+backend+con+microservicios&top_k=10
```

Encuentra ofertas que coincidan en *significado*, no solo en palabras exactas.

### Buscar las más similares a tu CV

```http
GET /search/cv?top_k=10
```

Devuelve las ofertas cuya descripción se parece más al contenido de tu CV.

**Respuesta:**

```json
[
  {
    "offer": { "id": 3, "title": "Python Developer", ... },
    "similarity": 0.8721
  }
]
```

El campo `similarity` va de 0 a 1; por encima de 0.7 suele indicar buen encaje.

---

## 10. Gestión del estado de ofertas

Cada oferta tiene un estado: `nueva` (por defecto), `aplicada` o `descartada`.

### Cambiar estado

```http
PATCH /offers/12/status
Content-Type: application/json

{"status": "aplicada"}
```

### Ver solo mis aplicaciones

```http
GET /offers?status=aplicada
```

### Eliminar una oferta

```http
DELETE /offers/12
```

---

## 11. Docker

```bash
cp .env.example .env          # añade tu GEMINI_API_KEY
cp tu_cv.pdf data/cv.pdf      # tu CV

docker compose up -d --build
```

La app queda en [http://localhost:8000](http://localhost:8000).

El directorio `data/` se monta como volumen: las ofertas y el CV persisten aunque el contenedor se reinicie.

Para ver los logs:

```bash
docker compose logs -f
```

---

## 12. Tests

```bash
pip install -r requirements-dev.txt
pytest
```

La suite cubre 56 tests sobre repositorio, servicios (scoring, scraping, embeddings, CV) y todos los endpoints. El LLM y el modelo de embeddings van mockeados: corre en ~1 segundo sin necesitar red ni API key.

---

## 13. Preguntas frecuentes

**¿El scraping falla en algunos portales?**
LinkedIn solo devuelve listado público sin descripción. Infojobs e Indeed necesitan Playwright instalado (`playwright install chromium`). Tecnoempleo es el más estable.

**¿El scoring tarda mucho?**
Es normal — el LLM añade ~4 segundos de pausa entre ofertas para respetar los límites de la API gratuita. Para 20 ofertas calcula ~1-2 minutos. Usa `pre_filter` para reducir la cantidad.

**¿Qué pasa si no tengo API key de Gemini?**
Puedes usar todo excepto el scoring: scraping, búsqueda semántica y gestión de estado funcionan sin API key.

**¿Dónde se guardan las ofertas?**
En `data/offers.json`. Se deduplicam automáticamente por URL, así que puedes scrapear varias veces sin duplicados.

**¿Cómo actualizo el CV?**
Reemplaza `data/cv.pdf` (o `data/cv.txt`) y reinicia la app. El CV se carga en cada llamada al scoring.

**¿Puedo añadir más portales?**
Sí. Crea una clase en `services/scrapers/` que herede de `BaseScraper` e impleméntala. La arquitectura es extensible por diseño.
