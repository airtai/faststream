from docs.docs_src.getting_started.asyncapi.asyncapi_customization.custom_info import (
    app,
)
from faststream.specification.asyncapi.generate import get_app_schema
from faststream.specification.asyncapi.version import AsyncAPIVersion


def test_info_customization():
    schema = get_app_schema(app, version=AsyncAPIVersion.v2_6).to_jsonable()

    assert schema["info"] == {
        "title": "My App",
        "version": "1.0.0",
        "description": "# Title of the description\nThis description supports **Markdown** syntax",
        "termsOfService": "https://my-terms.com/",
        "contact": {"name": "support", "url": "https://help.com/"},
        "license": {"name": "MIT", "url": "https://opensource.org/license/mit/"},
    }
