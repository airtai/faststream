from tests.marks import pydanticV2
from tests.mocks import mock_pydantic_settings_env


@pydanticV2
def test_exists_and_valid():
    with mock_pydantic_settings_env({"url": "localhost:9092"}):
        from docs.docs_src.getting_started.config.usage import settings

        assert settings.queue == "test-queue"
        assert settings.url == "localhost:9092"
