# Using FastStream with Django

[**Django**](https://www.djangoproject.com/){.external-link target="_blank"} is a high-level Python web framework that encourages rapid development and clean, pragmatic design. Built by experienced developers, it takes care of much of the hassle of web development, so you can focus on writing your app without needing to reinvent the wheel. It’s free and open source.

In this tutorial, let's see how to use the FastStream app alongside a **Django** app.

## ASGI

[**ASGI**](https://asgi.readthedocs.io/en/latest/){.external-link target="_blank"} protocol supports lifespan events, and **Django** can be served as an **ASGI** application. So, the best way to integrate FastStream with the **Django** is by using **ASGI** lifespan. You can write it by yourself (it is really easy) or use something like [this](https://github.com/illagrenan/django-asgi-lifespan){.external-link target="_blank"}, but the prefered way for us is using [**Starlette**](https://www.starlette.io/){.external-link target="_blank"} Router.

Starlette Router allows you to serve any **ASGI** application you want, and it also supports lifespans. So, you can use it in your project to serve your regular Django **ASGI** and start up your FastStream broker too. Additionally, Starlette has much better static files support, providing an extra zero-cost feature.

## Default Django Application

Well, lets take a look at a default **Django** `asgi.py`

```python linenums="1" title="asgi.py"
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

application = get_asgi_application()
```

You can already serve it using any **ASGI** server

For example, using [**uvicorn**](https://www.uvicorn.org/deployment/){.external-link target="_blank"}:

```bash
uvicorn asgi:app --workers 4
```

Or you can use [**Gunicorn**](https://docs.gunicorn.org/en/latest/run.html){.external-link target="_blank"} with uvicorn workers

```bash
gunicorn asgi:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

Your **Django** views, models and other stuff has no any changes if you serving it through **ASGI**, so you need no worry about it.

## FastStream Integration

### Serving Django via Starlette

Now, we need to modify our `asgi.py` to serve it using **Starlette**

```python linenums="1" title="asgi.py" hl_lines="16"
# regular Djano stuff
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

django_asgi = get_asgi_application()

# Starlette serving
from starlette.applications import Starlette
from starlette.routing import Mount

app = Starlette(
    routes=(
        Mount("/", django_asgi()),  # redirect all requests to Django
    ),
)
```

### Serving static files with Starlette

Also, **Starlette** has a better static files provider than original **Django** one, so we can reuse it too.

Just add this line to your `settings.py`

```python title="settings.py"
STATIC_ROOT = "static/"
```

And collect all static files by default **Django** command

```bash
python manage.py collectstatic
```

It creates a `static/` directory in the root of your project, so you can serve it using **Starlette**

```python linenums="1" title="asgi.py" hl_lines="8"
# Code above omitted 👆

from starlette.staticfiles import StaticFiles

app = Starlette(
    routes=(
        # /static is your STATIC_URL setting
        Mount("/static", StaticFiles(directory="static"), name="static"),
        Mount("/", get_asgi_application()),  # regular Django ASGI
    ),
)
```

### FastStream lifespan

Finally, we can add our **FastStream** integration like a regular lifespan

```python linenums="1" title="asgi.py" hl_lines="18"
# Code above omitted 👆

from contextlib import asynccontextmanager
from faststream.kafka import KafkaBroker

broker = KafkaBroker()

@asynccontextmanager
async def broker_lifespan(app):
    await broker.start()
    try:
        yield
    finally:
        await broker.close()

app = Starlette(
    ...,
    lifespan=broker_lifespan,
)
```

!!! note
    The code imports `KafkaBroker` as our application is going to connect with **Kafka**. Depending on your requirements, import the necessary service's broker from the options provided by **FastStream**, such as `RabbitBroker`, `NatsBroker` or `KafkaBroker`.

??? example "Full Example"
    ```python linenums="1" title="asgi.py"
    import os
    from contextlib import asynccontextmanager

    from django.core.asgi import get_asgi_application
    from starlette.applications import Starlette
    from starlette.routing import Mount
    from starlette.staticfiles import StaticFiles
    from faststream.kafka import KafkaBroker


    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    broker = KafkaBroker()

    @asynccontextmanager
    async def broker_lifespan(app):
        await broker.start()
        try:
            yield
        finally:
            await broker.close()

    app = Starlette(
        routes=(
            Mount("/static", StaticFiles(directory="static"), name="static"),
            Mount("/", get_asgi_application()),
        ),
        lifespan=broker_lifespan,
    )
    ```

This way we can easely integrate our **FastStream** apllication with the **Django**!
