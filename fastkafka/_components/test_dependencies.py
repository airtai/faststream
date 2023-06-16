# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/098_Test_Dependencies.ipynb.

# %% auto 0
__all__ = ['logger', 'kafka_version', 'kafka_fname', 'kafka_url', 'local_path', 'tgz_path', 'kafka_path', 'check_java',
           'VersionParser', 'check_kafka', 'generate_app_src', 'generate_app_in_tmp']

# %% ../../nbs/098_Test_Dependencies.ipynb 2
import re
import platform
import shutil
import tarfile
from contextlib import contextmanager
from html.parser import HTMLParser
from os import environ, rename
from os.path import expanduser
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import *

from packaging import version

from .helpers import change_dir, in_notebook
from .logger import get_logger

if in_notebook():
    from tqdm.notebook import tqdm
else:
    from tqdm import tqdm

# %% ../../nbs/098_Test_Dependencies.ipynb 4
logger = get_logger(__name__)

# %% ../../nbs/098_Test_Dependencies.ipynb 6
def check_java(*, potential_jdk_path: Optional[List[Path]] = None) -> bool:
    """Checks if JDK 11 is installed on the machine and exports it to PATH if necessary.

    Args:
        potential_jdk_path: Optional. List of potential paths where JDK 11 may be installed.
                            If not provided, it defaults to searching for JDK 11 in the user's home directory.

    Returns:
        bool: True if JDK 11 is installed and exported to PATH, False otherwise.
    """
    if potential_jdk_path is None:
        potential_jdk_path = list(Path(expanduser("~") + "/.jdk").glob("jdk-11*"))

    if potential_jdk_path != []:
        logger.info("Java is already installed.")
        if not shutil.which("java"):
            logger.info("But not exported to PATH, exporting...")
            env_path_separator = ";" if platform.system() == "Windows" else ":"
            environ["PATH"] = (
                environ["PATH"] + f"{env_path_separator}{potential_jdk_path[0]/ 'bin'}"
            )
        return True
    return False

# %% ../../nbs/098_Test_Dependencies.ipynb 8
def _install_java() -> None:
    """Checks if jdk-11 is installed on the machine and installs it if not

    Returns:
       None

    Raises:
        RuntimeError: If JDK 11 installation fails.
    """
    try:
        import jdk
    except Exception as e:
        msg = "Please install test version of fastkafka using 'pip install fastkafka[test]' command"
        logger.error(msg)
        raise RuntimeError(msg)

    if not check_java():
        logger.info("Installing Java...")
        logger.info(" - installing jdk...")
        jdk_bin_path = Path(jdk.install("11"))
        logger.info(f" - jdk path: {jdk_bin_path}")
        env_path_separator = ";" if platform.system() == "Windows" else ":"
        environ["PATH"] = (
            environ["PATH"] + f"{env_path_separator}{jdk_bin_path / 'bin'}"
        )
        logger.info("Java installed.")

# %% ../../nbs/098_Test_Dependencies.ipynb 10
class VersionParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.newest_version = "0.0.0"

    def handle_data(self, data):
        match = re.search("[0-9]+\.[0-9]+\.[0-9]+", data)
        if match is not None:
            if version.parse(self.newest_version) < version.parse(match.group(0)):
                self.newest_version = match.group(0)

# %% ../../nbs/098_Test_Dependencies.ipynb 13
# ToDo: move it somewhere
kafka_version = resolve_kafka_version()
kafka_fname = f"kafka_2.13-{kafka_version}"
kafka_url = f"https://dlcdn.apache.org/kafka/{kafka_version}/{kafka_fname}.tgz"
local_path = (
    Path(expanduser("~")).parent / "Public"
    if platform.system() == "Windows"
    else Path(expanduser("~")) / ".local"
)
tgz_path = local_path / f"{kafka_fname}.tgz"
kafka_path = (
    local_path / "kafka"
    if platform.system() == "Windows"
    else local_path / f"{kafka_fname}"
)


