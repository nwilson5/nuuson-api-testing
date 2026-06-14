from fastapi import FastAPI
from app.api.v1 import routes

app = FastAPI(
    title="nuuson testing API",
    description="POC service for nuuson.dev API platform.",
    version="0.1.0",
)

app.include_router(routes.router, prefix="/v1/testing", tags=["testing"])


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}
