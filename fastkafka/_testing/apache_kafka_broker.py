# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/002_ApacheKafkaBroker.ipynb.

# %% auto 0
__all__ = ['logger', 'T', 'get_zookeeper_config_string', 'get_kafka_config_string', 'ApacheKafkaBroker', 'run_and_match',
           'is_port_in_use', 'get_free_port', 'write_config_and_run', 'start_apache_kafka_brokers']

# %% ../../nbs/002_ApacheKafkaBroker.ipynb 1
import asyncio
import re
import platform
import socket
import subprocess  # nosec
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import *

import asyncer
import nest_asyncio

from .._components._subprocess import terminate_asyncio_process
from .._components.helpers import in_notebook
from .._components.logger import get_logger
from .._components.meta import delegates, export, filter_using_signature, patch
from .._components.test_dependencies import check_java, check_kafka

# %% ../../nbs/002_ApacheKafkaBroker.ipynb 3
if in_notebook():
    from tqdm.notebook import tqdm
else:
    from tqdm import tqdm

# %% ../../nbs/002_ApacheKafkaBroker.ipynb 4
logger = get_logger(__name__)

# %% ../../nbs/002_ApacheKafkaBroker.ipynb 8
def get_zookeeper_config_string(
    data_dir: Union[str, Path],  # the directory where the snapshot is stored.
    zookeeper_port: int = 2181,  # the port at which the clients will connect
) -> str:
    """Generates a zookeeeper configuration string that can be exported to file
    and used to start a zookeeper instance.

    Args:
        data_dir: Path to the directory where the zookeepeer instance will save data
        zookeeper_port: Port for clients (Kafka brokes) to connect
    Returns:
        Zookeeper configuration string.

    """
    zookeeper_data_dir = str((Path(data_dir) / "zookeeper").resolve())
    if platform.system() == "Windows":
        zookeeper_data_dir = zookeeper_data_dir.replace("\\", "/")
    zookeeper_config = f"""dataDir={zookeeper_data_dir}
clientPort={zookeeper_port}
maxClientCnxns=0
admin.enableServer=false
"""

    return zookeeper_config

# %% ../../nbs/002_ApacheKafkaBroker.ipynb 10
def get_kafka_config_string(
    data_dir: Union[str, Path], zookeeper_port: int = 2181, listener_port: int = 9092
) -> str:
    """Generates a kafka broker configuration string that can be exported to file
    and used to start a kafka broker instance.

    Args:
        data_dir: Path to the directory where the kafka broker instance will save data
        zookeeper_port: Port on which the zookeeper instance is running
        listener_port: Port on which the clients (producers and consumers) can connect
    Returns:
        Kafka broker configuration string.

    """
    kafka_logs_dir = str((Path(data_dir) / "kafka_logs").resolve())
    if platform.system() == "Windows":
        kafka_logs_dir = kafka_logs_dir.replace("\\", "/")
    kafka_config = f"""broker.id=0

############################# Socket Server Settings #############################

# The address the socket server listens on. If not configured, the host name will be equal to the value of
# java.net.InetAddress.getCanonicalHostName(), with PLAINTEXT listener name, and port 9092.
#   FORMAT:
#     listeners = listener_name://host_name:port
#   EXAMPLE:
#     listeners = PLAINTEXT://your.host.name:9092
listeners=PLAINTEXT://:{listener_port}

# Listener name, hostname and port the broker will advertise to clients.
# If not set, it uses the value for "listeners".
# advertised.listeners=PLAINTEXT://localhost:{listener_port}

# Maps listener names to security protocols, the default is for them to be the same. See the config documentation for more details
#listener.security.protocol.map=PLAINTEXT:PLAINTEXT,SSL:SSL,SASL_PLAINTEXT:SASL_PLAINTEXT,SASL_SSL:SASL_SSL

# The number of threads that the server uses for receiving requests from the network and sending responses to the network
num.network.threads=3

# The number of threads that the server uses for processing requests, which may include disk I/O
num.io.threads=8

# The send buffer (SO_SNDBUF) used by the socket server
socket.send.buffer.bytes=102400

# The receive buffer (SO_RCVBUF) used by the socket server
socket.receive.buffer.bytes=102400

# The maximum size of a request that the socket server will accept (protection against OOM)
socket.request.max.bytes=104857600


############################# Log Basics #############################

# A comma separated list of directories under which to store log files
log.dirs={kafka_logs_dir}

# The default number of log partitions per topic. More partitions allow greater
# parallelism for consumption, but this will also result in more files across
# the brokers.
num.partitions=1

# The number of threads per data directory to be used for log recovery at startup and flushing at shutdown.
# This value is recommended to be increased for installations with data dirs located in RAID array.
num.recovery.threads.per.data.dir=1

offsets.topic.replication.factor=1
transaction.state.log.replication.factor=1
transaction.state.log.min.isr=1

# The number of messages to accept before forcing a flush of data to disk
log.flush.interval.messages=10000

# The maximum amount of time a message can sit in a log before we force a flush
log.flush.interval.ms=1000

# The minimum age of a log file to be eligible for deletion due to age
log.retention.hours=168

# A size-based retention policy for logs. Segments are pruned from the log unless the remaining
# segments drop below log.retention.bytes. Functions independently of log.retention.hours.
log.retention.bytes=1073741824

# The maximum size of a log segment file. When this size is reached a new log segment will be created.
log.segment.bytes=1073741824

# The interval at which log segments are checked to see if they can be deleted according to the retention policies
log.retention.check.interval.ms=300000

# Zookeeper connection string (see zookeeper docs for details).
zookeeper.connect=localhost:{zookeeper_port}

# Timeout in ms for connecting to zookeeper
zookeeper.connection.timeout.ms=18000

# The following configuration specifies the time, in milliseconds, that the GroupCoordinator will delay the initial consumer rebalance.
group.initial.rebalance.delay.ms=0
"""

    return kafka_config

