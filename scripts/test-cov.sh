#!/bin/bash

bash scripts/test.sh -m "all" "$@"

coverage combine
coverage report --show-missing --skip-covered --sort=cover --precision=2

rm .coverage*
