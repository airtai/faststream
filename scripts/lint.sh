pyup_dirs --py38-plus --recursive faststream tests
mypy faststream
ruff faststream examples tests --fix
black faststream examples tests
isort faststream examples tests