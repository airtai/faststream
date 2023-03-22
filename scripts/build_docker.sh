#!/bin/bash

if test -z "$PYTHON_VERSION"
then
      echo 'PYTHON_VERSION variable not set, exiting'
      exit -1
fi
echo PYTHON_VERSION variable set to $PYTHON_VERSION

docker build --build-arg PYTHON_VERSION=$PYTHON_VERSION -t ghcr.io/airtai/fastkafka:$PYTHON_VERSION-slim-bullseye .
