up:
	docker compose up -d --build

down:
	docker compose down

test:
	@echo "=== Healthcheck ===" && \
	curl -s http://localhost:8000/health | python3 -m json.tool && \
	echo "=== O que é composição? ===" && \
	curl -s -X POST http://localhost:8000/messages \
	  -H "Content-Type: application/json" \
	  -d '{"message":"O que é composição?"}' | python3 -m json.tool && \
	echo "=== Fallback ===" && \
	curl -s -X POST http://localhost:8000/messages \
	  -H "Content-Type: application/json" \
	  -d '{"message":"Qual a capital do Brasil?"}' | python3 -m json.tool

.PHONY: up down test
