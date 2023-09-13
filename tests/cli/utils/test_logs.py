import logging
from itertools import zip_longest

import pytest

from faststream import FastStream
from faststream.cli.utils.logs import LogLevels, get_log_level, set_log_level
from faststream.rabbit import RabbitBroker


@pytest.mark.parametrize(
    "level,broker",
    tuple(
        zip_longest(
            (
                logging.ERROR,
                *LogLevels._member_map_.values(),
                *LogLevels.__members__.values(),
            ),
            [],
            fillvalue=FastStream(RabbitBroker()),
        )
    ),
)
def test_set_level(level, app: FastStream):
    level = get_log_level(level)

    set_log_level(level, app)
    assert app.logger.level is app.broker.logger.level is level


@pytest.mark.parametrize(
    "level,broker",
    tuple(
        zip_longest(
            [],
            (
                FastStream(),
                FastStream(RabbitBroker(), logger=None),
                FastStream(RabbitBroker(logger=None)),
                FastStream(RabbitBroker(logger=None), logger=None),
            ),
            fillvalue=LogLevels.critical,
        )
    ),
)
def test_set_level_to_none(level, app: FastStream):
    set_log_level(get_log_level(level), app)


def test_set_default():
    app = FastStream()
    level = "wrong_level"
    set_log_level(get_log_level(level), app)
    assert app.logger.level is logging.INFO
