#!/bin/bash

source ./scripts/set_variables.sh

docker-compose -p $DOCKER_COMPOSE_PROJECT -f docker/dev.yml up -d --no-recreate
