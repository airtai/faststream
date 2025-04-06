---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Sentry support

Unfortunately, **[Sentry](https://sentry.io/){.external-link target="_blank"}** does not fully support **OpenTelemetry**, namely, **Sentry** has its own context format, which does not work well in **Python** implementations, the depth of the cached spans is not enough to bind to the `root` span.

## OpenTelemetry collector

Fortunately, there is a workaround for exporting flights to **Sentry**. You just need to launch the `opentelemetry-collector` container, which will convert the traces to the **Sentry** format and export them according to the specified `DSN`.

1. Install [opentelemetry-exporter-otlp](https://pypi.org/project/opentelemetry-exporter-otlp/){.external-link target="_blank"} for export spans via **gRPC**

    ```shell
    pip install opentelemetry-exporter-otlp
    ```

2. Setup `TracerProvider` with **gRPC** exporter

    ```python linenums="1" hl_lines="8 10"
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create(attributes={"service.name": "faststream"})
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
    processor = BatchSpanProcessor(exporter)
    tracer_provider.add_span_processor(processor)
    ```

3. Create `otel.yaml` file config with your **Sentry** `DSN`

    ```yaml title="otel.yaml" linenums="1" hl_lines="9"
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317

    exporters:
      sentry:
        dsn: "https://your-secret-dsn.com"

    service:
      pipelines:
        traces:
          receivers: [otlp]
          exporters: [sentry]
    ```

4. Run **Docker** container with `opentelemetry-collector`

    ```yaml title="docker-compose.yaml" linenums="1""
    services:
      otel-collector:
        image: otel/opentelemetry-collector-contrib:latest
        command: [ "--config=/etc/otel.yaml" ]
        volumes:
          - ./otel.yaml:/etc/otel.yaml
        ports:
          - "4317:4317"
    ```

!!! note
    Despite the fact that this use case is somewhat curtailed due to the lack of `sentry-sdk`, your code remains independent of the tracing backend and you can switch to **Tempo** or **Jaeger** at any time by simply changing `otel.yaml`.

## Visualization

![HTML-page](../../../assets/img/sentry-trace.png){ .on-glb loading=lazy }
`Visualized via Sentry`

An example of visualizing a distributed trace between two services in **Sentry**.

## Alternatives

If you need a tracing collection and visualization system that can be easily configured and does not have infrastructure dependencies, then [Logfire](https://logfire.pydantic.dev/docs/integrations/event-streams/faststream/){.external-link target="_blank"} can be considered.

![HTML-page](../../../assets/img/logfire-trace.png){ .on-glb loading=lazy }
`Visualized via Logfire`
