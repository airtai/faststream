#!/bin/bash

bash scripts/test.sh -m "all" "$@"

coverage combine
coverage report --show-missing

rm .coverage*
