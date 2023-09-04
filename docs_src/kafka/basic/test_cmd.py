import asyncio
from  pathlib import Path

import pytest

from faststream.utils.test_utils import working_directory

root_path = Path(__file__).parent

cmd ="""
faststream run basic:app
"""

@pytest.mark.asyncio
async def test_run_cmd(cmd=cmd):
    with working_directory(root_path):
        cmd = cmd.strip()

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

        assert "FastStream app starting..." in dstderr
        assert "FastStream app started successfully! To exit press CTRL+C" in dstderr
