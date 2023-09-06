#!/bin/bash

coverage run -m pytest -x --ff -m "all" "$@" || \
coverage run -m pytest -x --ff -m "all" "$@" || \
coverage run -m pytest -x --ff -m "all" "$@"
