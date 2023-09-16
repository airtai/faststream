import pytest

from faststream_gen_examples.example_scrape_weather.test_app import (
    test_message_was_published,
)

pytest.mark.slow(test_message_was_published)
