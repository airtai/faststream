import logging
from itertools import zip_longest

import pytest

from propan import PropanApp
from propan.cli.utils.logs import LogLevels, get_log_level, set_log_level
from propan.rabbit import RabbitBroker


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
            fillvalue=PropanApp(RabbitBroker()),
        )
    ),
)
def test_set_level(level, app: PropanApp):
    level = get_log_level(level)

    set_log_level(level, app)
    assert app.logger.level is app.broker.logger.level is level


@pytest.mark.parametrize(
    "level,broker",
    tuple(
        zip_longest(
            [],
            (
                PropanApp(),
                PropanApp(RabbitBroker(), logger=None),
                PropanApp(RabbitBroker(logger=None)),
                PropanApp(RabbitBroker(logger=None), logger=None),
            ),
            fillvalue=LogLevels.critical,
        )
    ),
)
def test_set_level_to_none(level, app: PropanApp):
    set_log_level(get_log_level(level), app)


def test_set_default():
    app = PropanApp()
    level = "wrong_level"
    set_log_level(get_log_level(level), app)
    assert app.logger.level is logging.INFO
