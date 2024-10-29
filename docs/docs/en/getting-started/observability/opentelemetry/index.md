---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# OpenTelemetry

**OpenTelemetry** is an open-source observability framework designed to provide a unified standard for collecting and exporting telemetry data such as traces, metrics, and logs. It aims to make observability a built-in feature of software development, simplifying the integration and standardization of telemetry data across various services. For more details, you can read the official [OpenTelemetry documentation](https://opentelemetry.io/){.external-link target="_blank"}.

## Usage

basically, to use **OpenTelemetry** in **FastStream** you just need to

1. Install `FastStream` with `opentelemetry-sdk`

    ```shell
    pip install "faststream[otel]"
    ```

2. Configure `TracerProvider`

    ```python linenums="1" hl_lines="6"
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider

    resource = Resource.create(attributes={"service.name": "faststream"})
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    ```

3. Add `TelemetryMiddleware` to your broker

    {!> includes/getting_started/opentelemetry/1.md !}


In the following documentation sections you can find details information about all **OpenTelemtetry** features available in **FastStream**.

## OpenTelemetry FastStream example

Also, you can take a look at already configured project and use it as a reference for you services and infrastructure.

To see how to set up, visualize, and configure tracing for **FastStream** services, go to [example](https://github.com/draincoder/faststream-monitoring){.external-link target="_blank"}.

An example includes:

* Three `FastStream` services
* Exporting traces to `Grafana Tempo` via `gRPC`
* Visualization of traces via `Grafana`
* Collecting metrics and exporting using `Prometheus`
* `Grafana dashboard` for metrics
* Examples with custom spans
* Configured `docker-compose` with the entire infrastructure

![HTML-page](../../../assets/img/distributed-trace.png){ .on-glb loading=lazy }
`Visualized via Grafana and Tempo`
