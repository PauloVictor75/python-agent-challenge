import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

class LLMError(Exception):
    pass

SYSTEM_PROMPT = """Você é um assistente especializado que responde perguntas com base EXCLUSIVAMENTE no contexto fornecido abaixo.

Regras:
1. Responda apenas com informações presentes no contexto.
2. Se o contexto não contiver a informação necessária, responda EXATAMENTE com esta frase sem modificar nada: Não encontrei informação suficiente na base para responder essa pergunta.
3. Seja objetivo e direto.
4. Responda no mesmo idioma da pergunta do usuário.
5. Não invente informações."""

class LLMClient:
    def __init__(self):
        self.base_url = settings.LLM_BASE_URL.rstrip("/")
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self._endpoint = f"{self.base_url}/chat/completions"

    async def complete(self, question: str, context: str, history=None) -> str:
        messages = self._build_messages(question, context, history or [])
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 1024,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self._endpoint, json=payload, headers=self._headers()
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            raise LLMError(f"HTTP {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.RequestError as exc:
            raise LLMError(f"Erro de rede ao chamar LLM: {exc}") from exc
        return self._extract_text(data)

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_messages(self, question: str, context: str, history: list) -> list:
        user_prompt = (
            f"Contexto da base de conhecimento:\n---\n{context}\n---\n\nPergunta: {question}"
        )
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def _extract_text(self, data: dict) -> str:
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Resposta inesperada do LLM: {data}") from exc
        if not isinstance(text, str) or not text.strip():
            raise LLMError("LLM retornou resposta vazia ou invalida.")
        return text.strip()
