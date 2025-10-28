.PHONY: install test lint format clean run help

help: ## Show this help message
	@echo "CollabIQ - Email-based collaboration tracking system"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Install all dependencies
	uv sync

test: ## Run all tests
	uv run pytest

lint: ## Run linting and type checking
	uv run ruff check .
	uv run mypy src/

format: ## Format code with ruff
	uv run ruff format .
	uv run ruff check --fix .

clean: ## Clean up cache files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

run: ## Run the main application (placeholder)
	@echo "Main application entry point not yet implemented"
	@echo "Complete feasibility study (Phase 0) and Phase 1a-1b first"
