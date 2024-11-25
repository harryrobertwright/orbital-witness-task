.PHONY: run install lint format test docker-build docker-run

run:
	pipenv run uvicorn src.main:app --reload

install:
	pipenv install --dev

lint:
	pipenv run ruff check .

format:
	pipenv run ruff format .

test:
	pipenv run pytest

docker:
	docker build -t orbital-witness-task . && docker run -p 8000:8000 orbital-witness-task
