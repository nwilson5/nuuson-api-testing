from fastapi import APIRouter, HTTPException
from nwut.clients.gemini import GeminiClient
from nwut import errors

router = APIRouter()

_client: GeminiClient | None = None


def _get_client() -> GeminiClient:
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client


@router.get("/hello")
async def hello():
    return {"message": "hello from nuuson testing API"}


@router.get("/ask")
async def ask(q: str):
    try:
        return {"response": _get_client().generate(q)}
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except errors.RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except errors.ApiError as e:
        raise HTTPException(status_code=502, detail=str(e))
