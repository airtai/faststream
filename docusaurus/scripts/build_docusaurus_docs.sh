#!/bin/bash

# exit when any command fails
set -e

echo "Cleanup existing build artifacts"
rm -rf docusaurus/docs

echo "Run nbdev_mkdocs docs"
nbdev_mkdocs docs

echo "Copy newly generated markdown files to docusaurus directory"
cp -r mkdocs/docs docusaurus/

echo "Generate API docs"
build_markdown_docs

echo "Run docusaurus build"
cd docusaurus && npm run build

