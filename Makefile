sources = amano tests
.DEFAULT_GOAL := all

toml_sort:
	toml-sort pyproject.toml --all --in-place

isort:
	poetry run isort $(sources)

black:
	poetry run black -S -l 80 --target-version py38 $(sources)

flake:
	poetry run flake8 amano

mypy:
	poetry run mypy --install-types --show-error-codes --non-interactive .

bandit:
	poetry run bandit -r . -x ./tests,./test,./.venv,./cookbook

test:
	poetry run pytest tests

lint: isort black flake mypy

audit: bandit

tests: test

all: lint audit tests