# %% ../../nbs/002_ApacheKafkaBroker.ipynb 12
@export("fastkafka.testing")
class ApacheKafkaBroker:
    """ApacheKafkaBroker class, used for running unique kafka brokers in tests to prevent topic clashing."""

    @delegates(get_kafka_config_string, but=["data_dir"])
    @delegates(get_zookeeper_config_string, keep=True, but=["data_dir"])
    def __init__(
        self,
        topics: Iterable[str] = [],
        *,
        retries: int = 3,
        apply_nest_asyncio: bool = False,
        **kwargs: Dict[str, Any],
    ):
        """Initialises the ApacheKafkaBroker object

        Args:
            topics: List of topics to create after sucessfull Kafka broker startup
            retries: Number of retries to create kafka and zookeeper services using random
            apply_nest_asyncio: set to True if running in notebook
            zookeeper_port: Port for clients (Kafka brokes) to connect
            listener_port: Port on which the clients (producers and consumers) can connect
        """
        self.zookeeper_kwargs = filter_using_signature(
            get_zookeeper_config_string, **kwargs
        )
        self.kafka_kwargs = filter_using_signature(get_kafka_config_string, **kwargs)

        if "zookeeper_port" not in self.zookeeper_kwargs:
            self.zookeeper_kwargs["zookeeper_port"] = 2181
            self.kafka_kwargs["zookeeper_port"] = 2181

        if "listener_port" not in self.kafka_kwargs:
            self.kafka_kwargs["listener_port"] = 9092

        self.retries = retries
        self.apply_nest_asyncio = apply_nest_asyncio
        self.temporary_directory: Optional[TemporaryDirectory] = None
        self.temporary_directory_path: Optional[Path] = None
        self.kafka_task: Optional[asyncio.subprocess.Process] = None
        self.zookeeper_task: Optional[asyncio.subprocess.Process] = None
        self._is_started = False
        self.topics: Iterable[str] = topics

    @property
    def is_started(self) -> bool:
        """Property indicating whether the ApacheKafkaBroker object is started.

        The is_started property indicates if the ApacheKafkaBroker object is currently
        in a started state. This implies that Zookeeper and Kafka broker processes have
        sucesfully started and are ready for handling events.

        Returns:
            bool: True if the object is started, False otherwise.
        """
        return self._is_started

    @classmethod
    def _check_deps(cls) -> None:
        """Prepares the environment for running Kafka brokers.
        Returns:
           None
        """
        raise NotImplementedError

    async def _start(self) -> str:
        """Starts a local kafka broker and zookeeper instance asynchronously
        Returns:
           Kafka broker bootstrap server address in string format: add:port
        """
        raise NotImplementedError

    def start(self) -> str:
        """Starts a local kafka broker and zookeeper instance synchronously
        Returns:
           Kafka broker bootstrap server address in string format: add:port
        """
        raise NotImplementedError

    def stop(self) -> None:
        """Stops a local kafka broker and zookeeper instance synchronously
        Returns:
           None
        """
        raise NotImplementedError

    async def _stop(self) -> None:
        """Stops a local kafka broker and zookeeper instance synchronously
        Returns:
           None
        """
        raise NotImplementedError

    def get_service_config_string(self, service: str, *, data_dir: Path) -> str:
        """Generates a configuration for a service
        Args:
            data_dir: Path to the directory where the zookeepeer instance will save data
            service: "kafka" or "zookeeper", defines which service to get config string for
        """
        raise NotImplementedError

    async def _start_service(self, service: str = "kafka") -> None:
        """Starts the service according to defined service var
        Args:
            service: "kafka" or "zookeeper", defines which service to start
        """
        raise NotImplementedError

    async def _start_zookeeper(self) -> None:
        """Start a local zookeeper instance
        Returns:
           None
        """
        raise NotImplementedError

    async def _start_kafka(self) -> None:
        """Start a local kafka broker
        Returns:
           None
        """
        raise NotImplementedError

    async def _create_topics(self) -> None:
        """Create missing topics in local Kafka broker
        Returns:
           None
        """
        raise NotImplementedError

    def __enter__(self) -> str:
        #         ApacheKafkaBroker._check_deps()
        return self.start()

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        self.stop()

    async def __aenter__(self) -> str:
        #         ApacheKafkaBroker._check_deps()
        return await self._start()

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self._stop()

