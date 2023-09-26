#!/bin/bash

source ./scripts/set_variables.sh

docker-compose -p $DOCKER_COMPOSE_PROJECT -f docs/includes/docker-compose.yaml down
