#!/bin/bash

echo "Running pyup_dirs..."
pyup_dirs --py38-plus --recursive faststream examples tests docs_src

echo "Running ruff..."
ruff faststream examples tests docs_src --fix

echo "Running black..."
black faststream examples tests docs_src
