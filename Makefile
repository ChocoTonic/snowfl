# Makefile for the Snowfl project

.PHONY: install test build publish

install:
	uv sync --extra dev

test:
	PYTHONPATH=src uv run python -m coverage run -m pytest tests/
	PYTHONPATH=src uv run python -m coverage xml

build:
	rm -rf src/snowfl.egg-info dist
	uv run python -m build

publish:
	uv publish
