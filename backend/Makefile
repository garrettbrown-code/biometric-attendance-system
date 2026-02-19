.PHONY: format lint test check

format:
	python -m black .
	python -m ruff check . --fix

lint:
	python -m black . --check
	python -m ruff check .

test:
	python -m pytest -q

check: lint test
