#!/bin/bash

echo "Running pyup_dirs..."
pyup_dirs --py38-plus --recursive faststream examples tests docs

echo "Running ruff linter (isort, flake, pyupgrade, etc. replacement)..."
ruff check

# echo "Running ruff formater (black replacement)..."
# ruff format

echo "Running black..."
black faststream examples tests docs
