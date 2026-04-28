import logging
import uuid
from dataclasses import dataclass
from typing import List
from app.tools.kb_tool import KnowledgeBaseTool, KBSection
from app.llm.client import LLMClient, LLMError
from app.session import SessionManager

logger = logging.getLogger(__name__)
FALLBACK_ANSWER = "Não encontrei informação suficiente na base para responder essa pergunta."

@dataclass
class SourceRef:
    section: str

@dataclass
class OrchestratorResult:
    answer: str
    sources: List[SourceRef]

class Orchestrator:
    def __init__(self, kb_tool=None, llm_client=None, session_manager=None):
        self.kb_tool = kb_tool or KnowledgeBaseTool()
        self.llm_client = llm_client or LLMClient()
        self.session_manager = session_manager or SessionManager()

    async def handle(self, message: str, session_id=None) -> OrchestratorResult:
        sid = session_id or str(uuid.uuid4())
        logger.info("Processando | session=%s | msg=%.80s", sid, message)
        history = self.session_manager.get_history(sid)
        logger.info("Consultando Knowledge Base...")
        relevant_sections = await self.kb_tool.fetch_relevant_sections(message)
        if not relevant_sections:
            logger.info("Nenhuma secao relevante -> fallback")
            return OrchestratorResult(answer=FALLBACK_ANSWER, sources=[])
        logger.info("Secoes relevantes: %s", [s.section for s in relevant_sections])
        context = self._build_context(relevant_sections)
        try:
            answer = await self.llm_client.complete(
                question=message, context=context, history=history
            )
        except LLMError as exc:
            logger.error("Falha no LLM: %s", exc)
            return OrchestratorResult(answer=FALLBACK_ANSWER, sources=[])
        answer = self._validate_answer(answer)
        if answer == FALLBACK_ANSWER:
            return OrchestratorResult(answer=FALLBACK_ANSWER, sources=[])
        self.session_manager.add_turn(sid, message, answer)
        sources = [SourceRef(section=s.section) for s in relevant_sections]
        return OrchestratorResult(answer=answer, sources=sources)

    def _build_context(self, sections) -> str:
        return "\n\n".join(f"## {s.section}\n{s.content}" for s in sections)

    def _validate_answer(self, answer: str) -> str:
        if not answer or not answer.strip():
            return FALLBACK_ANSWER
        return answer.strip()
