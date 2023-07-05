#!/bin/bash

# exit when any command fails
set -e

echo "Run nbdev_readme and fix symbol links"
python3 -c "from fastkafka._docusaurus_helper import update_readme; update_readme('.')"