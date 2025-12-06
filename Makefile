# Makefile for the Snowfl project

.PHONY: test coverage

test:
	PYTHONPATH=src uv run python -m coverage run -m pytest tests/
	PYTHONPATH=src uv run python -m coverage xml
