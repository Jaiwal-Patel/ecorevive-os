.PHONY: up down build logs migrate seed founder test lint check shell

up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

migrate:
	docker compose exec backend python manage.py migrate

seed:
	docker compose exec backend python manage.py seed_ecorevive

founder:
	docker compose exec backend python manage.py bootstrap_governance --founder-email "$${FOUNDER_EMAIL:-ujaiwal@outlook.com}"

test:
	docker compose exec backend pytest
	docker compose exec frontend npm run test -- --run

lint:
	docker compose exec backend ruff check .
	docker compose exec frontend npm run lint

check:
	./scripts/run_checks.sh

shell:
	docker compose exec backend python manage.py shell
