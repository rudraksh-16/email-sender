.PHONY: help install gui headless test lint format clean

PY := uv run python

help:
	@echo "Targets:"
	@echo "  install   - sync Python deps (uv)"
	@echo "  gui       - launch pywebview window"
	@echo "  headless  - run FastAPI without GUI on :8765 (curl-testable)"
	@echo "  test      - pytest"
	@echo "  lint      - ruff check"
	@echo "  format    - ruff format"
	@echo "  clean     - remove caches"

install:
	uv sync

gui:
	$(PY) -m app

headless:
	EMAIL_APP_HEADLESS=1 $(PY) -m app

test:
	uv run pytest

lint:
	uv run ruff check

format:
	uv run ruff format

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
