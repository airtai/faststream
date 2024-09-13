import logging

from faststream._internal.log.formatter import ColourizedFormatter


def test_formatter():
    logger = logging.getLogger(__file__)
    handler = logging.Handler()
    formatter = ColourizedFormatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info("Hi")
