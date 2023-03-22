#!/bin/bash


echo "Looking for setup.py"
test -f setup.py && pip install -e "." || echo "setup.py doesn't exists"
echo "Looking for requirements.txt"
test -f requirements.txt && pip install -r requirements.txt || echo "requirements.txt doesn't exists"
echo "Looking for wheel files"
test -f *.whl && pip install *.whl || echo "wheel files not found"


echo "Installing docs dependencies"
fastkafka docs install_deps
echo "Generating fastkafka docs"
fastkafka docs generate $APP

echo "Starting fastkafka"
# ToDo: Uncomment following line to include --kafka-broker
# fastkafka run --num-workers $NUM_WORKERS --kafka-broker $KAFKA_BROKER $APP
fastkafka run --num-workers $NUM_WORKERS $APP
