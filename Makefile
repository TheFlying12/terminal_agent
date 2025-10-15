.PHONY: help install dev run daemon test lint format clean uninstall shell-zsh shell-bash

# Default target
help:
	@echo "AI Shell - Available commands:"
	@echo "  install     Install the package in development mode"
	@echo "  dev         Start development server with auto-reload"
	@echo "  run         Start the daemon in production mode"
	@echo "  daemon      Alias for run"
	@echo "  test        Run all tests"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code with black"
	@echo "  clean       Clean build artifacts"
	@echo "  uninstall   Uninstall the package"
	@echo "  shell-zsh   Show zsh integration snippet"
	@echo "  shell-bash  Show bash integration snippet"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Development
dev:
	uvicorn ai_shell.server:app --host 127.0.0.1 --port 8765 --reload

# Production
run:
	python -m ai_shell.server

daemon: run

# Testing
test:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=ai_shell --cov-report=html --cov-report=term

# Code quality
lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/
	ruff check --fix src/ tests/

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Uninstall
uninstall:
	pip uninstall ai-shell -y

# Shell integration helpers
shell-zsh:
	@./scripts/zsh_install_snippet.sh

shell-bash:
	@./scripts/bash_install_snippet.sh

# Setup environment
setup-env:
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "Created .env file from env.example"; \
		echo "Please edit .env to configure your AI provider"; \
	else \
		echo ".env file already exists"; \
	fi

# Quick start
quickstart: setup-env install
	@echo ""
	@echo "🚀 AI Shell setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit .env file to configure your AI provider"
	@echo "2. Add shell integration:"
	@echo "   make shell-zsh   # for zsh users"
	@echo "   make shell-bash  # for bash users"
	@echo "3. Restart your shell"
	@echo "4. Press Ctrl-G to use AI Shell!"
