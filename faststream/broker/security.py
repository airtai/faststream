# pragma: no cover

import warnings

from faststream.security import BaseSecurity, SASLPlaintext, SASLScram256, SASLScram512

warnings.warn(
    (
        "\n`faststream.broker.security` import path was deprecated and will be removed in 0.4.0"
        "\nPlease, use `faststream.security` instead"
    ),
    DeprecationWarning,
    stacklevel=2,
)

__all__ = (
    "SASLPlaintext",
    "SASLScram256",
    "SASLScram512",
    "BaseSecurity",
)
