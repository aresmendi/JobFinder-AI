from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import offers, scoring, search

app = FastAPI(title="JobFinder AI")

app.include_router(offers.router)
app.include_router(scoring.router)
app.include_router(search.router)

@app.get("/health")
def health():
    return {"status": "ok"}

# Sirve el frontend en / (debe ir al final para no pisar los routers)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
