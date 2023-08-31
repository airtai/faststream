import asyncio
import pytest


from docs_src.kafka.base_example.testing import test_base_app
from docs_src.kafka.base_example.testing_chain import test_end_to_end

__all__ = ("test_run_cmd", "test_end_to_end", "test_base_app", )

import os
import contextlib
from pathlib import Path

@contextlib.contextmanager
def working_directory(path):
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


@pytest.mark.asyncio
async def test_run_cmd():

    with working_directory("../../../../docs_src/kafka/base_example"):
        with open("app_run_cmd", "r") as f:
            cmd = "".join(f.readlines())

        proc = await asyncio.create_subprocess_exec(
            *cmd.split(" "),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        await asyncio.sleep(10)

        proc.terminate()

        stdout, stderr = await proc.communicate()
        dstdout = stdout.decode("utf-8")
        dstderr = stderr.decode("utf-8")

        assert "FastStream app starting..." in dstderr
        assert "FastStream app started successfully! To exit press CTRL+C" in dstderr