# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/Logger.ipynb.

# %% auto 0
__all__ = ['should_supress_timestamps', 'logger_spaces_added', 'supress_timestamps', 'get_default_logger_configuration',
           'get_logger', 'set_level', 'true_after']

# %% ../../nbs/Logger.ipynb 2
import logging
import logging.config
from datetime import datetime, timedelta
from typing import *
from .meta import patch

# %% ../../nbs/Logger.ipynb 4
# Logger Levels
# CRITICAL = 50
# ERROR = 40
# WARNING = 30
# INFO = 20
# DEBUG = 10
# NOTSET = 0

should_supress_timestamps: bool = False


def supress_timestamps(flag: bool = True) -> None:
    """Supress logger timestamp

    Args:
        flag: If not set, then the default value **True** will be used to supress the timestamp
            from the logger messages
    """
    global should_supress_timestamps
    should_supress_timestamps = flag


def get_default_logger_configuration(level: int = logging.INFO) -> Dict[str, Any]:
    """Return the common configurations for the logger

    Args:
        level: Logger level to set

    Returns:
        A dict with default logger configuration

    """
    global should_supress_timestamps

    if should_supress_timestamps:
        FORMAT = "[%(levelname)s] %(name)s: %(message)s"
    else:
        FORMAT = "%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s"

    DATE_FMT = "%y-%m-%d %H:%M:%S"

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": FORMAT, "datefmt": DATE_FMT},
        },
        "handlers": {
            "default": {
                "level": level,
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",  # Default is stderr
            },
        },
        "loggers": {
            "": {"handlers": ["default"], "level": level},  # root logger
        },
    }
    return LOGGING_CONFIG

# %% ../../nbs/Logger.ipynb 8
logger_spaces_added: List[str] = []


def get_logger(
    name: str, *, level: int = logging.INFO, add_spaces: bool = True
) -> logging.Logger:
    """Return the logger class with default logging configuration.

    Args:
        name: Pass the __name__ variable as name while calling
        level: Used to configure logging, default value `logging.INFO` logs
            info messages and up.
        add_spaces:

    Returns:
        The logging.Logger class with default/custom logging configuration

    """
    config = get_default_logger_configuration(level=level)
    logging.config.dictConfig(config)

    logger = logging.getLogger(name)
    #     stack_size = len(traceback.extract_stack())
    #     def add_spaces_f(f):
    #         def f_with_spaces(msg, *args, **kwargs):
    #             cur_stack_size = len(traceback.extract_stack())
    #             msg = " "*(cur_stack_size-stack_size)*2 + msg
    #             return f(msg, *args, **kwargs)
    #         return f_with_spaces

    #     if name not in logger_spaces_added and add_spaces:
    #         logger.debug = add_spaces_f(logger.debug) # type: ignore
    #         logger.info = add_spaces_f(logger.info) # type: ignore
    #         logger.warning = add_spaces_f(logger.warning) # type: ignore
    #         logger.error = add_spaces_f(logger.error) # type: ignore
    #         logger.critical = add_spaces_f(logger.critical) # type: ignore
    #         logger.exception = add_spaces_f(logger.exception) # type: ignore

    #         logger_spaces_added.append(name)

    return logger

# %% ../../nbs/Logger.ipynb 14
def set_level(level: int) -> None:
    """Set logger level

    Args:
        level: Logger level to set
    """

    # Getting all loggers that has either airt or __main__ in the name
    loggers = [
        logging.getLogger(name)
        for name in logging.root.manager.loggerDict
        if ("airt" in name) or ("__main__" in name)
    ]

    for logger in loggers:
        logger.setLevel(level)

# %% ../../nbs/Logger.ipynb 18
def true_after(seconds: float) -> Callable[[], bool]:
    """Function returning True after a given number of seconds"""
    t = datetime.now()

    def _true_after(seconds: float = seconds, t: datetime = t) -> bool:
        return (datetime.now() - t) > timedelta(seconds=seconds)

    return _true_after


@patch
def log_and_timeout(self: logging.Logger, msg: str, level: int, timeout: int = 5):
    try:
        self.timeouted_msgs
        pass
    except AttributeError:
        self.timeouted_msgs = {}

    if msg not in self.timeouted_msgs or self.timeouted_msgs[msg]():
        self.timeouted_msgs[msg] = true_after(timeout)

        if level == logging.DEBUG:
            self.debug(msg)
        if level == logging.INFO:
            self.info(msg)
        if level == logging.WARNING:
            self.warning(msg)
        if level == logging.ERROR:
            self.error(msg)
