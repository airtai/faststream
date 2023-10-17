# Using FastStream with Django

[**Django**](https://www.djangoproject.com/){.external-link target="_blank"} is a high-level Python web framework that encourages rapid development and clean, pragmatic design. Built by experienced developers, it takes care of much of the hassle of web development, so you can focus on writing your app without needing to reinvent the wheel. It’s free and open source.

In this tutorial, let's see how to use the FastStream app alongside a Django app.

## ASGI

[**ASGI**](https://asgi.readthedocs.io/en/latest/){.external-link target="_blank"} protocol supports lifespan events, and Django can be served as an ASGI application. So, the best way to integrate FastStream with the Django is by using ASGI lifespan. You can write it by yourself (it is really easy) or use something like [this](https://github.com/illagrenan/django-asgi-lifespan){.external-link target="_blank"}, but the prefered way for us is using [**Starlette**](https://www.starlette.io/){.external-link target="_blank"} Router.

Starlette Router allows you to serve any ASGI application you want, and it also supports lifespans. So, you can use it in your project to serve your regular Django ASGI and start up your FastStream broker too. Additionally, Starlette has much better static files support, providing an extra zero-cost feature.

## Writing Django + FastStream Application

```python title="django_faststream.py"
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
        Mount("/", get_asgi_application()),  # regular Django ASGI
    ),
    lifespan=broker_lifespan,
)
```

In the above code, we start by importing necessary packages.

The code imports `KafkaBroker` as our application is going to connect with Kafka. Depending on your requirements, import the necessary service's broker from the options provided by FastStream, such as  `RabbitBroker`, `NatsBroker` or `KafkaBroker`.

Then, we set the environment variable [**DJANGO_SETTINGS_MODULE**](https://docs.djangoproject.com/en/4.2/topics/settings/#envvar-DJANGO_SETTINGS_MODULE){.external-link target="_blank"} to tell our Django app where to find the Django app's settings.

Next, we initiate the Kafka broker. After that, as mentioned earlier, we create a lifespan context to start and stop our `KafkaBroker`.

Finally, we register the Django application as a Starlette app.

## Running the Django Application

The above application can be served with any ASGI server.

For example, using [**uvicorn**](https://www.uvicorn.org/deployment/){.external-link target="_blank"}, we can serve the application as follows:

```bash
uvicorn django_faststream:app --workers 4
```

Or you can use [**Gunicorn**](https://docs.gunicorn.org/en/latest/run.html){.external-link target="_blank"} with uvicorn workers

```bash
gunicorn django_faststream:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```
