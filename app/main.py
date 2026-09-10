from fastapi import FastAPI

app = FastAPI(title="Takeaway Service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
