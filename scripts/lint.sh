#!/bin/bash

echo "Running pyup_dirs..."
pyup_dirs --py38-plus --recursive faststream examples tests docs/docs_src faststream_gen_examples

echo "Running ruff..."
ruff faststream examples tests docs/docs_src faststream_gen_examples --fix

echo "Running black..."
black faststream examples tests docs/docs_src faststream_gen_examples
