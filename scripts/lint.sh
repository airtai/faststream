pyup_dirs --py38-plus --recursive propan tests
mypy propan
ruff propan examples tests --fix
black propan examples tests
isort propan examples tests