# %% ../../nbs/002_ApacheKafkaBroker.ipynb 14
@patch(cls_method=True)  # type: ignore
def _check_deps(cls: ApacheKafkaBroker) -> None:
    """Checks the dependencies required to run Apache KafkaBroker.

    Raises:
        RuntimeError: If JDK installation or Kafka installation is not found.
    """
    if not check_java():
        raise RuntimeError(
            "JDK installation not found! Please install JDK manually or run 'fastkafka testing install_deps'."
        )
    if not check_kafka():
        raise RuntimeError(
            "Kafka installation not found! Please install Kafka tools manually or run 'fastkafka testing install_deps'."
        )

# %% ../../nbs/002_ApacheKafkaBroker.ipynb 17
async def run_and_match(
    *args: str,
    capture: str = "stdout",
    timeout: int = 5,
    pattern: str,
    num_to_match: int = 1,
) -> asyncio.subprocess.Process:
    """Runs a command asynchronously and matches the output against a pattern.

    Args:
        *args: Command-line arguments for the subprocess.
        capture: Which output to capture ("stdout" or "stderr").
        timeout: Timeout in seconds for reading the output.
        pattern: Regular expression pattern to match in the output.
        num_to_match: Number of matches to wait for.

    Returns:
        The subprocess process object.

    Raises:
        ValueError: If the capture parameter has an unsupported value.
        TimeoutError: If the process times out.
        RuntimeError: If the process returns a non-zero return code.
    """
    # Create the subprocess; redirect the standard output
    # into a pipe.
    matched = 0

    if platform.system() == "Windows":
        proc = await asyncio.create_subprocess_shell(
            " ".join(args),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,  # type: ignore
        )
    else:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    # Read one line of output.
    t = datetime.now()
    while datetime.now() - t < timedelta(seconds=timeout):
        try:
            if capture == "stdout":
                data = await asyncio.wait_for(proc.stdout.readline(), timeout=1.0)  # type: ignore
            elif capture == "stderr":
                data = await asyncio.wait_for(proc.stderr.readline(), timeout=1.0)  # type: ignore
            else:
                raise ValueError(
                    f"Unknown capture param value {capture}, supported values are 'stdout', 'stderr'"
                )
            ddata = data.decode("utf-8")

            if len(re.findall(pattern, ddata)) > 0:
                # print(f"Matched: {ddata}")
                matched += 1
                if matched == num_to_match:
                    return proc
        except asyncio.exceptions.TimeoutError as e:
            pass

        if proc.returncode is not None:
            stdout, stderr = await proc.communicate()
            dstdout = stdout.decode("utf-8")
            dstderr = stderr.decode("utf-8")
            if proc.returncode == 0:
                raise TimeoutError(
                    f"stdout={dstdout}, stderr={dstderr}, returncode={proc.returncode}"
                )
            else:
                raise RuntimeError(
                    f"stdout={dstdout}, stderr={dstderr}, returncode={proc.returncode}"
                )

    await terminate_asyncio_process(proc)

    raise TimeoutError()

