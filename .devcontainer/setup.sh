# Update pip
pip install --upgrade pip

# Install dev packages
pip install -e ".[dev]"

# Install pre-commit hooks if not installed already
pre-commit install
