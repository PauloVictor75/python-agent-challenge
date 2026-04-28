import logging
from fastapi import FastAPI, status
from pydantic import BaseModel, Field
from app.config import settings
from app.orchestrator import Orchestrator

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

_orchestrator = Orchestrator()

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="Agente LLM com Knowledge Base em Markdown via HTTP.",
    docs_url="/docs",
    redoc_url="/redoc",
)

class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = Field(default=None)

class SourceRef(BaseModel):
    section: str

class MessageResponse(BaseModel):
    answer: str
    sources: list[SourceRef]

class HealthResponse(BaseModel):
    status: str
    version: str

@app.get("/health", response_model=HealthResponse, tags=["Infra"])
async def health():
    return HealthResponse(status="ok", version=settings.APP_VERSION)

@app.post("/messages", response_model=MessageResponse, status_code=status.HTTP_200_OK, tags=["Agent"])
async def post_message(request: MessageRequest):
    result = await _orchestrator.handle(message=request.message, session_id=request.session_id)
    return MessageResponse(
        answer=result.answer,
        sources=[SourceRef(section=s.section) for s in result.sources],
    )
