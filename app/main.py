from fastapi import FastAPI

app = FastAPI(title="AlaSonora AI Engine")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
