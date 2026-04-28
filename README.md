# Python Agent Challenge

Solução para o desafio técnico de IA: agente Python com orquestração de fluxo, base de conhecimento em Markdown acessada via HTTP, FastAPI, memória de sessão e deploy com Docker.

---

## Como rodar

### Pré-requisitos

- Docker + Docker Compose
- Chave de API de um LLM compatível com a API OpenAI (ex: OpenAI, Ollama, LiteLLM)

### 1. Clone o repositório

```bash
git clone https://github.com/PauloVictor75/python-agent-challenge.git
cd python-agent-challenge
```

### 2. Configure o ambiente

```bash
cp .env.example .env
# edite .env e preencha LLM_API_KEY
```

### 3. Suba com Docker

```bash
docker compose up -d --build
```

### 4. Teste

```bash
# Healthcheck
curl http://localhost:8000/health

# Pergunta com contexto na KB
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "O que é composição?"}'

# Pergunta fora do escopo (fallback)
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "Qual a capital do Brasil?"}'

# Com session_id (memória de contexto)
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "O que é composição?", "session_id": "sessao-123"}'

curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "Pode resumir em uma frase?", "session_id": "sessao-123"}'
```

### 5. Swagger UI

Acesse: http://localhost:8000/docs

---

## Como funciona o fluxo

```
POST /messages
     │
     ├─► [1] Recupera histórico da sessão (se session_id fornecido)
     │
     ├─► [2] KB Tool: GET KB_URL → parse Markdown → ranking por palavras-chave
     │
     ├─► [3] DECISÃO:
     │        ├── Sem seções relevantes → FALLBACK (LLM não é chamado)
     │        └── Com seções relevantes → continua
     │
     ├─► [4] LLM: pergunta + contexto + histórico → answer
     │
     ├─► [5] Valida resposta (garante que não é vazia)
     │
     └─► { "answer": "...", "sources": [{"section": "..."}] }
```

---

## Regras de decisão do orquestrador

| Situação | Decisão |
|---|---|
| Toda requisição | KB Tool é consultada SEMPRE, antes do LLM |
| KB retorna seções relevantes | LLM é chamado com pergunta + contexto |
| KB não encontra contexto | Fallback imediato, LLM não é chamado |
| LLM falha (erro HTTP, timeout) | Fallback aplicado |
| LLM retorna resposta vazia | Fallback aplicado |
| LLM retorna frase de fallback | sources retorna vazio [] |

**A tool nunca responde diretamente ao usuário — apenas fornece contexto para o LLM.**

---

## Contrato da API

### Requisição

```json
{
  "message": "O que é composição?",
  "session_id": "sessao-123"
}
```

`session_id` é opcional. Se não enviado, cada chamada é independente.

### Resposta com contexto

```json
{
  "answer": "Composição é quando uma função/classe utiliza outra instância para executar parte do trabalho.",
  "sources": [
    { "section": "Composição" }
  ]
}
```

### Resposta sem contexto (fallback)

```json
{
  "answer": "Não encontrei informação suficiente na base para responder essa pergunta.",
  "sources": []
}
```

---

## Memória de sessão

- Ativada quando `session_id` é fornecido
- Histórico limitado aos últimos `MAX_HISTORY_MESSAGES` turnos (padrão: 5)
- Sessões expiram após `SESSION_TTL_SECONDS` segundos de inatividade (padrão: 1800 = 30 min)
- Sessões isoladas por `session_id` — sem vazamento de estado entre sessões

---

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `KB_URL` | URL oficial do desafio | URL do Markdown da base de conhecimento |
| `LLM_PROVIDER` | `openai` | Identificador do provider (informativo) |
| `LLM_MODEL` | `gpt-4o-mini` | Nome do modelo |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | Base URL da API (compatÍvel OpenAI) |
| `LLM_API_KEY` | _(obrigatório)_ | Chave de API |
| `MAX_HISTORY_MESSAGES` | `5` | Turnos de histórico por sessão |
| `SESSION_TTL_SECONDS` | `1800` | TTL de sessão inativa (segundos) |
| `LOG_LEVEL` | `INFO` | Nível de log |

---

## Estrutura do projeto

```
app/
├── main.py          # FastAPI: endpoints, schemas Pydantic, zero lógica de negócio
├── orchestrator.py  # Fluxo principal: coordena KB → LLM → sessão → resposta
├── session.py       # Memória de sessão em memória com TTL e limite de histórico
├── config.py        # Settings via pydantic-settings + .env
├── tools/
│   └── kb_tool.py   # GET KB_URL → parse Markdown por tópicos → ranking por keywords
└── llm/
    └── client.py    # Cliente HTTP genérico compatÍvel com API OpenAI
```

---

## Compatibilidade de providers LLM

Qualquer provider compatível com a API OpenAI funciona:

| Provider | `LLM_BASE_URL` | Exemplo de modelo |
|---|---|---|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Ollama (local) | `http://localhost:11434/v1` | `llama3.2` |
| LiteLLM proxy | `http://localhost:4000/v1` | qualquer |
