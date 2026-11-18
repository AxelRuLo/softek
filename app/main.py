from fastapi import FastAPI

app = FastAPI(title="REST API")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check: does not require a database connection."""
    return {"status": "ok"}
