from typing import Mapping, Any
from unittest.mock import Mock
from contextlib import contextmanager

from pytest import MonkeyPatch


@contextmanager
def mock_pydantic_settings_env(env_mapping: Mapping[str, Any]):
    with MonkeyPatch().context() as c:
        mock = Mock()
        mock.return_value = env_mapping
        c.setattr("pydantic_settings.sources.DotEnvSettingsSource._read_env_files", mock)
        yield

