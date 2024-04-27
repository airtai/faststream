from faststream.opentelemetry.consts import TELEMETRY_PROVIDER_CONTEXT_KEY
from faststream.opentelemetry.provider import TelemetrySettingsProvider

__all__ = (
    "TELEMETRY_PROVIDER_CONTEXT_KEY",
    "HAS_OPEN_TELEMETRY",
    "TelemetryMiddleware",
    "TelemetrySettingsProvider",
)


try:
    from faststream.opentelemetry.middleware import TelemetryMiddleware

    HAS_OPEN_TELEMETRY = True

except ImportError:
    from unittest.mock import Mock

    TelemetryMiddleware = Mock(
        side_effect=ImportError(
            "To use TelemetryMiddleware, please install required dependencies:\n"
            'pip install "faststream[telemetry]"'
        )
    )

    HAS_OPEN_TELEMETRY = False
