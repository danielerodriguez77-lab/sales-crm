.PHONY: up down logs api-shell web-shell fmt lint test

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

api-shell:
	docker compose exec api bash

web-shell:
	docker compose exec web sh

fmt:
	docker compose exec api black app
	docker compose exec api isort app
	docker compose exec web npm run format

lint:
	docker compose exec api ruff app
	docker compose exec web npm run lint

test:
	docker compose exec api pytest

db-migrate:
	docker compose exec api alembic upgrade head

db-seed:
	docker compose exec api python -m app.seed
