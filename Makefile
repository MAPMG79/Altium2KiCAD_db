# Makefile for Altium to KiCAD Database Migration Tool

.PHONY: help clean clean-pyc clean-build clean-test install install-dev test test-all test-coverage lint lint-flake8 lint-mypy format format-black format-isort docs build dist docker docker-build docker-run pre-commit security benchmark init run-gui run-cli

help:
	@echo "Altium to KiCAD Database Migration Tool"
	@echo "make help              - Show this help message"
	@echo "make clean             - Remove all build, test, and coverage artifacts"
	@echo "make clean-pyc         - Remove Python file artifacts"
	@echo "make clean-build       - Remove build artifacts"
	@echo "make clean-test        - Remove test and coverage artifacts"
	@echo "make install           - Install the package in development mode"
	@echo "make install-dev       - Install development dependencies"
	@echo "make test              - Run tests with pytest"
	@echo "make test-all          - Run tests on multiple Python versions with tox"
	@echo "make test-coverage     - Run tests with coverage report"
	@echo "make lint              - Run all linting checks"
	@echo "make lint-flake8       - Check style with flake8"
	@echo "make lint-mypy         - Run type checking with mypy"
	@echo "make format            - Run all code formatters"
	@echo "make format-black      - Format code with black"
	@echo "make format-isort      - Sort imports with isort"
	@echo "make docs              - Generate Sphinx HTML documentation"
	@echo "make build             - Build source and wheel packages"
	@echo "make dist              - Package and upload a release"
	@echo "make docker            - Build and run Docker container"
	@echo "make docker-build      - Build Docker image"
	@echo "make docker-run        - Run Docker container"
	@echo "make pre-commit        - Run pre-commit hooks on all files"
	@echo "make security          - Run security checks"
	@echo "make benchmark         - Run performance benchmarks"
	@echo "make init              - Create directory structure"
	@echo "make run-gui           - Run the GUI"
	@echo "make run-cli           - Run the CLI"

clean: clean-pyc clean-build clean-test

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name '.pytest_cache' -exec rm -fr {} +

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info/

clean-test:
	rm -fr .tox/
	rm -fr .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache/
	rm -fr .mypy_cache/

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pip install -r requirements-dev.txt
	pip install pre-commit
	pre-commit install

test:
	pytest

test-all:
	tox

test-coverage:
	pytest --cov=migration_tool --cov-report=html --cov-report=term-missing

lint: lint-flake8 lint-mypy

lint-flake8:
	flake8 migration_tool tests

lint-mypy:
	mypy migration_tool

format: format-isort format-black

format-black:
	black migration_tool tests

format-isort:
	isort migration_tool tests

docs:
	rm -f docs/migration_tool.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ migration_tool
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

build:
	python -m build

dist: clean build
	twine check dist/*
	@echo "Run 'twine upload dist/*' to upload to PyPI"

docker: docker-build docker-run

docker-build:
	docker build -t altium2kicad .

docker-run:
	docker run -it --rm -v $(PWD)/data:/app/data -v $(PWD)/output:/app/output altium2kicad

pre-commit:
	pre-commit run --all-files

security:
	bandit -r migration_tool

benchmark:
	python scripts/performance_benchmark.py

# Create directory structure
init:
	mkdir -p migration_tool/core
	mkdir -p migration_tool/utils
	mkdir -p tests
	mkdir -p docs
	mkdir -p examples
	mkdir -p scripts
	mkdir -p config

# Run the GUI
run-gui:
	python -m migration_tool.gui

# Run the CLI
run-cli:
	python -m migration_tool.cli --help