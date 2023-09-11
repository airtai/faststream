import logging
import re
from pathlib import Path

import typer

logging.basicConfig(level=logging.INFO)


app = typer.Typer()


def read_lines_from_file(file_path, lines_spec):
    with open(file_path, "r") as file:
        all_lines = file.readlines()

    # Check if lines_spec is empty (indicating all lines should be read)
    if not lines_spec:
        return "".join(all_lines)

    selected_lines = []
    line_specs = lines_spec.split(",")

    for line_spec in line_specs:
        if "-" in line_spec:
            # Handle line ranges (e.g., "1-10")
            start, end = map(int, line_spec.split("-"))
            selected_lines.extend(all_lines[start - 1 : end])
        else:
            # Handle single line numbers
            line_number = int(line_spec)
            if 1 <= line_number <= len(all_lines):
                selected_lines.append(all_lines[line_number - 1])

    return "".join(selected_lines)


def extract_lines(embedded_line):
    to_expand_path = re.search("{!>(.*)!}", embedded_line).group(1).strip()
    lines_spec = ""
    if "[ln:" in to_expand_path:
        to_expand_path, lines_spec = to_expand_path.split("[ln:")
        to_expand_path = to_expand_path.strip()
        lines_spec = lines_spec[:-1]

    if Path("./docs/docs_src").exists():
        to_expand_path = Path("./docs") / to_expand_path
    elif Path("./docs_src").exists():
        to_expand_path = Path("./") / to_expand_path
    else:
        raise ValueError(f"Couldn't find docs_src directory")
    return read_lines_from_file(to_expand_path, lines_spec)


@app.command()
def expand_markdown(
    input_markdown_path: Path = typer.Argument(...),
    output_markdown_path: Path = typer.Argument(...),
):
    with open(input_markdown_path, "r") as input_file, open(
        output_markdown_path, "w"
    ) as output_file:
        for line in input_file:
            # Check if the line does not contain the "{!>" pattern
            if "{!>" not in line:
                # Write the line to the output file
                output_file.write(line)
            else:
                output_file.write(extract_lines(embedded_line=line))


def remove_lines_between_dashes(file_path: Path):
    with open(file_path, "r") as file:
        lines = file.readlines()

    start_dash_index = None
    end_dash_index = None
    new_lines = []

    for index, line in enumerate(lines):
        if line.strip() == "---":
            if start_dash_index is None:
                start_dash_index = index
            else:
                end_dash_index = index
                # Remove lines between the two dashes
                new_lines = (
                    lines[:start_dash_index] + new_lines + lines[end_dash_index + 1 :]
                )
                start_dash_index = end_dash_index = None
                break  # NOTE: Remove this line if you have multiple dash chunks

    with open(file_path, "w") as file:
        file.writelines(new_lines)


if __name__ == "__main__":
    app()
