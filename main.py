from fastapi import FastAPI
from routers import offers, scoring
app = FastAPI(title="JobFinder AI")

app.include_router(offers.router)

app.include_router(scoring.router)

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)