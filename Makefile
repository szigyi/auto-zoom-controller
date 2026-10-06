.PHONY: help venv install dev test lint format check run-dry web clean

PYTHON := .venv/bin/python
PIP := .venv/bin/pip
PYTEST := .venv/bin/pytest
RUFF := .venv/bin/ruff

help:
	@echo "Available commands:"
	@echo "  make venv         - Create Python virtual environment (.venv)"
	@echo "  make install      - Install package in editable mode"
	@echo "  make dev          - Install development dependencies (pytest, ruff, etc.)"
	@echo "  make test         - Run test suite"
	@echo "  make lint         - Run ruff linter check"
	@echo "  make format       - Format code with ruff"
	@echo "  make check        - Run lint and test checks"
	@echo "  make run-dry      - Run dry-run zoom simulation"
	@echo "  make web          - Start the localhost engine dry-run web UI"
	@echo "  make clean        - Remove build artifacts and caches"

venv:
	python3 -m venv .venv
	$(PIP) install --upgrade pip

install:
	$(PIP) install -e .

dev:
	$(PIP) install -e ".[dev]"
	@if [ -f .venv/bin/pre-commit ]; then .venv/bin/pre-commit install; fi

test:
	@if [ -f $(PYTEST) ]; then \
		$(PYTEST); \
	else \
		$(PYTHON) -m unittest discover -s tests -p "test_*.py"; \
	fi

lint:
	@if [ -f $(RUFF) ]; then \
		$(RUFF) check .; \
	else \
		echo "ruff not installed in .venv. Run 'make dev' to install dev tools."; \
	fi

format:
	@if [ -f $(RUFF) ]; then \
		$(RUFF) format .; \
		$(RUFF) check --fix .; \
	else \
		echo "ruff not installed in .venv. Run 'make dev' to install dev tools."; \
	fi

check: lint test

run-dry:
	$(PYTHON) -m auto_zoom_controller.main --dry-run -i 0.5 -d 0.05 -s 20

web:
	$(PYTHON) -m auto_zoom_controller.web.server

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache/ .ruff_cache/ htmlcov/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
