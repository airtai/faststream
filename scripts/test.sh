#!/bin/bash

coverage run -m pytest -m "all" "$@" || coverage run -m pytest -m "all" "$@" || coverage run -m pytest -m "all" "$@"
