from typing import TYPE_CHECKING, Any, List, Tuple

from faststream.cli.supervisors.basereload import BaseReload
from faststream.log import logger

if TYPE_CHECKING:
    from multiprocessing.context import SpawnProcess

    from faststream.types import DecoratedCallable


class Multiprocess(BaseReload):
    """A class to represent a multiprocess."""

    def __init__(
        self,
        target: "DecoratedCallable",
        args: Tuple[Any, ...],
        workers: int,
    ) -> None:
        super().__init__(target, args, None)

        self.workers = workers
        self.processes: List["SpawnProcess"] = []

    def startup(self) -> None:
        logger.info(f"Started parent process [{self.pid}]")

        for _ in range(self.workers):
            process = self._start_process()
            logger.info(f"Started child process [{process.pid}]")
            self.processes.append(process)

    def shutdown(self) -> None:
        for process in self.processes:
            process.terminate()
            logger.info(f"Stopping child process [{process.pid}]")
            process.join()

        logger.info(f"Stopping parent process [{self.pid}]")
