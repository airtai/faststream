from typing import Any, Dict

import pytest
from yarl import URL

from faststream.rabbit.utils import build_url


class TestUrlBuilder:
    @pytest.mark.parametrize(
        ("url_kwargs", "expected_url"),
        [
            pytest.param(
                {},
                URL("amqp://guest:guest@localhost:5672/"),  # pragma: allowlist secret
                id="blank_params_use_defaults",
            ),
            pytest.param(
                {"ssl": True},
                URL("amqps://guest:guest@localhost:5672/"),  # pragma: allowlist secret
                id="use_ssl",
            ),
            pytest.param(
                {"url": "fake", "virtualhost": "/", "host": "host"},
                URL("amqp://guest:guest@host:5672/"),  # pragma: allowlist secret
                id="overrides_and_default_vh",
            ),
            pytest.param(
                {"virtualhost": "//test"},  # pragma: allowlist secret
                URL(
                    "amqp://guest:guest@localhost:5672//test"  # pragma: allowlist secret
                ),
                id="exotic_virtualhost",
            ),
        ],
    )
    def test_unpack_args(self, url_kwargs: Dict[str, Any], expected_url: URL) -> None:
        url = build_url(**url_kwargs)
        assert url == expected_url
