.PHONY: run dev up down test

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8001

dev:
	uvicorn app.main:app --reload --port 8001

up:
	docker compose up --build

down:
	docker compose down

test:
	pytest -q
