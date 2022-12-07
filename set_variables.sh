#!/bin/bash

export BASE_DOCKER_IMAGE=ghcr.io/airtai/airt-docker-dask-tf2

BRANCH=$(git branch --show-current)
if [ "$BRANCH" == "main" ]; then
    TAG=latest
elif [ "$BRANCH" == "dev" ]; then
    TAG=dev
else
    if [ "$(docker image ls -q $BASE_DOCKER_IMAGE:$BRANCH)" == "" ]; then
        TAG=dev
    else
        TAG=$BRANCH
    fi
fi
DOCKER_IMAGE=$BASE_DOCKER_IMAGE:$TAG

echo PORT_PREFIX variable set to $PORT_PREFIX

export AIRT_JUPYTER_PORT="${PORT_PREFIX}8888"
echo AIRT_JUPYTER_PORT variable set to $AIRT_JUPYTER_PORT

export AIRT_TB_PORT="${PORT_PREFIX}6006"
echo AIRT_TB_PORT variable set to $AIRT_TB_PORT

export AIRT_DASK_PORT="${PORT_PREFIX}8787"
echo AIRT_DASK_PORT variable set to $AIRT_DASK_PORT

export AIRT_DOCS_PORT="${PORT_PREFIX}4000"
echo AIRT_DOCS_PORT variable set to $AIRT_DOCS_PORT


if test -z "$AIRT_DATA"; then
      echo 'AIRT_DATA variable not set, setting to current directory'
      export AIRT_DATA=`pwd`
fi
echo AIRT_DATA variable set to $AIRT_DATA

if test -z "$AIRT_PROJECT"; then
      echo 'AIRT_PROJECT variable not set, setting to current directory'
      export AIRT_PROJECT=`pwd`
fi
echo AIRT_PROJECT variable set to $AIRT_PROJECT

if test -z "$AIRT_GPU_DEVICE"; then
      echo 'AIRT_GPU_DEVICE variable not set, setting to all GPU-s'
      export AIRT_GPU_DEVICE="all"
fi
echo AIRT_GPU_DEVICE variable set to $AIRT_GPU_DEVICE

export UID=$(id -u)
export GID=$(id -g)


export ZOOKEEPER_PORT="${PORT_PREFIX}2181"
echo ZOOKEEPER_PORT variable set to $ZOOKEEPER_PORT

export KAFKA_PORT="${PORT_PREFIX}9092"
echo KAFKA_PORT variable set to $KAFKA_PORT

export DOCKER_COMPOSE_PROJECT="${USER}-fast-kafka-api"
echo DOCKER_COMPOSE_PROJECT variable set to $DOCKER_COMPOSE_PROJECT

if test -z "$KAFKA_HOSTNAME"
then
	echo "KAFKA_HOSTNAME variable not set, setting it to $USER-kafka"
	export KAFKA_HOSTNAME="$USER-kafka-1"
fi

if test -z "$DB_DOWNLOAD_SIZE"
then
	echo "DB_DOWNLOAD_SIZE variable not set, setting it to 50_000_000"
	export DB_DOWNLOAD_SIZE="50_000_000"
fi

if test -z "$ROOT_PATH"
then
	echo "WARNING: ROOT_PATH variable not set, using temporary path; You can set this variable to save dataset, models, etc in custom path"
fi

echo Using $DOCKER_IMAGE
docker image ls $DOCKER_IMAGE

if $(which nvidia-smi); then
	echo INFO: Running docker image with: $AIRT_GPU_PARAMS
	nvidia-smi -L
	export GPU_PARAMS=$AIRT_GPU_DEVICE
else
	echo INFO: Running docker image without GPU-s
	export GPU_PARAMS=""
fi
