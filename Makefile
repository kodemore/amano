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

pylint:
	poetry run pylint amano

mypy:
	poetry run mypy --install-types --show-error-codes --non-interactive .

audit_dependencies:
	poetry export --without-hashes -f requirements.txt | poetry run safety check --full-report --stdin

bandit:
	poetry run bandit -r . -x ./tests,./test

test:
	poetry run pytest tests

lint: isort black flake mypy toml_sort

audit: audit_dependencies bandit

tests: test

all: lint audit tests
