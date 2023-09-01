from docs_src.kafka.base_example.testing import test_base_app
<<<<<<< HEAD
from docs_src.kafka.base_example.testing_chain import test_end_to_end
from faststream.utils.test_utils import working_directory

__all__ = ("test_run_cmd", "test_end_to_end", "test_base_app", )


@pytest.mark.asyncio
async def test_run_cmd():

    with working_directory("docs_src/kafka/base_example"):
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
=======

__all__ = ("test_base_app",)
>>>>>>> 5ea166d92c6cccdad5e550ee0669caa8814a6ed8
