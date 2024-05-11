from functools import partial
from http import server
from typing import TYPE_CHECKING, Any, Dict
from urllib.parse import parse_qs, urlparse

from faststream._compat import json_dumps
from faststream.log import logger

if TYPE_CHECKING:
    from faststream.asyncapi.schema import Schema


def get_asyncapi_html(
    schema: "Schema",
    sidebar: bool = True,
    info: bool = True,
    servers: bool = True,
    operations: bool = True,
    messages: bool = True,
    schemas: bool = True,
    errors: bool = True,
    expand_message_examples: bool = True,
    title: str = "FastStream",
    asyncapi_js_url: str = "https://unpkg.com/@asyncapi/react-component@1.0.0-next.47/browser/standalone/index.js",
    asyncapi_css_url: str = "https://unpkg.com/@asyncapi/react-component@1.0.0-next.46/styles/default.min.css",
) -> str:
    """Generate HTML for displaying an AsyncAPI document."""
    schema_json = schema.to_json()

    config = {
        "schema": schema_json,
        "config": {
            "show": {
                "sidebar": sidebar,
                "info": info,
                "servers": servers,
                "operations": operations,
                "messages": messages,
                "schemas": schemas,
                "errors": errors,
            },
            "expand": {
                "messageExamples": expand_message_examples,
            },
            "sidebar": {
                "showServers": "byDefault",
                "showOperations": "byDefault",
            },
        },
    }

    return (
        """
    <!DOCTYPE html>
    <html>
        <head>
    """
        f"""
        <title>{title} AsyncAPI</title>
    """
        """
        <link rel="icon" href="https://www.asyncapi.com/favicon.ico">
        <link rel="icon" type="image/png" sizes="16x16" href="https://www.asyncapi.com/favicon-16x16.png">
        <link rel="icon" type="image/png" sizes="32x32" href="https://www.asyncapi.com/favicon-32x32.png">
        <link rel="icon" type="image/png" sizes="194x194" href="https://www.asyncapi.com/favicon-194x194.png">
    """
        f"""
        <link rel="stylesheet" href="{asyncapi_css_url}">
    """
        """
        </head>

        <style>
        html {
            font-family: ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica Neue,Arial,Noto Sans,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol,Noto Color Emoji;
            line-height: 1.5;
        }
        </style>

        <body>
        <div id="asyncapi"></div>
    """
        f"""
        <script src="{asyncapi_js_url}"></script>
        <script>
    """
        f"""
            AsyncApiStandalone.render({json_dumps(config).decode()}, document.getElementById('asyncapi'));
    """
        """
        </script>
        </body>
    </html>
    """
    )


def serve_app(
    schema: "Schema",
    host: str,
    port: int,
) -> None:
    """Serve the HTTPServer with AsyncAPI schema."""
    logger.info(f"HTTPServer running on http://{host}:{port} (Press CTRL+C to quit)")
    logger.warning("Please, do not use it in production.")

    server.HTTPServer(
        (host, port),
        partial(_Handler, schema=schema),
    ).serve_forever()


class _Handler(server.BaseHTTPRequestHandler):
    def __init__(
        self,
        *args: Any,
        schema: "Schema",
        **kwargs: Any,
    ) -> None:
        self.schema = schema
        super().__init__(*args, **kwargs)

    def get_query_params(self) -> Dict[str, bool]:
        return {
            i: _str_to_bool(next(iter(j))) if j else False
            for i, j in parse_qs(urlparse(self.path).query).items()
        }

    def do_GET(self) -> None:  # noqa: N802
        """Serve a GET request."""
        query_dict = self.get_query_params()

        encoding = "utf-8"
        html = get_asyncapi_html(
            self.schema,
            sidebar=query_dict.get("sidebar", True),
            info=query_dict.get("info", True),
            servers=query_dict.get("servers", True),
            operations=query_dict.get("operations", True),
            messages=query_dict.get("messages", True),
            schemas=query_dict.get("schemas", True),
            errors=query_dict.get("errors", True),
            expand_message_examples=query_dict.get("expandMessageExamples", True),
            title=self.schema.info.title,
        )
        body = html.encode(encoding=encoding)

        self.send_response(200)
        self.send_header("content-length", str(len(body)))
        self.send_header("content-type", f"text/html; charset={encoding}")
        self.end_headers()
        self.wfile.write(body)


def _str_to_bool(v: str) -> bool:
    return v.lower() in ("1", "t", "true", "y", "yes")
