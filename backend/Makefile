.PHONY: run install test lint format check

run:
	FLASK_APP=app.factory:create_app FLASK_ENV=development flask run --port=8000

install:
	pip install -r requirements.txt

format:
	python -m black .
	python -m ruff check . --fix

lint:
	python -m black . --check
	python -m ruff check .

test:
	python -m pytest -q

check: lint test
