import re
from pathlib import Path

import requests
import typer


def get_github_releases():
    # Get the latest version from GitHub releases
    response = requests.get("https://api.github.com/repos/airtai/FastStream/releases")
    return response.json()


def convert_links_and_usernames(text):
    # Convert HTTP/HTTPS links if not already a link
    text = re.sub(r'([^[])(https?://[^\s]+)', r'\1[\2](\2)', text)

    # Convert GitHub usernames to links if not already a link
    text = re.sub(r'([^[])(@\w+)', r'\1[@\2](https://github.com/\2)', text)

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
        f.write(header + "\n" + changelog)