def check_kafka(kafka_path: Path = kafka_path) -> bool:
    """Checks if Kafka is installed on the machine and exports it to PATH if necessary.

    Args:
        kafka_path: Path to the Kafka installation directory. Defaults to the global variable `kafka_path`.

    Returns:
        bool: True if Kafka is installed and exported to PATH, False otherwise.
    """
    if (kafka_path / "bin").exists():
        logger.info("Kafka is installed.")
        if not shutil.which("kafka-server-start.sh"):
            logger.info("But not exported to PATH, exporting...")
            kafka_binary_path = (
                f";{kafka_path / 'bin' / 'windows'}"
                if platform.system() == "Windows"
                else f":{kafka_path / 'bin'}"
            )
            environ["PATH"] = environ["PATH"] + kafka_binary_path
        return True
    return False

# %% ../../nbs/098_Test_Dependencies.ipynb 14
def _install_kafka(
    *,
    kafka_url: str = kafka_url,
    local_path: Path = local_path,
    tgz_path: Path = tgz_path,
    kafka_path: Path = kafka_path,
) -> None:
    """Checks if Kafka is installed on the machine and installs it if not.

    Args:
        kafka_url: URL to download the Kafka installation package. Defaults to the global variable `kafka_url`.
        local_path: Path where the Kafka installation package will be stored. Defaults to the global variable `local_path`.
        tgz_path: Path where the Kafka installation package will be extracted. Defaults to the global variable `tgz_path`.
        kafka_path: Path where Kafka will be installed. Defaults to the global variable `kafka_path`.

    Returns:
       None

    Raises:
        RuntimeError: If Kafka installation fails.
    """
    try:
        import requests
    except Exception as e:
        msg = "Please install test version of fastkafka using 'pip install fastkafka[test]' command"
        logger.error(msg)
        raise RuntimeError(msg)

    if not check_kafka():
        logger.info("Installing Kafka...")
        local_path.mkdir(exist_ok=True, parents=True)
        response = requests.get(
            kafka_url,
            stream=True,
            timeout=60,
        )
        try:
            total = response.raw.length_remaining // 128
        except Exception:
            total = None

        with open(tgz_path, "wb") as f:
            for data in tqdm(response.iter_content(chunk_size=128), total=total):
                f.write(data)

        with tarfile.open(tgz_path) as tar:
            for tarinfo in tar:
                tar.extract(tarinfo, local_path)

        if platform.system() == "Windows":
            rename(local_path / f"{kafka_fname}", kafka_path)

        kafka_binary_path = (
            f";{kafka_path / 'bin' / 'windows'}"
            if platform.system() == "Windows"
            else f":{kafka_path / 'bin'}"
        )
        environ["PATH"] = environ["PATH"] + kafka_binary_path
        logger.info(f"Kafka installed in {kafka_path}.")

# %% ../../nbs/098_Test_Dependencies.ipynb 16
def _install_testing_deps() -> None:
    """Installs Java and Kafka dependencies required for testing.

    Raises:
        RuntimeError: If Java or Kafka installation fails.
    """
    _install_java()
    _install_kafka()

# %% ../../nbs/098_Test_Dependencies.ipynb 18
def generate_app_src(out_path: Union[Path, str]) -> None:
    """Generates the source code for the test application based on a Jupyter notebook.

    Args:
        out_path: Path where the generated source code will be saved.

    Raises:
        ValueError: If the Jupyter notebook file does not exist.
    """
    import nbformat
    from nbconvert import PythonExporter

    path = Path("099_Test_Service.ipynb")
    if not path.exists():
        path = Path("..") / "099_Test_Service.ipynb"
    if not path.exists():
        raise ValueError(f"Path '{path.resolve()}' does not exists.")

    with open(path, "r") as f:
        notebook = nbformat.reads(f.read(), nbformat.NO_CONVERT)
        exporter = PythonExporter()
        source, _ = exporter.from_notebook_node(notebook)

    with open(out_path, "w") as f:
        f.write(source)

# %% ../../nbs/098_Test_Dependencies.ipynb 20
@contextmanager
def generate_app_in_tmp() -> Generator[str, None, None]:
    """Context manager that generates the test application source code in a temporary directory.

    Yields:
        str: Import statement for the generated test application.
    """
    with TemporaryDirectory() as d:
        src_path = Path(d) / "main.py"
        generate_app_src(src_path)
        with change_dir(d):
            import_str = f"{src_path.stem}:kafka_app"
            yield import_str
