# Makefile for the Snowfl project

.PHONY: install test test-live test-all build publish

install:
	uv sync --extra dev

test:
	PYTHONPATH=src uv run python -m coverage run -m pytest tests/
	PYTHONPATH=src uv run python -m coverage xml

test-live:
	PYTHONPATH=src uv run python -m pytest -m live --reruns 2 --reruns-delay 5 tests/

test-all:
	PYTHONPATH=src uv run python -m pytest -m "live or not live" tests/

build:
	rm -rf src/snowfl.egg-info dist
	uv run python -m build

publish: build
	uv publish
