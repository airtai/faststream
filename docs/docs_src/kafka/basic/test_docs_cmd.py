import asyncio
import json
import yaml
from pathlib import Path

import pytest

from faststream.utils.test_utils import working_directory

root_path = Path(__file__).parent

gen_json_cmd = """
faststream docs gen basic:app
"""

gen_yaml_cmd = """
faststream docs gen --yaml basic:app
"""

serve_cmd = """
faststream docs serve basic:app
"""


@pytest.mark.asyncio
async def test_run_docs_gen_json_cmd(tmp_path, cmd=gen_json_cmd):
    with working_directory(root_path):
        schema_path = tmp_path / "asyncapi.json"
        cmd = cmd.strip()
        cmd = cmd + f" --out {schema_path}"

        proc = await asyncio.create_subprocess_exec(
            *cmd.split(" "),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        await asyncio.sleep(3)
        assert proc.returncode == 0

        with schema_path.open("r") as f:
            schema = json.load(f)

        assert schema


@pytest.mark.asyncio
async def test_run_docs_gen_yaml_cmd(tmp_path, cmd=gen_yaml_cmd):
    with working_directory(root_path):
        schema_path = tmp_path / "asyncapi.yaml"
        cmd = cmd.strip()
        cmd = cmd + f" --out {schema_path}"

        proc = await asyncio.create_subprocess_exec(
            *cmd.split(" "),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        await asyncio.sleep(3)
        assert proc.returncode == 0

        with schema_path.open("r") as f:
            schema = yaml.load(f, Loader=yaml.BaseLoader)

        assert schema


@pytest.mark.asyncio
async def test_run_docs_serve_cmd(cmd=serve_cmd):
    with working_directory(root_path):
        cmd = cmd.strip()
        cmd = cmd + " --port 9999"

        proc = await asyncio.create_subprocess_exec(
            *cmd.split(" "),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        await asyncio.sleep(10)

        proc.terminate()

        stdout, stderr = await proc.communicate()
        stdout.decode("utf-8")
        dstderr = stderr.decode("utf-8")

        assert "Application startup complete" in dstderr
        assert "Uvicorn running on http://localhost:9999 (Press CTRL+C to quit)" in dstderr