# %% ../../nbs/002_ApacheKafkaBroker.ipynb 20
def is_port_in_use(port: Union[int, str]) -> bool:
    """
    Checks if a port is already in use.

    Args:
        port (Union[int, str]): The port number to check. It can be provided as an integer or a string.

    Returns:
        bool: True if the port is in use, False otherwise.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", int(port))) == 0

# %% ../../nbs/002_ApacheKafkaBroker.ipynb 22
def get_free_port() -> str:
    """Gets a port number which is available and free in the system.

    Returns:
        The free port number as a string.
    """
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = str(s.getsockname()[1])
    s.close()
    return port


async def write_config_and_run(
    config: str, config_path: Union[str, Path], run_cmd: str
) -> asyncio.subprocess.Process:
    """Writes the configuration to a file, and runs a command using the configuration.

    Args:
        config: The configuration string.
        config_path: Path to the configuration file.
        run_cmd: The command to run.

    Returns:
        The subprocess process object.
    """
    with open(config_path, "w") as f:
        f.write(config)

    return await asyncio.create_subprocess_exec(
        run_cmd,
        config_path,
        stdout=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE,
    )


@patch
def get_service_config_string(
    self: ApacheKafkaBroker, service: str, *, data_dir: Path
) -> str:
    """Gets the configuration string for a service.

    Args:
        service: Name of the service ("kafka" or "zookeeper").
        data_dir: Path to the directory where the service will save data.

    Returns:
        The service configuration string.
    """
    service_kwargs = getattr(self, f"{service}_kwargs")
    if service == "kafka":
        return get_kafka_config_string(data_dir=data_dir, **service_kwargs)
    else:
        return get_zookeeper_config_string(data_dir=data_dir, **service_kwargs)


@patch
async def _start_service(self: ApacheKafkaBroker, service: str = "kafka") -> None:
    """Starts a service (kafka or zookeeper) asynchronously.

    Args:
        service: Name of the service ("kafka" or "zookeeper").
    """
    logger.info(f"Starting {service}...")

    if self.temporary_directory_path is None:
        raise ValueError(
            "ApacheKafkaBroker._start_service(): self.temporary_directory_path is None, did you initialise it?"
        )

    configs_tried: List[Dict[str, Any]] = []

    for i in range(self.retries + 1):
        configs_tried = configs_tried + [getattr(self, f"{service}_kwargs").copy()]

        service_config_path = self.temporary_directory_path / f"{service}.properties"

        with open(service_config_path, "w") as f:
            f.write(
                self.get_service_config_string(
                    service, data_dir=self.temporary_directory_path
                )
            )

        try:
            port = (
                self.zookeeper_kwargs["zookeeper_port"]
                if service == "zookeeper"
                else self.kafka_kwargs["listener_port"]
            )
            if is_port_in_use(port):
                raise ValueError(f"Port {port} is already in use")

            script_extension = "bat" if platform.system() == "Windows" else "sh"
            service_start_script = f"{service}-server-start.{script_extension}"
            service_task = await run_and_match(
                service_start_script,
                str(service_config_path),
                pattern="Recorded new controller, from now on will use node"
                if service == "kafka"
                else "INFO Snapshot taken",
                timeout=30,
            )
        except Exception as e:
            print(e)
            logger.info(
                f"{service} startup failed, generating a new port and retrying..."
            )
            port = get_free_port()
            if service == "zookeeper":
                self.zookeeper_kwargs["zookeeper_port"] = port
                self.kafka_kwargs["zookeeper_port"] = port
            else:
                self.kafka_kwargs["listener_port"] = port

            logger.info(f"{service} new port={port}")
        else:
            setattr(self, f"{service}_task", service_task)
            return

    raise ValueError(f"Could not start {service} with params: {configs_tried}")


@patch
async def _start_kafka(self: ApacheKafkaBroker) -> None:
    """Starts a local Kafka broker asynchronously."""
    return await self._start_service("kafka")


@patch
async def _start_zookeeper(self: ApacheKafkaBroker) -> None:
    """Starts a local ZooKeeper instance asynchronously."""
    return await self._start_service("zookeeper")


@patch
async def _create_topics(self: ApacheKafkaBroker) -> None:
    """Creates missing topics in a local Kafka broker asynchronously."""
    listener_port = self.kafka_kwargs.get("listener_port", 9092)
    bootstrap_server = f"127.0.0.1:{listener_port}"

    script_extension = "bat" if platform.system() == "Windows" else "sh"
    topics_script = f"kafka-topics.{script_extension}"
    async with asyncer.create_task_group() as tg:
        processes = [
            tg.soonify(asyncio.create_subprocess_exec)(
                topics_script,
                "--create",
                f"--topic={topic}",
                f"--bootstrap-server={bootstrap_server}",
                stdout=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
            )
            for topic in self.topics
        ]

    try:
        return_values = [
            await asyncio.wait_for(process.value.wait(), 30) for process in processes
        ]
        if any(return_value != 0 for return_value in return_values):
            raise ValueError("Could not create missing topics!")
    except asyncio.TimeoutError as _:
        raise ValueError("Timed out while creating missing topics!")


@patch
async def _start(self: ApacheKafkaBroker) -> str:
    """Starts a local Kafka broker and ZooKeeper instance asynchronously.

    Returns:
        The Kafka broker bootstrap server address in string format: host:port.
    """
    self._check_deps()

    self.temporary_directory = TemporaryDirectory()
    self.temporary_directory_path = Path(self.temporary_directory.__enter__())

    await self._start_zookeeper()
    await self._start_kafka()

    listener_port = self.kafka_kwargs.get("listener_port", 9092)
    bootstrap_server = f"127.0.0.1:{listener_port}"
    logger.info(f"Local Kafka broker up and running on {bootstrap_server}")

    await self._create_topics()

    self._is_started = True

    return bootstrap_server


@patch
async def _stop(self: ApacheKafkaBroker) -> None:
    """Stops a local Kafka broker and ZooKeeper instance asynchronously."""
    await terminate_asyncio_process(self.kafka_task)  # type: ignore
    await terminate_asyncio_process(self.zookeeper_task)  # type: ignore
    self.temporary_directory.__exit__(None, None, None)  # type: ignore
    self._is_started = False

# %% ../../nbs/002_ApacheKafkaBroker.ipynb 25
@patch
def start(self: ApacheKafkaBroker) -> str:
    """Starts a local Kafka broker and ZooKeeper instance synchronously.

    Returns:
        The Kafka broker bootstrap server address in string format: host:port.
    """
    logger.info(f"{self.__class__.__name__}.start(): entering...")
    try:
        # get or create loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError as e:
            logger.warning(
                f"{self.__class__.__name__}.start(): RuntimeError raised when calling asyncio.get_event_loop(): {e}"
            )
            logger.warning(
                f"{self.__class__.__name__}.start(): asyncio.new_event_loop()"
            )
            loop = asyncio.new_event_loop()

        # start zookeeper and kafka broker in the loop

        if loop.is_running():
            if self.apply_nest_asyncio:
                logger.warning(
                    f"{self.__class__.__name__}.start(): ({loop}) is already running!"
                )
                logger.warning(
                    f"{self.__class__.__name__}.start(): calling nest_asyncio.apply()"
                )
                nest_asyncio.apply(loop)
            else:
                msg = f"{self.__class__.__name__}.start(): ({loop}) is already running! Use 'apply_nest_asyncio=True' when creating 'ApacheKafkaBroker' to prevent this."
                logger.error(msg)
                raise RuntimeError(msg)

        retval = loop.run_until_complete(self._start())
        logger.info(f"{self.__class__}.start(): returning {retval}")
        return retval
    finally:
        logger.info(f"{self.__class__.__name__}.start(): exited.")


@patch
def stop(self: ApacheKafkaBroker) -> None:
    """Stops a local kafka broker and zookeeper instance synchronously
    Returns:
       None
    """
    logger.info(f"{self.__class__.__name__}.stop(): entering...")
    try:
        if not self._is_started:
            raise RuntimeError(
                "ApacheKafkaBroker not started yet, please call ApacheKafkaBroker.start() before!"
            )

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._stop())
    finally:
        logger.info(f"{self.__class__.__name__}.stop(): exited.")

# %% ../../nbs/002_ApacheKafkaBroker.ipynb 30
async def _start_broker(broker: Any) -> Union[Any, Exception]:
    try:
        await broker._start()
        return broker
    except Exception as e:
        return e


async def _stop_broker(broker: Any) -> Union[Any, Exception]:
    try:
        await broker._stop()
        return broker
    except Exception as e:
        return e


async def _get_unique_local_brokers_to_start(
    kafka_brokers_name: str,
    kafka_brokers: List[Dict[str, Dict[str, Any]]],
    duplicate_ok: bool = False,
    zookeeper_ports: List[int] = [2181],
    ignore_nonlocal_brokers: bool = False,
) -> List[Tuple[str, int]]:
    brokers_to_start = [
        x[kafka_brokers_name] for x in kafka_brokers if kafka_brokers_name in x
    ]
    unique_brokers_to_start = set([(x["url"], x["port"]) for x in brokers_to_start])

    if len(unique_brokers_to_start) < len(brokers_to_start) and not duplicate_ok:
        raise ValueError(
            f"Duplicate kafka_brokers are found - {brokers_to_start}. Please change values or use 'duplicate_ok=True'"
        )

    unique_urls = set([x[0] for x in unique_brokers_to_start])
    localhost_urls = set(
        [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",  # nosec: B104 - Possible binding to all interfaces
        ]
    )
    if not unique_urls.issubset(localhost_urls) and not ignore_nonlocal_brokers:
        raise ValueError(
            f"URL values other than {', '.join(sorted(localhost_urls))} are found - {unique_urls - localhost_urls}. Please change values or use 'ignore_nonlocal_brokers=True'"
        )

    unique_local_brokers_to_start = [
        x for x in unique_brokers_to_start if x[0] in localhost_urls
    ]
    return unique_local_brokers_to_start

# %% ../../nbs/002_ApacheKafkaBroker.ipynb 31
T = TypeVar("T")


@asynccontextmanager
async def _start_and_stop_brokers(brokers: List[T]) -> AsyncIterator[None]:
    try:
        retvals = [await _start_broker(broker) for broker in brokers]
        exceptions = [x for x in retvals if isinstance(x, Exception)]

        if exceptions:
            raise RuntimeError(exceptions)

        yield
    finally:
        retvals = [
            await _stop_broker(broker)
            for broker in retvals
            if not isinstance(broker, Exception)
        ]
        exceptions = [x for x in retvals if isinstance(x, Exception)]

        if exceptions:
            raise RuntimeError(exceptions)


@asynccontextmanager
async def start_apache_kafka_brokers(
    kafka_brokers_name: str,
    kafka_brokers: List[Dict[str, Dict[str, Any]]],
    duplicate_ok: bool = False,
    zookeeper_ports: List[int] = [2181],
    ignore_nonlocal_brokers: bool = False,
) -> AsyncIterator[None]:
    unique_local_brokers_to_start = await _get_unique_local_brokers_to_start(
        kafka_brokers_name=kafka_brokers_name,
        kafka_brokers=kafka_brokers,
        duplicate_ok=duplicate_ok,
        ignore_nonlocal_brokers=ignore_nonlocal_brokers,
    )

    if len(zookeeper_ports) < len(unique_local_brokers_to_start):
        raise ValueError(
            f"Atleast {len(unique_local_brokers_to_start)} zookeeper ports are needed to start kafka. Current zookeeper_ports length is {len(zookeeper_ports)}"
        )

    brokers = [
        ApacheKafkaBroker(listener_port=broker[1], zookeeper_port=zookeeper_port)  # type: ignore
        for broker, zookeeper_port in zip(
            unique_local_brokers_to_start, zookeeper_ports
        )
    ]

    async with _start_and_stop_brokers(brokers=brokers):
        yield
