#!/usr/bin/env make

.DEFAULT_GOAL := help

PACKAGE_NAME		:= $(shell grep '^name = ' pyproject.toml | sed 's/name = "\(.*\)"/\1/')
PACKAGE_TEST_DIR	:= $(TMPDIR)
PYTHON_VERSION		:= 3.14
VENV_DIR			:= .venv

help: ## Print this help
	@echo 'Usage:'
	@echo '  make <target>'
	@echo ''
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  %-25s %s\n", $$1, $$2}'
.PHONY: help

build: clean test ## Build the package (clean, test, build)
	@echo $@
	uv build
.PHONY: build

check-version: ## Check if git tag equals version in pyproject.toml
	@echo $@
	@TAG=$$(git tag -l --points-at HEAD); \
	echo "$$TAG" | grep -E "^[0-9]+\.[0-9]+\.[0-9]+"; \
	grep "version = \"$$TAG\"" pyproject.toml
.PHONY: check-version

clean: ## Clean files and directories
	@echo $@
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "test" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
.PHONY: clean

deploy-prod: build ## Deploy to prod pypi.org (build, deploy)
	@echo $@
	uv run twine upload dist/*
.PHONY: deploy-prod

deploy-test: build ## Deploy to test pypi.org (build, deploy)
	@echo $@
	uv run twine upload --repository testpypi dist/*
.PHONY: deploy-test

install: ## Install local venv and dev packages
	@echo $@
	uv venv --clear $(VENV_DIR) --python $(PYTHON_VERSION)
	uv pip install -U --group dev
.PHONY: install

lint: ## Run formatter, linters etc.
	@echo $@
	uvx ruff format
	uvx ruff check --fix
	uvx ty check -q
	uvx pymarkdownlnt scan "**/*.md"
	uvx yamllint -c .yamllint ./
.PHONY: lint

test: ## Run tests
	@echo $@
	uv run pytest tests/
.PHONY: test

validate-local-package: ## Install the locally built package and perform basic validation
	@echo $@
	@DEST="$(PACKAGE_TEST_DIR)$(PACKAGE_NAME)"; \
	mkdir -p "$$DEST"; \
	cd "$$DEST" && \
	trap 'rm -fr $(VENV_DIR)' EXIT; \
	uv venv --clear $(VENV_DIR) --python $(PYTHON_VERSION) && \
	VIRTUAL_ENV=$(VENV_DIR) uv pip install -U "$(CURDIR)/dist/$(PACKAGE_NAME)-"*.whl && \
	VIRTUAL_ENV=$(VENV_DIR) uv run $(PACKAGE_NAME) --help
.PHONY: validate-local-package

validate-pypi-package: ## Install the package from pypi.org and perform basic validation
	@echo $@
	@TAG=$$(git tag -l --points-at HEAD); \
	DEST="$(PACKAGE_TEST_DIR)$(PACKAGE_NAME)"; \
	mkdir -p "$$DEST"; \
	cd "$$DEST" && \
	trap 'rm -fr $(VENV_DIR)' EXIT; \
	uv venv --clear $(VENV_DIR) --python $(PYTHON_VERSION) && \
	VIRTUAL_ENV=$(VENV_DIR) uv pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple $(PACKAGE_NAME)==$$TAG && \
	VIRTUAL_ENV=$(VENV_DIR) uv run $(PACKAGE_NAME) --help
.PHONY: validate-pypi-package
