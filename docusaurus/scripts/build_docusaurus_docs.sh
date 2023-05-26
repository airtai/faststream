#!/bin/bash

# exit when any command fails
set -e

echo "Cleanup existing build artifacts"
rm -rf docusaurus/docs

echo "Runing nbdev_mkdocs docs"
mkdir -p mkdocs/docs
cp LICENSE mkdocs/docs/LICENSE.md
cp CONTRIBUTING.md mkdocs/docs
nbdev_mkdocs docs

echo "Copying newly generated markdown files to docusaurus directory"
cp -r mkdocs/docs docusaurus/

echo "Generating API docs"
python3 -c "from fastkafka._docusaurus_helper import fix_invalid_syntax_in_markdown, generate_markdown_docs; fix_invalid_syntax_in_markdown('./docusaurus/docs'); generate_markdown_docs('fastkafka', './docusaurus/docs')"

echo "Generating sidebars.js"
python3 -c "from fastkafka._docusaurus_helper import generate_sidebar; generate_sidebar('./docusaurus/docs/SUMMARY.md', './docusaurus/sidebars.js')"

echo "Deleting the markdown files from the docs directory that are not present in the sidebar."
python3 -c "from fastkafka._docusaurus_helper import delete_unused_markdown_files_from_sidebar; delete_unused_markdown_files_from_sidebar('./docusaurus/docs', './docusaurus/sidebars.js')"


echo "Runing docusaurus build"
cd docusaurus && npm run build

echo "Checking and creating new document version..."
settings_file="../settings.ini"
docs_versioning_flag=$( { grep '^docs_versioning[[:space:]]*=' "$settings_file" || [[ $? == 1 ]]; } | awk -F = '{print $2}' | xargs)

if [ "$docs_versioning_flag" == "minor" ]; then
    echo "Error: minor versioning is not supported when using Docusaurus static site generator. Use patch to create new document version or None to disable document versioning." >&2
    exit 1
fi

if [ -z "$docs_versioning_flag" ]; then
    docs_versioning_flag="None"
fi

if [ "$docs_versioning_flag" != "patch" ] && [ "$docs_versioning_flag" != "None" ]; then
    echo "Error: Invalid value set for 'docs_versioning' in settings.ini file: $docs_versioning_flag. Allowed values are patch or None." >&2
    exit 1
fi

docs_version_file="versions.json"
if [ "$docs_versioning_flag" == "patch" ]; then
    echo "Document versioning is enabled."
    lib_version=$(grep '^version[[:space:]]*=' "$settings_file" | awk -F = '{print $2}' | xargs)
    pat="^[0-9]+([.][0-9]+)*$"
    if [[ $lib_version =~ $pat ]]; then
        if [ -f "$docs_version_file" ]; then
            if grep -q "\"$lib_version\"" "$docs_version_file"; then
                echo "Document version already exists: '$lib_version'"
            else
                npm run docusaurus docs:version $lib_version
            fi
        else
            npm run docusaurus docs:version $lib_version
        fi
    else
        echo "Canary document version updated: '$lib_version'"
    fi
elif [ "$docs_versioning_flag" == "None" ]; then
    echo "Document versioning is disabled."
    if [ -f "$docs_version_file" ]; then
        echo "Deleting previously created document versions."
        rm -rf versioned_docs versioned_sidebars versions.json
        echo "Successfully deleted all previous document versions."
    fi
fi
