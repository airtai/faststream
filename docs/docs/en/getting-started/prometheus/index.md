---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Prometheus

**Prometheus** is an open-source monitoring and alerting toolkit originally built at SoundCloud. With a focus on reliability, robustness, and easy scalability, Prometheus allows users to collect metrics, scrape data from various sources, store them efficiently, and query them in real-time. Its flexible data model, powerful query language, and seamless integration with Grafana make it a popular choice for monitoring the health and performance of systems and applications.

### FastStream Metrics

To add a metrics to your broker, you need to:

1. Install `FastStream` with `prometheus-client`

    ```shell
    pip install faststream[prometheus]
    ```

2. Add `PrometheusMiddleware` to your broker

    {!> includes/getting_started/prometheus/1.md !}
