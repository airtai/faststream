import re
from pathlib import Path

import requests
import typer


def get_github_releases():
    # Get the latest version from GitHub releases
    response = requests.get("https://api.github.com/repos/airtai/FastStream/releases")
    return response.json()


def convert_links_and_usernames(text):
    if "](" not in text:
        # Convert HTTP/HTTPS links
        text = re.sub(r'(https?://[^\s]+)', r'[\1](\1){.external-link target="_blank"}', text)

        # Convert GitHub usernames to links
        text = re.sub(r'@(\w+)', r'[@\1](https://github.com/\1){.external-link target="_blank"}', text)

    return text


def update_release_notes(realease_notes_path: Path):
    typer.echo("Updating Release Notes")
    releases = get_github_releases()

    # Get the changelog from the RELEASE.md file
    with open(realease_notes_path, "r") as f:
        changelog = f.read()

    lines = changelog.splitlines()
    header, changelog = "\n".join(lines[0:8]), "\n".join(lines[8:])

    for release in reversed(releases):
        version = release["tag_name"]
        body = release["body"].replace("##", "###")
        body = convert_links_and_usernames(body)
        version_changelog = f"## {version}\n\n{body}\n\n"

        # Match the latest version in the changelog
        if f"## {version}" not in changelog:
            changelog = version_changelog + changelog

    # Update the RELEASE.md file with the latest version and changelog
    with open(realease_notes_path, "w") as f:
        release_notes = (header + "\n" + changelog).replace('\r','')
        f.write(release_notes)
