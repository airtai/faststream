from tests.marks import pydanticV1


@pydanticV1
def test_exists_and_valid():
    from docs.docs_src.getting_started.config.settings_base_1 import settings

    assert settings.queue == "test-queue"
