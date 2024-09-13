import logging

import pytest

from faststream import FastStream
from faststream._internal.cli.utils.logs import LogLevels, get_log_level, set_log_level
from faststream.rabbit import RabbitBroker


@pytest.mark.parametrize(
    "level",
    (  # noqa: PT007
        pytest.param(logging.ERROR, id=str(logging.ERROR)),
        *(pytest.param(level, id=level) for level in LogLevels.__members__),
        *(
            pytest.param(level, id=str(level))
            for level in LogLevels.__members__.values()
        ),
    ),
)
def test_set_level(level, app: FastStream):
    level = get_log_level(level)
    set_log_level(level, app)
    assert app.logger.level is app.broker.logger.level is level


@pytest.mark.parametrize(
    ("level", "broker"),
    (  # noqa: PT007
        pytest.param(
            logging.CRITICAL,
            FastStream(),
            id="empty app",
        ),
        pytest.param(
            logging.CRITICAL,
            FastStream(RabbitBroker(), logger=None),
            id="app without logger",
        ),
        pytest.param(
            logging.CRITICAL,
            FastStream(RabbitBroker(logger=None)),
            id="broker without logger",
        ),
        pytest.param(
            logging.CRITICAL,
            FastStream(RabbitBroker(logger=None), logger=None),
            id="both without logger",
        ),
    ),
)
def test_set_level_to_none(level, app: FastStream):
    set_log_level(get_log_level(level), app)


def test_set_default():
    app = FastStream()
    level = "wrong_level"
    set_log_level(get_log_level(level), app)
    assert app.logger.level is logging.INFO
