from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import APIConnectionError, APIError, APITimeoutError, NotFoundError
from pydantic import ValidationError

from app.config import get_settings
from app.db.repository import LogAnalysisRepository
from app.llm.mock import MockLLMClient
from app.llm.openai_compatible import OpenAICompatibleLLMClient
from app.schemas.log_analysis import LogAnalysisResponse, LogInput, StoredLogAnalysis
from app.services.log_analysis_service import LogAnalysisService

settings = get_settings()

# Initialize LLM client based on provider
if settings.llm_provider == "mock":
    llm_client = MockLLMClient()
else:
    llm_client = OpenAICompatibleLLMClient(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
    )

analysis_service = LogAnalysisService(llm_client=llm_client)
repository = LogAnalysisRepository(db_path=settings.database_url)

frontend_dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"

app = FastAPI(
    title="Local LLM Log Analyzer",
    description="Analyze application logs and stacktraces with a local LLM via Ollama or LM Studio.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _frontend_index() -> FileResponse:
    return FileResponse(frontend_dist / "index.html")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "provider": settings.llm_provider,
        "base_url": settings.llm_base_url,
        "model": settings.llm_model,
    }


@app.post("/logs/analyze", response_model=LogAnalysisResponse)
def analyze_log(log_input: LogInput) -> LogAnalysisResponse:
    try:
        analysis = analysis_service.analyze(log_input)
        analysis_id = repository.save(log_input, analysis)
        return LogAnalysisResponse(analysis_id=analysis_id, analysis=analysis)
    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail="LLM returned an invalid analysis payload that failed schema validation.",
        ) from exc
    except NotFoundError as exc:
        raise HTTPException(
            status_code=502,
            detail="Configured LLM model was not found in the provider.",
        ) from exc
    except (APIConnectionError, APITimeoutError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not reach the LLM provider. Check base URL and local model server.",
        ) from exc
    except (APIError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM provider returned an error: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unexpected internal error during log analysis.",
        ) from exc


@app.get("/logs", response_model=list[StoredLogAnalysis])
def list_logs() -> list[StoredLogAnalysis]:
    return repository.list_all()


@app.get("/logs/{analysis_id}", response_model=StoredLogAnalysis)
def get_log(analysis_id: int) -> StoredLogAnalysis:
    analysis = repository.get(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Log analysis not found")
    return analysis


@app.delete("/logs/{analysis_id}")
def delete_log(analysis_id: int) -> dict:
    deleted = repository.delete(analysis_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Log analysis not found")
    return {"deleted": True, "analysis_id": analysis_id}


@app.get("/")
def frontend_root() -> FileResponse:
    if (frontend_dist / "index.html").exists():
        return _frontend_index()
    raise HTTPException(
        status_code=404,
        detail="Frontend build not found. Run 'npm run build' inside frontend or use Vite dev mode.",
    )


@app.get("/{full_path:path}")
def frontend_spa_fallback(full_path: str) -> FileResponse:
    requested_file = frontend_dist / full_path
    if requested_file.exists() and requested_file.is_file():
        return FileResponse(requested_file)
    if (frontend_dist / "index.html").exists():
        return _frontend_index()
    raise HTTPException(status_code=404, detail="Not found")
