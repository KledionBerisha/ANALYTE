# Komandat e zakonshme. Në Windows pa `make`, ekzekutoni rreshtat drejtpërdrejt.

PYTHONPATH := backend/src:.
export PYTHONPATH

.PHONY: dev db migrate api worker test test-postgres eval tables

dev: db migrate
	@echo "Baza gati. Nisni API-në me 'make api' dhe punëtorin me 'make worker'."

db:
	docker compose up -d --wait

migrate:
	cd backend && alembic upgrade head

api:
	uvicorn analyte.main:app --reload --app-dir backend/src

worker:
	arq analyte.orchestration.worker.WorkerSettings

test:
	python -m pytest

test-postgres: db
	ANALYTE_TEST_DATABASE_URL=postgresql+psycopg://analyte:analyte@localhost:5433/analyte_test \
		python -m pytest tests/integration

eval:
	python -m evaluation.harness --dataset data/v1 --pipeline grounding --ocr

tables:
	python scripts/build_tables.py
