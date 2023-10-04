from docs.docs_src.getting_started.asyncapi.asyncapi_customization.custom_info import (
    app,
)
from faststream.asyncapi.generate import get_app_schema


def test_info_customization():
    schema = get_app_schema(app).to_jsonable()

    assert schema["info"] == {
        "title": "My App",
        "version": "1.0.0",
        "description": "Test description",
        "termsOfService": "https://my-terms.com/",
        "contact": {"name": "support", "url": "https://help.com/"},
        "license": {"name": "MIT", "url": "https://opensource.org/license/mit/"},
    }
