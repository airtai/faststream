#!/bin/bash

echo "Running pyup_dirs..."
pyup_dirs --py38-plus --recursive faststream examples tests

echo "Running ruff linter (isort, flake, etc. replacement)..."
ruff check --fix

echo "Running ruff formater (black replacement)..."
ruff format
