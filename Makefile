.PHONY: help install lint format test test-cov build clean security all

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync --dev

lint: ## Run linting (ruff)
	uv run ruff check .

lint-fix: ## Run linting with auto-fix
	uv run ruff check . --fix

format: ## Run code formatting
	uv run ruff format .

format-check: ## Check code formatting
	uv run ruff format --check .

type-check: ## Run type checking
	uv run mypy services/ infrastructure/ --ignore-missing-imports

test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=services --cov=infrastructure --cov-report=term-missing --cov-report=html

test-integration: ## Run integration tests
	uv run python -m pytest test_*.py -v

security: ## Run security checks
	uv run safety check
	uv run bandit -r services/ infrastructure/

build: ## Build the package
	uv build

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

pre-commit-install: ## Install pre-commit hooks
	pip install pre-commit
	pre-commit install

pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files

ci-local: lint format-check type-check test test-integration security build ## Run full CI pipeline locally

all: lint format type-check test build ## Run common development checks
