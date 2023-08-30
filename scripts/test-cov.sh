#!/bin/bash

bash scripts/test.sh "$@"

coverage combine
coverage report --show-missing

rm .coverage*
