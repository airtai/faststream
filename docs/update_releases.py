import re
from pathlib import Path
from typing import List, Tuple

import requests
import typer


def find_metablock(lines: List[str]) -> Tuple[List[str], List[str]]:
    if lines[0] != "---":
        return [], lines

    index: int = 0
    for i in range(1, len(lines)):
        if lines[i] == "---":
            index = i + 1

    return lines[:index], lines[index:]


def find_header(lines: List[str]) -> Tuple[str, List[str]]:
    for i in range(len(lines)):
        if (line := lines[i]).startswith("#"):
            return line, lines[i+1:]

    return "", lines


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
    changelog = realease_notes_path.read_text()

    metablock, lines = find_metablock(changelog.splitlines())
    metablock = "\n".join(metablock)

    header, changelog = find_header(lines)
    changelog = "\n".join(changelog)

    for release in reversed(releases):
        version = release["tag_name"]
        body = release["body"].replace("##", "###")
        body = convert_links_and_usernames(body)
        version_changelog = f"## {version}\n\n{body}\n\n"

        # Match the latest version in the changelog
        if f"## {version}" not in changelog:
            changelog = version_changelog + changelog

    # Update the RELEASE.md file with the latest version and changelog
    realease_notes_path.write_text((
        metablock + "\n\n" +
        header + "\n" +
        changelog + "\n"
    ).replace("\r", ""))


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    update_release_notes(base_dir / "docs" / "en" / "release.md")
