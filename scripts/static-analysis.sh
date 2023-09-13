#!/bin/bash

echo "Running mypy..."
mypy faststream

echo "Running bandit..."
bandit -c pyproject.toml -r faststream

echo "Running semgrep..."
semgrep scan --config auto --error
