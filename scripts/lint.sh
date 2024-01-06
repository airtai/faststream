#!/bin/bash

echo "Running ruff linter (isort, flake, pyupgrade, etc. replacement)..."
ruff check

echo "Running ruff formatter (black replacement)..."
ruff format
