
.DEFAULT_GOAL := all

toml_sort:
	toml-sort pyproject.toml --all --in-place

isort:
	poetry run isort --recursive .

black:
	poetry run black .

flake8:
	poetry run flake8 .

pylint:
	poetry run pylint amano

mypy:
	poetry run mypy --install-types --non-interactive .

audit_dependencies:
	poetry export --without-hashes -f requirements.txt | poetry run safety check --full-report --stdin

bandit:
	poetry run bandit -r . -x ./tests,./test

test:
	poetry run pytest

lint: isort black flake8 mypy toml_sort

audit: audit_dependencies bandit

tests: test

all: lint audit tests
