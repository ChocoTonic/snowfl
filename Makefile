# Makefile for the Snowfl project

.PHONY: test coverage

install:
	uv sync --extra dev

test:
	PYTHONPATH=src uv run python -m coverage run -m pytest tests/
	PYTHONPATH=src uv run python -m coverage xml

.PHONY: build publish test-publish

build:
	rm -rf src/snowfl.egg-info dist
	uv run python -m build

publish:
	uv run python -m twine upload dist/*
